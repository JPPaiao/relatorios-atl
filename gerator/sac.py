def gerator_sac(df_new, df_old):
  df_old['remarks'] = df_old['remarks'].fillna('')

  remarks = {
    '': '',
    '1': 'fotos não constam sujeira',
    '2': 'sem necessidade de lavar ou varrer',
    '3': 'fotos de origem comprovam piso sujo',
    '4': 'sujo na origem/comprovado',
    '5': 'fotos ruins',
    '6': 'unidade limpa',
    '7': 'o piso está velho',
    '8': 'conforme BL',
    '9': 'lavada antes da entrega',
    '10': 'sem fotos do interior',
    '11': 'comprovado por fotos dos containers na origem já estavam sujos',
    '12': 'fotos de outra unidade',
    '13': 'foram anexadas fotos de dois tipos de piso',
    '14': 'produto não gera odor',
    '15': 'unidade precisava lavar e foi lançada p/ varrer',
    '16': 'não possui fotos no sistema',
    '17': 'piso diferente da foto da origem',
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

  # 'ISENTO', 'OBS SAC', 'SAC', 'V. ISENTO'  =  ordem

  for i, unidade in enumerate(df_new['UNIDADE']):
    isentos = df_old.loc[df_old['cntr'] == unidade, 'remarks'].values[0]
    isento_separado = isentos.split(' - ')
    array_remarks = [item for parte in isento_separado for item in parte.split('-')]

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
        service += services[array_remarks[s]]
      else: 
        service = ''

    df_new.loc[df_new['UNIDADE'] == unidade, 'ISENTO'] = isento
    df_new.loc[df_new['UNIDADE'] == unidade, 'OBS SAC'] = remark
    df_new.loc[df_new['UNIDADE'] == unidade, 'SAC'] = colab
    df_new.loc[df_new['UNIDADE'] == unidade, 'V. ISENTO'] = service

  return df_new