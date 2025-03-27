import pandas as pd

def scan_repets(new, old):
  """
  Verifica se há dados repetidos nos DataFrames 'new' e 'old',
  e depois verifica se há repetições ao juntar ambos.

  Args:
      new (pd.DataFrame): Novo conjunto de dados.
      old (pd.DataFrame): Conjunto de dados antigo.

  Returns:
      dict: Dicionário contendo DataFrames com registros duplicados.
  """
  # Verificar duplicatas dentro de cada DataFrame separadamente

  df_new_repetidos = pd.DataFrame()
  df_old_repetidos = pd.DataFrame()
  df_geral_repetidos = pd.DataFrame()

  if not new.empty and 'UNIDADE' in new.columns:
    df_new_repetidos = new[new.duplicated(subset=['UNIDADE'], keep=False)].sort_values(by='UNIDADE')

  if not old.empty and 'UNIDADE' in old.columns:
    df_old_repetidos = old[old.duplicated(subset=['UNIDADE'], keep=False)].sort_values(by='UNIDADE')

  # Juntar os dois DataFrames
  df_geral = pd.concat([new, old], ignore_index=True)

  # Verificar duplicatas após a junção
  if 'UNIDADE' in new.columns and 'UNIDADE' in old.columns:
    df_geral_repetidos = df_geral[df_geral.duplicated(subset=['UNIDADE'], keep=False)].sort_values(by='UNIDADE')

  # Exibir os resultados
  print("🔄 Duplicados em 'new':")
  print(df_new_repetidos)

  print("\n🔄 Duplicados em 'old':")
  print(df_old_repetidos)

  print("\n🔄 Duplicados na junção:")
  print(df_geral_repetidos)

