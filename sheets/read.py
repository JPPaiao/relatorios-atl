from itertools import chain
import time
from googleapiclient.errors import HttpError
import numpy as np
from connect_api.connect_api import main

sheet = main()

def read_sheets(depot, start_month=None, end_month=None, month=False):
  try:
    sheet_ids = sheet['sheet_ids']
    time.sleep(1)

    if end_month is None:
      end_month = start_month

    months_sheet = []

    if start_month and end_month:
      month_range = filter_month_range(depot, end_month, start_month)
      days_sheet = []
      columns_value = []

      for month in month_range:
        print(month) 
        try:
          result = sheet['sheet'].values().get(spreadsheetId=sheet_ids[depot], range=month).execute()
          values = result.get("values", [])

          columns_value = values[0]
          date_separetor = start_month.split('-')
          
          if len(date_separetor) > 2:
            filtered_values = filter_days(values, start_month, end_month)
            if filtered_values:
              days_sheet.append(filtered_values)
          else:
            if len(values) >= 1 and values[0][0] == 'UNIDADE' and month:
              if len(values[1:]) >= 1:
                months_sheet.append(values[1:])
            elif len(values) > 0:
              months_sheet.append(values)
            else:
              print(f"Sem dados para o month: {month}")

        except HttpError as err:
          print(f"Erro ao acessar dados para o mes {month}: {err}")

      return {
        'sheet': days_sheet if days_sheet else months_sheet,
        'columns': columns_value
      }

    if not start_month and not end_month:
      month = filter_month(depot)
      months = [] 

      for m in month:
        result = sheet['sheet'].values().get(spreadsheetId=sheet_ids[depot], range=m).execute()
        values = result.get("values", [])

        if len(values) >= 1 and values[0][0] == 'UNIDADE':
          months.append(values[1:])
        elif len(values) >= 1 and values:
          months.append(values)

      return months
  except HttpError as err:
    print(err)
    return []
  
def filter_days(values, start_date, end_date):
  """
  Filtra as linhas da aba com base no intervalo de dias.
  """
  start_day, start_month, start_year = map(int, start_date.split('-'))
  end_day, end_month, end_year = map(int, end_date.split('-'))

  filtered_data = []
  for row in values:
    if len(row) > 0:
      try:
        raw_date = row[3]  # Supondo que a data relevante esteja nesta coluna
        date_parts = raw_date.split(' ')[0]  # Remove a parte de hora, se existir
        day, month, year = map(int, date_parts.split('-'))
        

        if (year, month, day) >= (start_year, start_month, start_day) and \
          (year, month, day) <= (end_year, end_month, end_day):
          filtered_data.append(row)
      except ValueError:
        continue  # Ignora linhas com formato inválido
  
  return filtered_data

def filter_month(depot):
  sheet_ids = sheet['sheet_ids']

  sheet_metadata = sheet['sheet'].get(spreadsheetId=sheet_ids[depot]).execute()
  sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]

  list_names = [sheet_names[-1]]

  if len(sheet_names) > 1:
    list_names.append(sheet_names[-2])

  return list_names

def filter_month_range(depot, start_month, end_month):
  def convert_date_to_tuple(month_year):
    date_destructor = month_year.split('-')
    day, month, year = '', '', ''

    if len(date_destructor) == 3:
      month = date_destructor[1]
      year = date_destructor[2]
    else:
      month, year = month_year.split('-')

    return (int(year), int(month))
  
  if start_month == end_month:
    (year, month) = convert_date_to_tuple(start_month)
    return [f'{month:02}-{year}']

  sheet_ids = sheet['sheet_ids']
  sheet_metadata = sheet['sheet'].get(spreadsheetId=sheet_ids[depot]).execute()
  sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]

  converted_dates = [convert_date_to_tuple(date) for date in sheet_names]

  start_date = convert_date_to_tuple(start_month)
  end_date = convert_date_to_tuple(end_month)

  filtered_dates = [
    (year, month) for year, month in converted_dates
    if (year, month) >= end_date and (year, month) <= start_date
  ]
 
  sorted_dates = sorted(filtered_dates, key=lambda x: (x[0], x[1]), reverse=True)
  formatted_filtered_dates = [f"{month:02d}-{year}" for year, month in sorted_dates]

  return formatted_filtered_dates