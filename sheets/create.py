from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime
from connect_api.connect_api import main 
from sheets.convert_df import dataframe_for_sheet

def create_data(values, depot):
  try:
    sheet = main()
    spreadsheet = sheet['sheet']
    sheet_ids = sheet['sheet_ids']
    process_data_by_month(values, spreadsheet, sheet_ids[depot])
    
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

def process_data_by_month(df_new_sheet, service, sheet_ids):
  old = df_new_sheet['old']
  new = df_new_sheet['new']

  if not old.empty:
    old['ENTRADA'] = pd.to_datetime(old['ENTRADA'], errors='coerce', dayfirst=True)
    grouped = old.groupby([old['ENTRADA'].dt.year, old['ENTRADA'].dt.month])

    for (year, month), group in grouped:
      month_name = f"{month:02}-{year}" 

      sheet_format = dataframe_for_sheet(group, True)
      print('criado')
      update_sheet(sheet_format, service, sheet_ids, month_name)
  
  if not new.empty:
    grouped = new.groupby([new['ENTRADA'].dt.year, new['ENTRADA'].dt.month])

    for (year, month), group in grouped:
      month_name = f"{month:02}-{year}" 

      sheet_format = dataframe_for_sheet(group)
      print('criado')
      add_sheet(sheet_format, service, sheet_ids, month_name)

def update_sheet(datas, service, sheet_id, worksheet):
  body = { "values": datas }
  service.values().update(
    spreadsheetId=sheet_id,
    range=worksheet,
    valueInputOption='RAW',
    body=body
  ).execute()

def add_sheet(datas, service, sheet_id, worksheet):
  body = { "values": datas }
  service.values().append(
    spreadsheetId=sheet_id,
    range=worksheet,
    valueInputOption='RAW',
    insertDataOption='INSERT_ROWS',
    body=body
  ).execute()
