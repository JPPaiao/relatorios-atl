import pandas as pd
from connect_api.connect_api import main
from googleapiclient.errors import HttpError

from gerator.gerator import comex
from sheets.create import create_data
from sheets.convert_df import dataframe_for_sheet

def filter_df(df: pd.DataFrame):
  duplicated_units = df[df.duplicated(subset=['UNIDADE'], keep=False)]
  duplicated = duplicated_units.copy()
  non_duplicated = df[~df['UNIDADE'].isin(duplicated['UNIDADE'])]
  unique_duplicated = duplicated.drop_duplicates(subset=['UNIDADE'], keep='last')

  print('não duplicatas')
  print(non_duplicated)
  print()
  print('duplicadas')
  print(duplicated_units)
  print() 
  print('sem duplicadas')
  print(unique_duplicated)
  print()

  return {
    'duplicateds': unique_duplicated,
    'non_duplicated': non_duplicated
  }

def delete(df, depot):
  df_filter = filter_df(df)
  duplicateds = df_filter['duplicateds']
  non_duplicateds = df_filter['non_duplicated']

  duplicateds['ENTRADA'] = pd.to_datetime(duplicateds['ENTRADA'], format='%d-%m-%Y', errors='coerce') 
  grouped = duplicateds.groupby([duplicateds['ENTRADA'].dt.year, duplicateds['ENTRADA'].dt.month])
  months = []

  try:
    sheet = main()
    service = sheet['sheet']
    sheet_id = sheet['sheet_ids']
    
    for (year, month), group in grouped:
      worksheets = f"{month:02}-{year}"
      months.append(worksheets)
      print(months)

      print(worksheets)
      df_comex = comex(group, None, depot)
      final_df = pd.concat([non_duplicateds, df_comex], ignore_index=True)

      for col in ['CNPJ AGENDADO', 'CNPJ HBL', 'CNPJ TRANSPORTADORA']:
        final_df[col] = final_df[col].apply(format_cnpj)
      
      df_process = {
        'old': final_df,
        'new': pd.DataFrame()
      }
      delete_sheet(service, sheet_id, worksheets, depot)
      create_data(df_process, depot)


  except HttpError as error:
    print(f"An error occurred: {error}") 
    return error

def format_cnpj(cnpj):
  return str(cnpj).zfill(14)

def delete_sheet(service, sheet_id, worksheet, depot):
  body = {}
  print('delete')

  service.values().clear(
    spreadsheetId=sheet_id[depot],
    range=worksheet,
    body=body
  ).execute()