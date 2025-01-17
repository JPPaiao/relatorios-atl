import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = 'connect_api/server_key.json'
HOMOLOG = {
  'nav': os.getenv('ID_HOMOLOG'),
  'gja': os.getenv('ID_HOMOLOG'),
  'pga': os.getenv('ID_HOMOLOG'),
}

SAMPLE_RANGE_NAME = "Página1" 

def main():  
  credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
  )
  service = build("sheets", "v4", credentials=credentials)
  sheet = service.spreadsheets()

  return {
    'sheet': sheet,
    'sheet_ids': HOMOLOG,
    'sheet_range': SAMPLE_RANGE_NAME,
  }

