import pandas as pd
from sheets.convert_df import sheet_for_dataframe
from sheets.read import read_sheets
from sheets.worksheets import dates_df

def get_hbl_process(file_path, depot):
  if not file_path:
    return 'Sem arquivo'

  df = pd.read_excel(file_path)

  df_process = pd.DataFrame({
    "UNIDADE": df["cntr"],
    "ENTRADA": pd.to_datetime(df["datein"], format='%d-%m-%Y %H:%M:%S', errors='coerce')
  })

  df_for_dates = dates_df(df_process, depot)

  first_months = df_for_dates['months'][0]
  last_months = df_for_dates['months'][-1]
  sheets = read_sheets(depot, first_months, last_months)

  if sheets:
    list_dfs = [sheet_for_dataframe(sheet) for sheet in sheets]      
    df_sheet_concat = pd.concat(list_dfs, axis=0, ignore_index=True)

    list_units = df_process['UNIDADE'].to_list()
    df_sheets = df_sheet_concat[df_sheet_concat['UNIDADE'].isin(list_units)]
    df_hbls_process = df_sheets[['UNIDADE', 'ENTRADA', 'VALORES', 'TRANSPORTADORA', 'CNPJ AGENDADO', 'CNPJ HBL']]

    process_file_path = file_path.replace('.xlsx', '_hbl.xlsx')
    df_hbls_process.to_excel(process_file_path, index=False)

    return process_file_path
