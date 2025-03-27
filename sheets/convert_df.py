from googleapiclient.errors import HttpError
from sheets.create import create_data
from dotenv import load_dotenv
import pandas as pd
import os

# load_dotenv()
# COLUMNS = os.getenv('COLUMNS')
COLUMNS = ['UNIDADE', 'TIPO', 'OWNER', 'ENTRADA', 'CNPJ AGENDADO', 'CNPJ HBL', 'TRANSPORTADORA', 'CNPJ TRANSPORTADORA', 'VALORES', 'OBS', 'DATA. PAG', 'NF', 'TERMO', 'DOCUMENTACAO', 'ISENTO', 'V. FINAL',	'OBS SAC',	'SAC']

NEW_COLUMNS = {
  'V. ORIGINAL': 15,
  'V. DIFERENÇA': 17,
  'DATA ATUALIZACAO': 20
}

def insert_collumn(df, depot):
  verify = False

  for column, position in sorted(NEW_COLUMNS.items(), key=lambda item: item[1]):
    if column not in df.columns:
      verify = True
      df.insert(min(position, len(df.columns)), column, '')

  if "V. ISENTO" in df.columns:
    df = df.rename(columns={"V. ISENTO": "V. FINAL"})

  if verify:
    df_new_sheet = {
      'old': df,
      'new': pd.DataFrame()
    }
    print('isert')
    print(df)
    print()
    # create_data(df_new_sheet, depot)

  return df


def sheet_for_dataframe(sheet, old_column=[]):
  try:
    if old_column and sheet:
      for i in range(len(sheet)):
        if len(sheet[i]) < len(old_column):
          lack = len(old_column) - len(sheet[i])
          sheet[i].extend([''] * lack)

        elif len(sheet[i]) > len(old_column):
          sheet[i] = sheet[i][:len(old_column)]

      df = pd.DataFrame(sheet, columns=old_column)
      return df
    
    if sheet:
      columns_sheet = COLUMNS

      for new_column, position in sorted(NEW_COLUMNS.items(), key=lambda item: item[0], reverse=True):
        if new_column not in columns_sheet:
          columns_sheet.insert(position, new_column)

      for i in range(len(sheet)):
        if len(sheet[i]) < len(columns_sheet):
          lack = len(columns_sheet) - len(sheet[i])
          sheet[i].extend([''] * lack)

        elif len(sheet[i]) > len(columns_sheet):
          sheet[i] = sheet[i][:len(columns_sheet)]

      df = pd.DataFrame(sheet, columns=columns_sheet)
      return df
    else:
      print("Nenhum dado encontrado.")
      return pd.DataFrame()

  except HttpError as err:
    print(err)


def dataframe_for_sheet(df, collumn=False):
  if not df.empty:
    columns_sheet = COLUMNS

    for new_column, position in sorted(NEW_COLUMNS.items(), key=lambda item: item[0], reverse=True):
      if new_column not in columns_sheet:
        columns_sheet.insert(position, new_column)

    df['ENTRADA'] = df['ENTRADA'].apply(format_date)
    for col in ['NF', 'DATA. PAG', 'DOCUMENTACAO', 'TERMO']:
      df[col] = df[col].fillna('').replace({'nan': ''})

    convert = df.values.tolist()

    if convert[0][0] != 'UNIDADE' and collumn:
      convert.insert(0, columns_sheet)

    return convert
  else:
    print("Nenhum dado encontrado.")
    return None


def format_date(valor):
  if isinstance(valor, str) and valor != '':
    return valor
  elif isinstance(valor, pd.Timestamp):
    return valor.strftime('%d-%m-%Y')
  else:
    return ''
