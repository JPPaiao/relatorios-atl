import pandas as pd
from connect_api.connect_api import main

service = main()
sheet_ids = service['sheet_ids']

def create_sheet_if_not_exists(sheet_name, depot):
  # Verifica se a aba existe
  sheet_metadata = service['sheet'].get(spreadsheetId=sheet_ids[depot]).execute()
  sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
  
  # Cria a aba se não existir
  if sheet_name not in sheet_names:
    requests = [{
      'addSheet': {
        'properties': {
          'title': sheet_name
        }
      }
    }]
    body = {'requests': requests}
    service['sheet'].batchUpdate(
      spreadsheetId=sheet_ids[depot],
      body=body
    ).execute()

    body = {'values': [['UNIDADE', 'TIPO', 'OWNER', 'ENTRADA', 'CNPJ AGENDADO', 'CNPJ HBL', 'TRANSPORTADORA', 'CNPJ TRANSPORTADORA', 'VALORES', 'OBS', 'DATA. PAG', 'NF', 'ISENTO', 'V. ISENTO',	'OBS SAC',	'SAC']]}
    service['sheet'].values().update(
      spreadsheetId=sheet_ids[depot],
      range=f"{sheet_name}!A1",
      valueInputOption='RAW',
      body=body
    ).execute()

def dates_df(df, depot):
  df = df[df['ENTRADA'].notna()]
  df['ENTRADA'] = pd.to_datetime(df['ENTRADA'], format='%d/%m/%Y', errors='coerce')
  grouped = df.groupby([df['ENTRADA'].dt.year, df['ENTRADA'].dt.month])
  months = []

  for (year, month), group in grouped:
    month_name = f"{month:02}-{year}" 
    create_sheet_if_not_exists(month_name, depot)
    months.append(month_name)

  return {
    'df_for_months': grouped,
    'months': months
  }