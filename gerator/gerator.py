from gerator.clean_uploads import clean_uploads_folder
from gerator.sac import gerator_sac
from sheets.convert_df import sheet_for_dataframe
from sheets.read import read_sheets
from sheets.worksheets import dates_df
from dotenv import load_dotenv
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


def process_spreadsheet(file_path=None, depot=None, set_progress=None, df_reprocess=None):
  df_cobranca = pd.DataFrame()

  if file_path:
    df = pd.read_excel(file_path)

    df_cobranca = pd.DataFrame({
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
      "DOCUMENTACAO": pd.to_datetime(df['files'], errors='coerce').dt.strftime('%d-%m-%Y %H:%M:%S'),
      "ISENTO": "",
      "V. ISENTO": "",
      "OBS SAC": "",
      "SAC": "",
    })


    df_cobranca = gerator_sac(df_cobranca, df)
  elif not df_reprocess.empty:
    df_cobranca = df_reprocess

  print(depot)
  df_cobranca['ENTRADA'] = pd.to_datetime(df_cobranca['ENTRADA'], format='%d-%m-%Y %H:%M:%S', errors='coerce') 
  df_for_dates = dates_df(df_cobranca, depot)

  dataframes_to_concat = [group for (year, month), group in df_for_dates['df_for_months']]
  df_concat = pd.concat(dataframes_to_concat, axis=0, ignore_index=True) 

  first_months = df_for_dates['months'][0]
  last_months = df_for_dates['months'][-1]
  sheets = read_sheets(depot, first_months, last_months)

  list_datas = {'new': [], 'duplicad': pd.DataFrame(), 'update': pd.DataFrame()}
  if sheets:
    list_dfs = [sheet_for_dataframe(sheet) for sheet in sheets]      
    df_sheet = pd.concat(list_dfs, axis=0, ignore_index=True)

    list_units = df_sheet['UNIDADE'].to_list()
    df_new_datas = df_concat[~df_concat['UNIDADE'].isin(list_units)]
    df_old_datas = df_concat[df_concat['UNIDADE'].isin(list_units)]

    list_olds = df_old_datas['UNIDADE'].to_list() 
    df_update = update_df(df_sheet, df_old_datas)
    df_duplicated = df_update[df_update['UNIDADE'].isin(list_olds)] if not df_update.empty else pd.DataFrame()

    list_datas['update'] = df_update
    list_datas['duplicad'] = df_duplicated
    list_datas['new'] = df_new_datas
  else:
    list_datas['new'] = df_concat  

  df_new = list_datas['new']
  df_old = list_datas['duplicad']
  df_comex = comex(df_new, set_progress, depot)

  name_sheet = ''
  if file_path:
    clean_uploads_folder(limit=10)
    name_sheet = save_sheet_cobran([df_comex, df_old], file_path, depot)

  print(df_new)
  sheet_process = {
    'df_process': {
      'new': df_comex,
      'old': list_datas['update']
    },
    'name_sheet': name_sheet 
  }

  return sheet_process 



def update_df(df_dados, df_novos):
  if df_novos.empty:
    return pd.DataFrame()
  
  for index, row in df_novos.iterrows():
    idx = df_dados[df_dados['UNIDADE'] == row['UNIDADE']].index

    if not idx.empty:
      df_dados.loc[idx, 'DATA. PAG'] = row['DATA. PAG']
      df_dados.loc[idx, 'VALORES'] = df_dados['VALORES'].apply(
        lambda x: int(float(str(x).replace(',', '.'))) if pd.notna(x) and x != '' else ''
      )
      df_dados.loc[idx, 'NF'] = (
        int(float(row['NF']))
        if pd.notna(row['NF']) and row['NF'] != '' 
        else ''
      )
      df_dados.loc[idx, 'TERMO'] = row['TERMO'] if pd.notna(row['TERMO']) else ''
      df_dados.loc[idx, 'DOCUMENTACAO'] = row['DOCUMENTACAO'] if pd.notna(row['DOCUMENTACAO']) else ''
      df_dados.loc[idx, 'ISENTO'] = row['ISENTO']
      df_dados.loc[idx, 'OBS SAC'] = row['OBS SAC']
      df_dados.loc[idx, 'SAC'] = row['SAC']
      df_dados.loc[idx, 'V. ISENTO'] = row['V. ISENTO']

  for col in ['NF', 'DATA. PAG', 'DOCUMENTACAO', 'TERMO']:
    df_dados[col] = df_dados[col].fillna('').replace({'nan': ''})

  return df_dados


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
  return json.loads(req.content)

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



def comex(df, set_progress, depot):
  if set_progress:
    set_progress(0)
  print('processando', depot)
 
  total_unidades = df['UNIDADE'].nunique()

  if not df.empty:
    df = df.dropna(subset=['ENTRADA'])

    for i, unidade in enumerate(df['UNIDADE']):
      if pd.notna(df.loc[df['UNIDADE'] == unidade, 'OBS'].values[0]) and df.loc[df['UNIDADE'] == unidade, 'OBS'].values[0].strip() != '':
        continue
      df_get_uni = pd.DataFrame(get_cnpj_unit(unidade))

      dados_validos = df_get_uni.loc[df_get_uni['importador_cnpj'] != ""]
      dados_validos = dados_validos.dropna(subset=['importador_cnpj'])

      dados_validos['data_operacao'] = pd.to_datetime(dados_validos['data_operacao'], format='%Y-%m-%d')

      dados_validos = dados_validos[dados_validos['data_operacao'].dt.year == dados_validos['data_operacao'].dt.year.max()]
      dados_validos = dados_validos[dados_validos['data_operacao'].dt.month == dados_validos['data_operacao'].dt.month.max()]

      dados_ordenados = dados_validos.sort_values(by='tipo_conhecimento', key=lambda x: x != 'HBL')

      cnpj_mais_recente = dados_ordenados.iloc[0]['importador_cnpj'] if not dados_ordenados.empty else ''

      if dados_ordenados.empty:
        df.loc[df["UNIDADE"] == unidade, 'CNPJ HBL'] = cnpj_mais_recente
        progress_percent = (i + 1) / total_unidades * 100
        if set_progress:
          set_progress(round(progress_percent))
        continue

      if dados_ordenados.iloc[0]['tipo_conhecimento'] != 'HBL':
        df.loc[df["UNIDADE"] == unidade, 'OBS'] = f'SEM HBL/AGENDADO NO {dados_ordenados.iloc[0]["tipo_conhecimento"]}'
      else:
        df.loc[df["UNIDADE"] == unidade, 'OBS'] = ''

      df.loc[df["UNIDADE"] == unidade, 'CNPJ HBL'] = cnpj_mais_recente
      progress_percent = (i + 1) / total_unidades * 100
      print(round(progress_percent))

      if set_progress:
        set_progress(round(progress_percent))

    df['CNPJ HBL'] = df['CNPJ HBL'].apply(formatar_cnpj)
    df['CNPJ AGENDADO'] = df['CNPJ AGENDADO'].apply(formatar_cnpj)
    df['CNPJ TRANSPORTADORA'] = df['CNPJ TRANSPORTADORA'].apply(formatar_cnpj)
    df = df.drop_duplicates(subset=['UNIDADE'])
  
  if set_progress:
    set_progress(100)

  print('processado', depot)
  return df
