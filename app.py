# app.py

import os
import json
import random
import re
import unicodedata
from flask import Flask, render_template, jsonify, request, session
import google.generativeai as genai
from dotenv import load_dotenv
from thefuzz import fuzz
# <<< MUDANÇA: Novas importações >>>
import markdown
import bleach

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
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
    "Em uma única e concisa frase, descreva o objetivo principal do protagonista de '{title}' e o maior obstáculo em seu caminho. Não use nomes de personagens ou lugares.",
    "Resuma a trama de '{title}' como se fosse uma reclamação postada em uma rede social sobre um inconveniente. Não mencione nomes ou o título do filme, seja o mais breve e obejetiva o possivel.",
    "Resuma '{title}' em uma frase, focando na pior decisão tomada pelo protagonista que inicia toda a confusão. Não mencione nomes.",
    "Como um personagem secundário totalmente confuso descreveria os eventos de '{title}' em uma ou duas frases curtas? Foque na confusão dele. Não mencione nomes.",
    "Classifique o filme '{title}' com um gênero comicamente errado e justifique o porquê em uma única frase. Exemplo: 'É uma comédia romântica sobre um homem e seu barco'. Não use nomes.",
    "Resuma a premissa de '{title}' da forma mais burocrática e sem emoção possível, como se fosse um relatório de incidente para uma seguradora. Máximo de duas frases. Não use nomes.",
    "Descreva o problema central de '{title}' como uma avaliação de 1 estrela para um serviço, produto ou local. Exemplo: 'Péssimo serviço de cruzeiro, bateu num iceberg'. Responda em uma frase e não use nomes.",
]

def normalize_string(text):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# <<< MUDANÇA: Nova função para processar e sanitizar o texto da IA >>>
def process_and_sanitize_text(text):
    """Converte Markdown para HTML e limpa, permitindo apenas tags seguras."""
    # Converte o Markdown gerado pela IA em HTML (ex: *texto* -> <em>texto</em>)
    html = markdown.markdown(text)
    
    # Define quais tags HTML são permitidas. O resto será removido ou escapado.
    allowed_tags = ['b', 'i', 'em', 'strong', 'br']
    
    # Limpa o HTML, mantendo apenas as tags seguras para evitar ataques XSS.
    safe_html = bleach.clean(html, tags=allowed_tags, strip=True)
    return safe_html

@app.route('/')
def index():
    session.clear()
    session['game_count'] = 0
    session['correct_movies'] = []
    session['wrong_movies'] = []
    session['played_local_titles'] = []
    session['played_ia_titles'] = []
    return render_template('index.html')

@app.route('/api/new_game')
def new_game():
    session['current_chances'] = 3
    session['game_count'] = session.get('game_count', 0) + 1
    
    chosen_movie_object = None
    is_ia_game = session['game_count'] > 1

    if not is_ia_game:
        played_titles = session.get('played_local_titles', [])
        available_movies = [m for m in MASTER_LOCAL_MOVIES if m['title'] not in played_titles]
        if not available_movies:
            session['played_local_titles'] = []
            available_movies = MASTER_LOCAL_MOVIES
        
        temp_movie = random.choice(available_movies)
        session['played_local_titles'].append(temp_movie['title'])
        chosen_movie_object = { 
            "display_title": temp_movie["title"], 
            "aliases": [temp_movie["title"]], 
            "synopsis": temp_movie["synopsis"] 
        }
    else:
        played_titles = session.get('played_ia_titles', [])
        available_movies = [m for m in MASTER_TITLES_FOR_IA if m['display_title'] not in played_titles]
        if not available_movies:
            session['played_ia_titles'] = []
            available_movies = MASTER_TITLES_FOR_IA
            
        movie_identity = random.choice(available_movies)
        session['played_ia_titles'].append(movie_identity['display_title'])
        
        if model:
            random_template = random.choice(PROMPT_TEMPLATES)
            prompt = random_template.format(title=movie_identity['display_title'])
            try:
                generation_config = {"max_output_tokens": 80}
                response = model.generate_content(prompt, generation_config=generation_config)
                
                # <<< MUDANÇA: Usando a nova função de sanitização >>>
                synopsis_text = process_and_sanitize_text(response.text)
                
                if not synopsis_text:
                    synopsis_text = f"Nossa IA ficou sem palavras para descrever '{movie_identity['display_title']}', mas aqui vai uma dica: é um filme famoso!"

                chosen_movie_object = {
                    "display_title": movie_identity['display_title'],
                    "aliases": movie_identity['aliases'],
                    "synopsis": synopsis_text
                }
            except Exception as e:
                print(f"ERRO na API do Gemini: {e}")
                chosen_movie_object = { "display_title": "Erro de IA", "aliases": [], "synopsis": "Ops, algo deu errado ao contatar nossa IA. Por favor, clique em 'Pular' para um novo desafio!", "error": True }
        else:
            chosen_movie_object = { "display_title": movie_identity['display_title'], "aliases": movie_identity['aliases'], "synopsis": "Modo IA desabilitado, mas aqui está um filme para você adivinhar!" }
            
    session['current_movie'] = chosen_movie_object
    session.modified = True
    
    return jsonify({
        "synopsis": chosen_movie_object.get("synopsis"), 
        "chancesLeft": session['current_chances'], 
        "error": chosen_movie_object.get("error", False),
        "isIAGame": is_ia_game 
    })

