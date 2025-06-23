# wtfilm/routes/game.py

import os
import random
import markdown
import bleach
from flask import Blueprint, render_template, jsonify, request, session
from thefuzz import fuzz

# Importando as variáveis que antes eram globais no app.py
# o app passa essas variáveis para o blueprint
from flask import current_app

# 1. Criação do Blueprint
# 'game_bp' é o nome que darei a este conjunto de rotas.
# __name__ ajuda o Flask a localizar o blueprint.
# template_folder='../../templates' diz onde encontrar os templates HTML a partir deste arquivo.
game_bp = Blueprint(
    'game_bp', __name__,
    template_folder='../../templates',
    static_folder='../../static'
)

# Funções auxiliares que agora pertencem a esse blueprint
def normalize_string(text):
    import unicodedata
    import re
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_and_sanitize_text(text):
    html = markdown.markdown(text)
    allowed_tags = ['b', 'i', 'em', 'strong', 'br']
    safe_html = bleach.clean(html, tags=allowed_tags, strip=True)
    return safe_html

# As rotas agora usam @game_bp.route() em vez de @app.route()
@game_bp.route('/')
def index():
    session.clear()
    session['game_count'] = 0
    session['correct_movies'] = []
    session['wrong_movies'] = []
    session['played_local_titles'] = []
    session['played_ia_titles'] = []
    return render_template('index.html')

@game_bp.route('/api/new_game')
def new_game():
    session['current_chances'] = 3
    session['game_count'] = session.get('game_count', 0) + 1
    
    chosen_movie_object = None
    is_ia_game = session['game_count'] > 1

    if not is_ia_game:
        played_titles = session.get('played_local_titles', [])
        available_movies = [m for m in current_app.config['MASTER_LOCAL_MOVIES'] if m['title'] not in played_titles]
        if not available_movies:
            session['played_local_titles'] = []
            available_movies = current_app.config['MASTER_LOCAL_MOVIES']
        
        temp_movie = random.choice(available_movies)
        session['played_local_titles'].append(temp_movie['title'])
        chosen_movie_object = { 
            "display_title": temp_movie["title"], 
            "aliases": [temp_movie["title"]], 
            "synopsis": temp_movie["synopsis"] 
        }
    else:
        played_titles = session.get('played_ia_titles', [])
        available_movies = [m for m in current_app.config['MASTER_TITLES_FOR_IA'] if m['display_title'] not in played_titles]
        if not available_movies:
            session['played_ia_titles'] = []
            available_movies = current_app.config['MASTER_TITLES_FOR_IA']
            
        movie_identity = random.choice(available_movies)
        session['played_ia_titles'].append(movie_identity['display_title'])
        
        model = current_app.config.get('GEMINI_MODEL')
        if model:
            random_template = random.choice(current_app.config['PROMPT_TEMPLATES'])
            prompt = random_template.format(title=movie_identity['display_title'])
            try:
                generation_config = {"max_output_tokens": 80}
                response = model.generate_content(prompt, generation_config=generation_config)
                synopsis_text = process_and_sanitize_text(response.text)
                if not synopsis_text:
                    synopsis_text = f"Nossa IA ficou sem palavras para descrever '{movie_identity['display_title']}', mas aqui vai uma dica: é um filme famoso!"
                chosen_movie_object = { "display_title": movie_identity['display_title'], "aliases": movie_identity['aliases'], "synopsis": synopsis_text }
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

@game_bp.route('/api/new_synopsis', methods=['POST'])
def new_synopsis():
    if session.get('current_chances', 0) <= 1:
        return jsonify({"error": "Você não tem mais novas descrições"}), 400

    current_movie = session.get('current_movie')
    model = current_app.config.get('GEMINI_MODEL')
    if not model or not current_movie or session.get('game_count', 0) <= 1:
        return jsonify({"error": "Ação não disponível para este filme."}), 400

    try:
        random_template = random.choice(current_app.config['PROMPT_TEMPLATES'])
        prompt = random_template.format(title=current_movie['display_title'])
        generation_config = {"max_output_tokens": 80}
        response = model.generate_content(prompt, generation_config=generation_config)
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

    return jsonify({ "newSynopsis": new_synopsis_text, "chancesLeft": session['current_chances'] })

@game_bp.route('/api/check_answer', methods=['POST'])
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
    return jsonify({ "result": result_status, "chancesLeft": session['current_chances'], "outOfChances": out_of_chances, "correctAnswer": correct_display_title })

@game_bp.route('/api/skip', methods=['POST'])
def skip():
    current_movie = session.get('current_movie')
    skipped_title = "Filme Desconhecido"
    if current_movie and not current_movie.get("error"):
        skipped_title = current_movie.get('display_title', skipped_title).title()
        session['wrong_movies'].append(skipped_title)
        
    session.modified = True
    return jsonify({"success": True, "skippedTitle": skipped_title})