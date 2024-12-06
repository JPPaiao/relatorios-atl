import os.path
# import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HOMOLOG = {
  'nav': os.getenv('ID_HOMOLOG'),
  'gja': os.getenv('ID_HOMOLOG'),
  'pga': os.getenv('ID_HOMOLOG'),
}
 
# IDS = {
#   'nav': os.getenv('ID_NAV'),
#   'gja': os.getenv('ID_GJA'),
#   'pga': os.getenv('ID_PGA'),
# }

SAMPLE_RANGE_NAME = "Página1"

# def main():
#   creds = None

#   if os.path.exists("connect_api/token.json"):
#   # if os.path.exists("/var/www/geradorrelatorio/connect_api/token.json"):
#     creds = Credentials.from_authorized_user_file("connect_api/token.json", SCOPES)
#     # creds = Credentials.from_authorized_user_file("/var/www/geradorrelatorio/connect_api/token.json", SCOPES)
#   if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#       creds.refresh(Request())
#     else:
#       flow = InstalledAppFlow.from_client_secrets_file(
#           "connect_api/client_secret.json", SCOPES
#           # "/var/www/geradorrelatorio/connect_api/client_secret.json", SCOPES
#       )
#       creds = flow.run_local_server(port=0)
def main():
  creds = None
  token_path = "connect_api/token.json"
  client_secret_path = "connect_api/client_secret.json"

  # Carregar o token existente, se disponível
  if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

  # Verificar se as credenciais são válidas
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      # Executa o fluxo de autenticação para obter novas credenciais
      flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
      creds = flow.run_local_server(port=0)
    # try:
    #   creds = flow.run_local_server(port=0)
    # except webbrowser.Error:
    #   webbrowser.register('firefox', None, webbrowser.BackgroundBrowser("/usr/bin/firefox"))
    #   creds = flow.run_local_server(port=0, open_browser=True)


    with open("connect_api/token.json", "w") as token:
    # with open("/var/www/geradorrelatorio/connect_api/token.json", "w") as token:
      token.write(creds.to_json())

  service = build("sheets", "v4", credentials=creds)
  sheet = service.spreadsheets()

  return {
    'sheet': sheet,
    'sheet_ids': HOMOLOG,
    'sheet_range': SAMPLE_RANGE_NAME,
  }

