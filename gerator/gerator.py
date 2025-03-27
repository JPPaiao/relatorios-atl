from datetime import datetime
from gerator.clean_uploads import clean_uploads_folder
from gerator.sac import gerator_sac
from gerator.scan import scan_repets
from sheets.convert_df import insert_collumn, sheet_for_dataframe
from sheets.read import read_sheets
from sheets.worksheets import dates_df
from dotenv import load_dotenv
from itertools import chain
import requests
import json
import pandas as pd
import os
import glob

load_dotenv() 
UPLOAD_FOLDER = os.getenv('UPLOAD')
LOGCOMEX_API = os.getenv('LOGCOMEX')

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

def create_cobranca_dataframe(df):
  """Cria o DataFrame inicial de cobrança com base nos dados fornecidos."""
  return pd.DataFrame({
    "UNIDADE": df["cntr"],
    "TIPO": df['type'],
    "OWNER": df['own'],
    "ENTRADA": df['datein'],
    "CNPJ AGENDADO": df["importer"],
    "CNPJ HBL": "",
    "TRANSPORTADORA": df["carrier"],
    "CNPJ TRANSPORTADORA": df["carrier_cnpj"],
    "VALORES": df['price_use'],
    "OBS": "",
    "DATA. PAG": pd.to_datetime(df['payment'], errors='coerce').dt.strftime('%d-%m-%Y'),
    "NF": df['number nf'],
    "TERMO": pd.to_datetime(df['term'], errors='coerce').dt.strftime('%d-%m-%Y'),
    "DOCUMENTACAO": pd.to_datetime(df['files'], errors='coerce').dt.strftime('%d-%m-%Y'),
    "ISENTO": "",
    "V. ORIGINAL": "",
    "V. FINAL": "",
    "V. DIFERENÇA": "",
    "OBS SAC": "",
    "SAC": "",
    "DATA ATUALIZACAO": datetime.today().strftime('%d-%m-%Y %H:%M:%S')
  })

def process_spreadsheet(file_path=None, depot=None, request_id=None, df_reprocess=None):
  print(depot)
  df_cobranca = pd.DataFrame()
  df = pd.read_excel(file_path)

  if file_path:
    df_cobranca = create_cobranca_dataframe(df)

  elif not df_reprocess.empty:
    df_cobranca = df_reprocess

  df_cobranca['ENTRADA'] = pd.to_datetime(df_cobranca['ENTRADA'], format='%d-%m-%Y', errors='coerce')

  df_for_dates = dates_df(df_cobranca, depot)
  dataframes_to_concat = [group for (year, month), group in df_for_dates['df_for_months']]
  df_concat_new = pd.concat(dataframes_to_concat, axis=0, ignore_index=True)

  df_concat_new = gerator_sac(df_concat_new, df)

  if 'status' in df_concat_new:
    error_remark = {
      "status": "erro",
      "erros": list(chain(df_concat_new.get('erros', [])))
    }
    return error_remark

  sheets = read_sheets(depot, df_for_dates['months'][0], df_for_dates['months'][-1], month=True)
  list_datas = {'new': [], 'update': pd.DataFrame(), 'duplicad': pd.DataFrame()}

  if sheets['sheet']:
    list_dfs = [sheet_for_dataframe(sheet, sheets['columns']) for sheet in sheets['sheet']]

    list_dfs = [insert_collumn(df_list, depot) for df_list in list_dfs]
    df_exists = pd.concat(list_dfs, axis=0, ignore_index=True)
    df_exists_filtrado = filter_months_df(df_exists, df_for_dates['months'])

    print()
    print('scan')
    scan_repets(df_concat_new, df_exists_filtrado)

    list_datas = process_sheets_data(df_concat_new, df_exists_filtrado)
  else:
    df_concat_new = value_origin_update(df_concat_new)
    list_datas['new'] = df_concat_new

  # df_new = gerator_sac(list_datas['new'], df)
  # df_old = gerator_sac(list_datas['update'], df)

  df_comex = comex(list_datas['new'], request_id, depot)

  name_sheet = ''
  if file_path:
    clean_uploads_folder(limit=10)
    name_sheet = save_sheet_cobran([df_comex, list_datas['update']], file_path, depot)

  sheet_process = {
    'df_process': { 'new': df_comex, 'old': list_datas['update'] },
    'name_sheet': name_sheet,
    'status': 'completed'
  }

  return sheet_process

def filter_months_df(df, list_months):
  df['ENTRADA'] = pd.to_datetime(df['ENTRADA'], format='%d-%m-%Y', errors='coerce')

  if df['ENTRADA'].isna().sum() > 0:
    df['ENTRADA'] = pd.to_datetime(df['ENTRADA'], errors='coerce')

  df['MES_ANO'] = pd.to_datetime(df['ENTRADA'], format='%d-%m-%Y').dt.strftime('%m-%Y')

  df_filtrado = df[df['MES_ANO'].isin(list_months)]
  df_filtrado = df_filtrado.drop(columns=['MES_ANO'])
  df_filtrado = df_filtrado.reset_index(drop=True)
  df_filtrado['ENTRADA'] = df_filtrado['ENTRADA'].dt.strftime('%d-%m-%Y')

  return df_filtrado


