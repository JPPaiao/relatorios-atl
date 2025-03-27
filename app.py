from concurrent.futures import ThreadPoolExecutor
import json
from threading import Lock
import threading
from datetime import datetime
import calendar
import uuid
from flask import Flask, jsonify, redirect, render_template, request, send_file, send_from_directory
import pandas as pd
from gerator.clean_uploads import clean_uploads_folder
from gerator.gerator import process_spreadsheet
from gerator.hbl import get_hbl_process
from sheets.convert_df import sheet_for_dataframe
from sheets.create import create_data
from sheets.delete import delete, filter_df
from sheets.read import read_sheets
from dotenv import load_dotenv
import os

load_dotenv('/var/www/geradorrelatorio/.env')
# load_dotenv()
app = Flask(__name__)
# redis_store = redis.Redis(host='localhost', port=6379, db=0)
# limiter = Limiter(
#   key_func=get_remote_address,
#   app=app,
#   default_limits=["100 per hour"]
# )

progress_lock = Lock()
progress_dict = {}
name_sheet = ''
event = threading.Event()

# PROGRESS_FILE = '/var/www/geradorrelatorio/progress_store.json'
PROGRESS_FILE = 'progress_store.json'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'xlsx'}
UPLOAD_FOLDER = os.getenv('UPLOAD')

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

if not os.path.exists(PROGRESS_FILE):
  with open(PROGRESS_FILE, 'w') as f:
    json.dump({}, f)

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

# Atualiza progresso em arquivo JSON compartilhado
def set_progress(request_id, value, status="processing", mensagem="", erros=None):
  with progress_lock:
    with open(PROGRESS_FILE, 'r') as f:
      progress_store = json.load(f)

    progress_store[request_id] = {
      "progress": value,
      "status": status,
      "mensagem": mensagem,
      "erros": erros or []
    }

    with open(PROGRESS_FILE, 'w') as f:
      json.dump(progress_store, f)

def process_sheet_task(request_id, file, depot):
  """Executa o processamento da planilha em uma thread separada."""
  set_progress(request_id, 0)

  print('cria')
  print(request_id)
  print()
  new_file = process_spreadsheet(file, depot, request_id)
  
  if new_file['status'] == 'erro':
    set_progress(request_id, 100, status="erro", erros=new_file['erros'])
    return new_file

  name_sheet = new_file['name_sheet']
  processed_file_path = os.path.join(name_sheet)
  os.rename(new_file['name_sheet'], processed_file_path)

  create_data(new_file['df_process'], depot)
  set_progress(request_id, 100, status="concluído")

  print('fim')
  return new_file


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/get-hbl/<string:depot>', methods=['POST'])
def get_hbl(depot):
  if 'file' not in request.files:
    return "Nenhum arquivo foi enviado!", 400
    
  file = request.files['file']

  if not allowed_file(file.filename):
    return "Arquivo inválido!", 400
  
  if file.filename == '':
    return "Nenhum arquivo selecionado!", 400
  
  if file.mimetype != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
    return "Tipo de arquivo inválido!", 400
  
  if file and file.filename.endswith('.xlsx'):
    clean_uploads_folder(limit=10)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    get_hbl = get_hbl_process(file_path, depot)
    print()
    print(get_hbl)
    
    if get_hbl['status'] == 'erro':
      return get_hbl

    process_file_path, new_file_name = get_hbl['data']

    if not process_file_path or not os.path.exists(process_file_path):
      return "Erro ao processar o arquivo.", 500

    return send_file(process_file_path, as_attachment=True, download_name=new_file_name)


@app.route('/download_processed_file/<string:request_id>')
def download_processed_file(request_id):
  """Permite o usuário baixar o arquivo processado apenas se o status for concluído."""
  with progress_lock:
    progress_info = progress_dict.get(request_id, {})

  if progress_info.get("status") == "concluído":
    file_path = os.path.basename(progress_info.get("file_name", ""))
    return send_from_directory(UPLOAD_FOLDER, file_path, as_attachment=True)

  return "O arquivo ainda não está pronto para download.", 404


@app.route('/progress/<string:request_id>')
def get_progress(request_id):
  with progress_lock:
    with open(PROGRESS_FILE, 'r') as f:
      progress_store = json.load(f)

    if request_id not in progress_store:
      return jsonify({"status": "not_found", "progress": 0}), 404

    progress_status = progress_store[request_id]

    # Exclui o request_id somente após o cliente consultar e progresso for 100%
    if progress_status["progress"] >= 100:
      del progress_store[request_id]
      with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_store, f)

    return jsonify(progress_status)


@app.route('/read_sheet/<string:depot>')
def read_sheet(depot):
  months = request.args.get('months')
  if months:
    month_pass, months_current = months.split("_")
  else:
    today = datetime.today()
    first_day = today.replace(day=1)
    last_day = today.replace(
      day=calendar.monthrange(today.year, today.month)[1]
    )

    months_current = first_day.strftime("%d-%m-%Y") 
    month_pass = last_day.strftime("%d-%m-%Y")
 
  list_dfs = []
  sheets = read_sheets(depot, months_current, month_pass)

  for month in sheets['sheet']:
    list_dfs.append(sheet_for_dataframe(month))

  df_concat = pd.concat(list_dfs)
  df_json = df_concat.to_json(orient='records')
  return df_json


# @limiter.limit("10 por minuto")
@app.route('/create_sheet/<string:depot>', methods=['POST'])
def create_sheet(depot):
  if 'file' not in request.files:
    return "Nenhum arquivo foi enviado!", 400
    
  file = request.files['file']

  if not allowed_file(file.filename):
    return "Arquivo inválido!", 400
  
  if file.filename == '':
    return "Nenhum arquivo selecionado!", 400
  
  if file.mimetype != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
    return "Tipo de arquivo inválido!", 400
  
  if file and file.filename.endswith('.xlsx'):
    global name_sheet
    request_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    thread = threading.Thread(target=process_sheet_task, args=(request_id, file_path, depot))
    thread.start()

    return jsonify({"request_id": request_id, "message": "Processamento iniciado!"})

  return "Arquivo inválido!", 400


if __name__ == '__main__':
    app.run(debug=True)
