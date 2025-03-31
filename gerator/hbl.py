import os
import pandas as pd
from sheets.convert_df import sheet_for_dataframe
from sheets.read import read_sheets
from sheets.worksheets import dates_df
from dotenv import load_dotenv

load_dotenv()
UPLOAD_FOLDER = os.getenv('UPLOAD')

def get_hbl_process(file_path, depot):
  if not file_path:
    return 'Sem arquivo'
  
  print('hbl_error')

  df = pd.read_excel(file_path)

  df_process = pd.DataFrame({
    "UNIDADE": df["cntr"],
    "ENTRADA": pd.to_datetime(df["datein"], format='%d-%m-%Y', errors='coerce')
  })

  df_for_dates = dates_df(df_process, depot)

  first_months = df_for_dates['months'][0]
  last_months = df_for_dates['months'][-1]
  sheets = read_sheets(depot, first_months, last_months)

  if sheets['sheet']:
    list_dfs = [sheet_for_dataframe(sheet, sheets['columns']) for sheet in sheets['sheet']]      
    df_sheet_concat = pd.concat(list_dfs, axis=0, ignore_index=True)

    list_units = df_process['UNIDADE'].to_list()
    df_sheets = df_sheet_concat[df_sheet_concat['UNIDADE'].isin(list_units)]
    df_hbls_process = df_sheets[['UNIDADE', 'OWNER', 'ENTRADA', 'CNPJ AGENDADO', 'CNPJ HBL', 'TRANSPORTADORA', 'CNPJ TRANSPORTADORA', 'VALORES', 'OBS' ]]
    
    new_file_name = f"hbl_{depot}.xlsx"
    process_file_path = os.path.join(UPLOAD_FOLDER, new_file_name)
    df_hbls_process.to_excel(process_file_path, index=False)

    return {
      'status': 'completed',
      'mensagem': 'Unidades não encontrados',
      'data': { process_file_path, new_file_name }
    }
  else: 
    return {
      'status': 'erro',
      'mensagem': 'Unidades não encontrados'
    }