def process_sheets_data(df_datas_new, df_exists):
  """Processa os dados para separar novos e atualizados."""
  list_units = df_exists['UNIDADE'].to_list()

  df_datas_new = value_origin_update(df_datas_new)
  print(df_datas_new)

  df_new_datas = df_datas_new[~df_datas_new['UNIDADE'].isin(list_units)]
  df_old_datas = df_datas_new[df_datas_new['UNIDADE'].isin(list_units)]

  # df_old_datas = value_origin_update(df_old_datas)

  df_update = update_df(df_exists, df_old_datas)

  return {
    'update': df_update,
    'new': df_new_datas
  }

def update_df(df_exists, df_old_datas):
  """
  Atualiza df_exists com os novos dados de df_old_datas, removendo registros antigos sem DATA ATUALIZACAO.

  Args:
    df_exists (pd.DataFrame): DataFrame original contendo os registros existentes.
    df_old_datas (pd.DataFrame): DataFrame com os registros atualizados.

  Returns:
    pd.DataFrame: DataFrame atualizado, removendo registros antigos sem DATA ATUALIZACAO.
  """

  if df_old_datas.empty:
      return df_exists  # Se não há dados para atualizar, retorna df_exists sem mudanças

  # 🔹 Lista de colunas que devem ser atualizadas
  columns_update = ['VALORES', 'DATA. PAG', 'NF', 'TERMO', 'DOCUMENTACAO', 'ISENTO', 'V. FINAL', 'V. DIFERENÇA', 'OBS SAC', 'SAC', 'DATA ATUALIZACAO']

  # 🔹 Verificar se todas as colunas para atualizar existem em df_old_datas
  colunas_validas = [col for col in columns_update if col in df_old_datas.columns]

  if not colunas_validas:
      print("⚠️ Nenhuma coluna válida para atualização. Verifique as colunas disponíveis.")
      return df_exists

  # 🔹 Criar um dicionário contendo apenas as colunas que devem ser atualizadas
  dict_updates = df_old_datas.set_index('UNIDADE')[colunas_validas].to_dict(orient='index')

  # 🔹 Filtrar unidades antigas que NÃO têm DATA ATUALIZACAO
  unidades_sem_data = df_exists[df_exists['DATA ATUALIZACAO'].isna()]['UNIDADE'].tolist()

  # 🔹 Remover essas unidades do df_exists
  df_exists = df_exists[~df_exists['UNIDADE'].isin(unidades_sem_data)]

  # 🔹 Adicionar as novas unidades atualizadas de df_old_datas
  df_exists = pd.concat([df_exists, df_old_datas], ignore_index=True)

  # 🔹 Garantir que não haja duplicatas, mantendo apenas a versão mais recente
  df_exists = df_exists.drop_duplicates(subset=['UNIDADE'], keep='last')

  return df_exists


def value_origin_update(df_new): 
  for i in df_new.index:
    if pd.isna(df_new.loc[i, 'V. ORIGINAL']) or df_new.loc[i, 'V. ORIGINAL'] == '':
      df_new.loc[i, 'V. ORIGINAL'] = df_new.loc[i, 'VALORES'].astype(float)

  return df_new


# def update_df(df_dados, df_novos):
#   if df_novos.empty:
#     return pd.DataFrame()
  
#   for index, row in df_novos.iterrows():
#     idx = df_dados[df_dados['UNIDADE'] == row['UNIDADE']].index
#     if not idx.empty:
#       update_row(df_dados, idx, row)
#       # Data de atualização nova (sempre a data do sistema)
#       data_atual_nova = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

#       df_dados.loc[idx, 'DATA ATUALIZACAO'] = data_atual_nova

#   columns_to_clean = ['NF', 'DATA. PAG', 'DOCUMENTACAO', 'TERMO']
#   df_dados[columns_to_clean] = df_dados[columns_to_clean].fillna('').replace({'nan': ''})

#   return df_dados


# def update_row(df_dados, idx, row):
#   """Atualiza uma linha do DataFrame `df_dados` com base em `row`."""
#   if pd.notna(row['VALORES']) and row['VALORES'] != '':
#     df_dados.loc[idx, 'VALORES'] = float(str(row['VALORES']).replace(',', '.'))
#   else:
#     df_dados.loc[idx, 'VALORES'] = ''
  
#   df_dados.loc[idx, 'DATA. PAG'] = row['DATA. PAG']
#   df_dados.loc[idx, 'NF'] = int(row['NF']) if pd.notna(row['NF']) and row['NF'] != '' else ''
#   df_dados.loc[idx, 'TERMO'] = row['TERMO'] if pd.notna(row['TERMO']) else ''
#   df_dados.loc[idx, 'DOCUMENTACAO'] = row['DOCUMENTACAO'] if pd.notna(row['DOCUMENTACAO']) else ''


