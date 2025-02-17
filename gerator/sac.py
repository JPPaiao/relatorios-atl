from datetime import datetime
import pandas as pd


def gerator_sac(df_new: pd.DataFrame, df_old: pd.DataFrame):
  if df_new.empty:
    return df_new

  df_old['remarks'] = df_old['remarks'].fillna('')

  remarks = {
    '': '',
    '0': '',
    '1': 'Fotos não constam sujeira',
    '2': 'Sem necessidade de lavar ou varrer',
    '3': 'Cliente Vip',
    '4': 'Sujo na origem/comprovado',
    '5': 'Fotos ruins',
    '6': 'Unidade limpa',
    '7': 'O piso está velho',
    '8': 'Conforme BL',
    '9': 'Lavada antes da entrega',
    '10': 'Sem fotos do interior',
    '11': 'Comprovado por fotos dos containers na origem já estavam sujos',
    '12': 'Fotos de outra unidade',
    '13': 'Foram anexadas fotos de dois tipos de piso',
    '14': 'Produto não gera odor',
    '15': 'Unidade precisava lavar e foi lançada p/ varrer',
    '16': 'Não possui fotos no sistema',
    '17': 'Piso diferente da foto da origem',
  }

  colabs = {
    '': '',
    '1': 'Gustavo',
    '2': 'Julia',
    '3': 'Nayara',
    '4': 'Nelson',
    '5': 'Sarah',
    '6': 'Theo',
    '7': 'Weslley',
    '8': 'Maria Eduarda',
    '9': 'Michele'
  }

  services = {
    '': '',
    'LS': 260, 
    'LQ': 350,
    'LI': 400,
    'RA': 33.82,
    'VA': 60,
    'RL': 100,
    'OR': ''
  }

  erros_list = []
  # 'ISENTO', 'OBS SAC', 'SAC', 'V. ISENTO'  =  ordem
  
  for i, unidade in enumerate(df_new['UNIDADE']):
    try:
      date_in = df_new.loc[df_new['UNIDADE'] == unidade, 'ENTRADA'].values[0]
      date_format = ''
      date_format = pd.to_datetime(date_in, dayfirst=True).strftime("%d-%m-%Y")
      
      isentos = df_old.loc[df_old['cntr'] == unidade, 'remarks'].values[0]
      isento_separado = isentos.split(' - ')
      array_remarks = [item for parte in isento_separado for item in parte.split('-')]

      values = df_new.loc[df_new['UNIDADE'] == unidade, 'V. ORIGINAL'].values[0] if df_new.loc[df_new['UNIDADE'] == unidade, 'V. ORIGINAL'].any() else df_new.loc[df_new['UNIDADE'] == unidade, 'VALORES'].values[0]

      if isinstance(values, str):
        values = values.replace(',', '.')
        values = float(values)
      elif not isinstance(values, float):
        values = float(values)

      while len(array_remarks) <= 3:
        array_remarks.append('')

      isento = array_remarks[0]
      if array_remarks[0] == 'EA':
        isento = 'Em aberto'
      elif array_remarks[0] == 'RED':
        isento = 'Redução'

      remark = remarks[array_remarks[1]]
      colab = colabs[array_remarks[2]]
      service = 0

      for s in range(3, len(array_remarks)):
        if services[array_remarks[s]] != '':
          if isinstance(services[array_remarks[s]], str): 
            service += float(services[array_remarks[s]].replace(',', '.'))
          else:
            service += float(services[array_remarks[s]])

      difference_in_values = values

      if service != '' or values != '':
        difference_in_values = float(values) - float(service)

      if service == 0:
        service = ''

      # print(df_new.loc[df_new['UNIDADE'] == unidade])

      df_new.loc[df_new['UNIDADE'] == unidade, 'ISENTO'] = isento
      df_new.loc[df_new['UNIDADE'] == unidade, 'OBS SAC'] = remark
      df_new.loc[df_new['UNIDADE'] == unidade, 'SAC'] = colab
      df_new.loc[df_new['UNIDADE'] == unidade, 'V. FINAL'] = service
      df_new.loc[df_new['UNIDADE'] == unidade, 'V. DIFERENÇA'] = difference_in_values
    except Exception as e:
      erro = {
        "unidade": unidade,
        "data": date_format,
        "mensagem": str(e)
      }
      erros_list.append(erro)

  if erros_list:
    print(erros_list)
    return {"status": "erro", "erros": erros_list}

  return df_new