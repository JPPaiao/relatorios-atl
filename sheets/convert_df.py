from googleapiclient.errors import HttpError
import pandas as pd

COLUMNS = ['UNIDADE', 'TIPO', 'OWNER', 'ENTRADA', 'CNPJ AGENDADO', 'CNPJ HBL', 'TRANSPORTADORA', 'CNPJ TRANSPORTADORA', 'VALORES', 'OBS', 'DATA. PAG', 'NF', 'TERMO', 'DOCUMENTACAO', 'ISENTO', 'V. ISENTO',	'OBS SAC',	'SAC']

def sheet_for_dataframe(sheet):
  try:
    if sheet:
      for i in range(len(sheet)):
        if len(sheet[i]) < len(COLUMNS):
          lack = len(COLUMNS) - len(sheet[i])
          sheet[i].extend([''] * lack)

        elif len(sheet[i]) > len(COLUMNS):
          sheet[i] = sheet[i][:len(COLUMNS)]

      df = pd.DataFrame(sheet, columns=COLUMNS)
      return df
    else:
      print("Nenhum dado encontrado.")
      return pd.DataFrame()

  except HttpError as err:
    print(err)

def dataframe_for_sheet(df, collumn=False):
  if not df.empty:
    df['ENTRADA'] = df['ENTRADA'].apply(format_date)
    for col in ['NF', 'DATA. PAG', 'DOCUMENTACAO', 'TERMO']:
      df[col] = df[col].fillna('').replace({'nan': ''})

    convert = df.values.tolist()

    if convert[0][0] != 'UNIDADE' and collumn:
      convert.insert(0, COLUMNS)
    
    return convert
  else:
    print("Nenhum dado encontrado.")
    return None

def format_date(valor):
  if isinstance(valor, str) and valor != '':
    return valor
  elif isinstance(valor, pd.Timestamp):
    return valor.strftime('%d-%m-%Y %H:%M:%S')
  else:
    return ''