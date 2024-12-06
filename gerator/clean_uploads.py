import os
from dotenv import load_dotenv

load_dotenv() 
UPLOAD_FOLDER = os.getenv('UPLOAD')

def clean_uploads_folder(limit=10, exc=5):
	# Obter a lista de todos os arquivos na pasta de uploads, ordenados pela data de modificação
	files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
	files.sort(key=os.path.getctime)  # Ordena pelos arquivos mais antigos

	# Verifica se a quantidade de arquivos excede o limite
	if len(files) >= limit:
		# Excluir os files mais antigos
		for arquivo in files[:exc]:
			print(f"Excluindo arquivo: {arquivo}")
			os.remove(arquivo)