def save_sheet_cobran(dfs, sheet_path, depot):
  if not dfs:
    return dfs
  
  dfs = [df for df in dfs if len(df) > 0]
  df = pd.concat(dfs)

  processed_file_path = os.path.join(sheet_path)

  df.to_excel(processed_file_path, index=False, engine='openpyxl')
  return processed_file_path


def clean_uploads_folder(limit=10):
  # Obter a lista de todos os arquivos na pasta de uploads, ordenados pela data de modificação
  files = glob.glob(os.path.join(UPLOAD_FOLDER, '*'))
  files.sort(key=os.path.getmtime)  # Ordena pelos arquivos mais antigos

  # Verifica se a quantidade de arquivos excede o limite
  if len(files) > limit:
    # Calcula quantos arquivos excedem o limite
    excess_files = len(files) - limit
    
    # Remove os arquivos mais antigos até que a quantidade seja menor ou igual ao limite
    for file_to_delete in files[:excess_files]:
      try:
        os.remove(file_to_delete)
        print(f"Arquivo excluído: {file_to_delete}")
      except Exception as e:
        print(f"Erro ao excluir o arquivo {file_to_delete}: {e}")


def get_units(unidade):
  req = requests.get(f"https://api.logcomex.com.br/v2/get_conteiner_tracking?api_key={LOGCOMEX_API}&conteiner={unidade}")
  response = json.loads(req.content)
  return response

def get_cnpj_unit(unidade):
  datas = get_units(unidade)

  if datas['status'] != "ok":
    while datas['status'] != "ok":
      datas = get_units(unidade)
    
    return datas['data']

  return datas['data']

def formatar_cnpj(cnpj):
  if '' == cnpj or pd.isna(cnpj):
    return ''
  
  cnpj_format = str(int(float(cnpj))) 
  return cnpj_format.zfill(14)


def comex(df, request_id, depot):
  import app
  progress = app.set_progress

  if request_id:
    progress(request_id, 0)
  print('processando', depot)
 
  total_unidades = df['UNIDADE'].nunique()

  if not df.empty:
    df = df.dropna(subset=['ENTRADA'])

    for i, unidade in enumerate(df['UNIDADE']):
      if pd.notna(df.loc[df['UNIDADE'] == unidade, 'OBS'].values[0]) and df.loc[df['UNIDADE'] == unidade, 'OBS'].values[0].strip() != '':
        continue
      df_get_uni = pd.DataFrame(get_cnpj_unit(unidade))

      if df_get_uni.empty:
        continue

      dados_validos = df_get_uni
      dados_validos = dados_validos.dropna(subset=['importador_cnpj'])

      dados_validos['data_operacao'] = pd.to_datetime(dados_validos['data_operacao'], format='%Y-%m-%d')

      dados_validos = dados_validos[dados_validos['data_operacao'].dt.year == dados_validos['data_operacao'].dt.year.max()]
      dados_validos = dados_validos[dados_validos['data_operacao'].dt.month == dados_validos['data_operacao'].dt.month.max()]

      dados_ordenados = dados_validos.sort_values(by='tipo_conhecimento', key=lambda x: x != 'HBL')

      cnpj_mais_recente = dados_ordenados.iloc[0]['importador_cnpj'] if not dados_ordenados.empty else ''

      if dados_ordenados.empty:
        df.loc[df["UNIDADE"] == unidade, 'CNPJ HBL'] = cnpj_mais_recente
        progress_percent = (i + 1) / total_unidades * 100
        if request_id:
          print(request_id)
          progress(request_id, round(progress_percent))
        continue

      if dados_ordenados.iloc[0]['tipo_conhecimento'] != 'HBL':
        df.loc[df["UNIDADE"] == unidade, 'OBS'] = f'SEM HBL/AGENDADO NO {dados_ordenados.iloc[0]["tipo_conhecimento"]}'
      else:
        df.loc[df["UNIDADE"] == unidade, 'OBS'] = ''

      df.loc[df["UNIDADE"] == unidade, 'CNPJ HBL'] = cnpj_mais_recente
      progress_percent = (i + 1) / total_unidades * 100
      print(round(progress_percent))

      if request_id:
        progress(request_id, round(progress_percent))

    df['CNPJ HBL'] = df['CNPJ HBL'].apply(formatar_cnpj)
    df['CNPJ AGENDADO'] = df['CNPJ AGENDADO'].apply(formatar_cnpj)
    df['CNPJ TRANSPORTADORA'] = df['CNPJ TRANSPORTADORA'].apply(formatar_cnpj)
    df = df.drop_duplicates(subset=['UNIDADE'])
  
  if request_id:
    progress(request_id, 100)

  print('processado', depot)
  return df
