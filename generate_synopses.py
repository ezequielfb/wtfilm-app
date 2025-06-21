# generate_synopses.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega a chave de API do arquivo .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("A GEMINI_API_KEY não foi definida no arquivo .env!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Lista de filmes para gerar as sinopses
FILM_TITLES = [
    "Matrix", "Titanic", "O Poderoso Chefão", "Forrest Gump", "O Rei Leão",
    "De Volta para o Futuro", "Jurassic Park", "Pulp Fiction", "Star Wars: Uma Nova Esperança",
    "O Iluminado", "Psicose", "Clube da Luta", "A Origem", "O Senhor dos Anéis: A Sociedade do Anel",
    "Indiana Jones e os Caçadores da Arca Perdida", "E.T. o Extraterrestre"
]

movie_data_list = []
print("Iniciando a geração de sinopses com a API do Gemini...")

for title in FILM_TITLES:
    print(f"Gerando para: {title}...")
    prompt = f"Gere uma sinopse de uma única frase, que seja intencionalmente ruim, engraçada e excessivamente literal para o filme '{title}'. Não mencione nomes de personagens, atores ou o título do filme."
    try:
        response = model.generate_content(prompt)
        bad_synopsis = response.text.strip().replace('"', '')
        movie_data_list.append({ "title": title, "synopsis": bad_synopsis })
    except Exception as e:
        print(f"ERRO ao gerar para '{title}': {e}")

# Salva a lista completa em um arquivo JSON
with open('movies.json', 'w', encoding='utf-8') as f:
    json.dump(movie_data_list, f, ensure_ascii=False, indent=4)

print(f"\nArquivo 'movies.json' criado com {len(movie_data_list)} filmes.")