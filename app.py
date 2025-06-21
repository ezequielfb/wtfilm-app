# app.py (Versão com tratamento de erro melhorado)

import os
import json
import random
import re
import unicodedata
from flask import Flask, render_template, jsonify, request, session
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
# ... (configuração do Gemini e carregamento de dados) ...
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
try:
    with open('movies.json', 'r', encoding='utf-8') as f:
        MASTER_LOCAL_MOVIES = json.load(f)
except FileNotFoundError:
    MASTER_LOCAL_MOVIES = [{"title": "Erro", "synopsis": "Arquivo movies.json não encontrado."}]
try:
    with open('movie_database.json', 'r', encoding='utf-8') as f:
        MASTER_TITLES_FOR_IA = json.load(f)
except FileNotFoundError:
    MASTER_TITLES_FOR_IA = [{"display_title": "Matrix", "aliases": ["Matrix"]}]
PROMPT_TEMPLATES = [
    "Descreva em uma frase o que o protagonista do filme '{title}' quer muito fazer, e os principais obstáculos que o impedem. Não use nomes.",
    "Resuma a trama de '{title}', em um pequeno texto, como se fosse uma reclamação postada em uma rede social sobre um inconveniente. Não mencione nomes ou o título do filme.",
    "Resuma '{title}' em uma frase, focando na pior decisão tomada pelo protagonista que inicia toda a confusão. Não mencione nomes.",
    "Descreva os eventos de '{title}' do ponto de vista de um personagem secundário que está confuso, mas testemunha tudo. Não mencione nomes, e faça um texto bem pequeno.",
    "Classifique '{title}' como um gênero de filme completamente errado e justifique em uma frase. Exemplo: 'É uma comédia romântica sobre um homem e seu barco'. Não mencione nomes.",
    "Descreva em uma frase a drástica mudança na rotina diária do personagem principal após os eventos de '{title}'. Não mencione nomes ou o título do filme.",
    "Descreva bem resumidamente '{title}' como se estivesse explicando para um gatinho, usando voz fininha e falando com muito carinho, Não mencione nomes ou o título do filme e seja o mais breve o possivel."
]

def normalize_string(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@app.route('/')
def index():
    session['correct_movies'] = []
    session['wrong_movies'] = []
    local_deck = list(MASTER_LOCAL_MOVIES)
    random.shuffle(local_deck)
    session['available_local_movies'] = local_deck
    ia_deck = list(MASTER_TITLES_FOR_IA)
    random.shuffle(ia_deck)
    session['available_ia_titles'] = ia_deck
    return render_template('index.html')

@app.route('/api/new_game')
def new_game():
    session['current_chances'] = 3
    session['game_count'] = session.get('game_count', 0) + 1
    chosen_movie_object = None
    if session['game_count'] <= 2:
        if not session.get('available_local_movies'):
            local_deck = list(MASTER_LOCAL_MOVIES); random.shuffle(local_deck)
            session['available_local_movies'] = local_deck
        temp_movie = session['available_local_movies'].pop()
        chosen_movie_object = { "display_title": temp_movie["title"], "aliases": [temp_movie["title"]], "synopsis": temp_movie["synopsis"] }
    else:
        if not session.get('available_ia_titles'):
            ia_deck = list(MASTER_TITLES_FOR_IA); random.shuffle(ia_deck)
            session['available_ia_titles'] = ia_deck
        movie_identity = session['available_ia_titles'].pop()
        if model:
            random_template = random.choice(PROMPT_TEMPLATES)
            prompt = random_template.format(title=movie_identity['display_title'])
            try:
                generation_config = {"max_output_tokens": 60}
                response = model.generate_content(prompt, generation_config=generation_config)
                chosen_movie_object = {
                    "display_title": movie_identity['display_title'],
                    "aliases": movie_identity['aliases'],
                    "synopsis": response.text.strip().replace('"', '')
                }
            except Exception as e:
                print(f"ERRO na API do Gemini: {e}")
                # --- MUDANÇA APLICADA AQUI ---
                chosen_movie_object = {
                    "display_title": "Erro de IA", 
                    "aliases": [], 
                    "synopsis": "Ops, algo deu errado ao contatar nossa IA. Por favor, clique em 'Pular' para um novo desafio!",
                    "error": True # Sinalizador para o frontend
                }
        else:
            chosen_movie_object = {"display_title": movie_identity['display_title'], "aliases": movie_identity['aliases'], "synopsis": "Modo IA desabilitado."}
    session['current_movie'] = chosen_movie_object
    session.modified = True
    return jsonify({"synopsis": chosen_movie_object.get("synopsis"), "chancesLeft": session['current_chances'], "error": chosen_movie_object.get("error", False)})

# O resto do arquivo (check_answer, skip) continua exatamente igual
@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    # ... código igual ao anterior ...
    current_movie = session.get('current_movie')
    user_guess = request.json.get('guess', '')
    normalized_guess = normalize_string(user_guess)
    valid_answers = [normalize_string(alias) for alias in current_movie.get('aliases', [])]
    is_correct = normalized_guess and normalized_guess in valid_answers
    result_status = "wrong"
    correct_display_title = current_movie.get('display_title', '').title()
    if is_correct:
        result_status = "correct"
        session['correct_movies'].append(correct_display_title)
    elif any(normalized_guess in answer for answer in valid_answers if len(normalized_guess) > 3):
        result_status = "close"
        session['current_chances'] -= 1
    else:
        session['current_chances'] -= 1
    out_of_chances = session['current_chances'] <= 0
    if out_of_chances and not is_correct:
        session['wrong_movies'].append(correct_display_title)
    session.modified = True
    return jsonify({ "result": result_status, "chancesLeft": session['current_chances'], "outOfChances": out_of_chances, "correctAnswer": correct_display_title })

@app.route('/api/skip', methods=['POST'])
def skip():
    # ... código igual ao anterior ...
    current_movie = session.get('current_movie')
    skipped_title = "Filme Desconhecido"
    if current_movie:
        skipped_title = current_movie.get('display_title', skipped_title).title()
        session['wrong_movies'].append(skipped_title)
    session.modified = True
    return jsonify({"success": True, "skippedTitle": skipped_title})


if __name__ == '__main__':
    app.run(debug=True)