@app.route('/api/new_synopsis', methods=['POST'])
def new_synopsis():
    if session.get('current_chances', 0) <= 1:
        return jsonify({"error": "Você não tem mais novas descrições"}), 400

    current_movie = session.get('current_movie')
    if not model or not current_movie or session.get('game_count', 0) <= 1:
        return jsonify({"error": "Ação não disponível para este filme."}), 400

    try:
        random_template = random.choice(PROMPT_TEMPLATES)
        prompt = random_template.format(title=current_movie['display_title'])
        generation_config = {"max_output_tokens": 80}
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # <<< MUDANÇA: Usando a nova função de sanitização >>>
        new_synopsis_text = process_and_sanitize_text(response.text)

        if not new_synopsis_text:
            new_synopsis_text = "A IA tentou, mas falhou em criar uma nova sinopse. Nenhuma chance foi gasta."
        else:
            session['current_chances'] -= 1
            session['current_movie']['synopsis'] = new_synopsis_text
            session.modified = True
            
    except Exception as e:
        print(f"ERRO na API do Gemini (new_synopsis): {e}")
        return jsonify({"error": "Não foi possível gerar uma nova sinopse no momento."}), 500

    return jsonify({
        "newSynopsis": new_synopsis_text,
        "chancesLeft": session['current_chances']
    })

@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    current_movie = session.get('current_movie')
    if not current_movie:
        return jsonify({"result": "error", "message": "Sessão expirada. Atualize a página."}), 400

    user_guess = request.json.get('guess', '')
    if not user_guess:
        return jsonify({"result": "error", "message": "Nenhuma resposta fornecida."}), 400

    normalized_guess = normalize_string(user_guess)
    valid_answers = [normalize_string(alias) for alias in current_movie.get('aliases', [])]
    correct_display_title = current_movie.get('display_title', '').title()
    
    result_status = "wrong" 
    
    if normalized_guess in valid_answers:
        is_correct = True
    else:
        is_correct = False
    
    if is_correct:
        result_status = "correct"
        session['correct_movies'].append(correct_display_title)
    else:
        best_match_score = 0
        for answer in valid_answers:
            ratio_score = fuzz.ratio(normalized_guess, answer)
            partial_score = fuzz.partial_ratio(normalized_guess, answer)
            current_score = max(ratio_score, partial_score if len(normalized_guess) < len(answer) else 0)
            if current_score > best_match_score:
                best_match_score = current_score
        if best_match_score > 85:
            result_status = "close"
            session['current_chances'] -= 1
        else:
            result_status = "wrong"
            session['current_chances'] -= 1
            
    out_of_chances = session['current_chances'] <= 0
    if out_of_chances and not is_correct:
        session['wrong_movies'].append(correct_display_title)
        
    session.modified = True
    return jsonify({ 
        "result": result_status, 
        "chancesLeft": session['current_chances'], 
        "outOfChances": out_of_chances, 
        "correctAnswer": correct_display_title 
    })

@app.route('/api/skip', methods=['POST'])
def skip():
    current_movie = session.get('current_movie')
    skipped_title = "Filme Desconhecido"
    if current_movie and not current_movie.get("error"):
        skipped_title = current_movie.get('display_title', skipped_title).title()
        session['wrong_movies'].append(skipped_title)
        
    session.modified = True
    return jsonify({"success": True, "skippedTitle": skipped_title})

if __name__ == '__main__':
    app.run(debug=True)