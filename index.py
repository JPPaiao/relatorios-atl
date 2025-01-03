from threading import Lock
import threading
from datetime import datetime
import calendar
from flask import Flask, jsonify, redirect, render_template, request, send_file, send_from_directory
import pandas as pd
from gerator.clean_uploads import clean_uploads_folder
from gerator.gerator import process_spreadsheet
from gerator.hbl import get_hbl_process
from sheets.convert_df import sheet_for_dataframe
from sheets.create import create_data
from sheets.read import read_sheets
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
limiter = Limiter(
  key_func=get_remote_address,
  app=app,
  default_limits=["100 per hour"]
) 
progress = {'progress': 0}
progress_lock = Lock()
name_sheet = ''
event = threading.Event()


MAX_CONTENT_LENGTH = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'xlsx'}
UPLOAD_FOLDER = os.getenv('UPLOAD')

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

def set_progress(value: int):
  with progress_lock:
    progress['progress'] = value

def process_sheet_task(file, depot):
  global progress, name_sheet

  set_progress(0)

  new_file = process_spreadsheet(file, depot, set_progress)

  name_sheet = new_file['name_sheet']
  processed_file_path = os.path.join(name_sheet)
  os.rename(new_file['name_sheet'], processed_file_path)

  create_data(new_file['df_process'], depot)
  set_progress(100)
  print('fim') 


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

    hbls = get_hbl_process(file_path, depot)
    return send_file(hbls, as_attachment=True, download_name='arquivo_processado.xlsx')


@app.route('/download_processed_file')
def download_processed_file():
  global progress, name_sheet 
  BASENAME_PATH = os.path.basename(name_sheet)

  if progress['progress'] == 100 and name_sheet:
    return send_from_directory(UPLOAD_FOLDER, BASENAME_PATH, as_attachment=True)
  return "O arquivo ainda não está pronto para download.", 404


@app.route('/progress')
def get_progress():
  global progress 

  with progress_lock:
    progress_status = progress['progress']

  status = 'completed' if progress_status >= 100 else 'processing'
  return jsonify({'status': status, 'progress': progress_status})


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

  for month in sheets:
    list_dfs.append(sheet_for_dataframe(month))

  df_concat = pd.concat(list_dfs)
  df_json = df_concat.to_json(orient='records')
  return df_json


@app.route('/create_sheet/<string:depot>', methods=['POST'])
@limiter.limit("10 por minuto")
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
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # def task_process():
    #   print('inicio')
    #   process_sheet_task(file_path, depot)
    #   event.set()

    # thread = threading.Thread(target=task_process)
    # thread.start()
    # event.wait()

    thread = threading.Thread(target=process_sheet_task, args=(file_path, depot))
    thread.start()

    return send_from_directory(UPLOAD_FOLDER, name_sheet, as_attachment=True)
  
  return "Arquivo inválido!", 400


if __name__ == '__main__':
    app.run(debug=True)
