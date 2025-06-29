# app.py

import os
import json
from flask import Flask
import google.generativeai as genai
from dotenv import load_dotenv

def create_app():
    """Cria e configura a instância do aplicativo Flask."""
    load_dotenv()
    
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY"),
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
    )

    if app.config['GEMINI_API_KEY']:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
        app.config['GEMINI_MODEL'] = genai.GenerativeModel('gemini-1.5-flash')
    else:
        app.config['GEMINI_MODEL'] = None

    try:
        with open('movies.json', 'r', encoding='utf-8') as f:
            app.config['MASTER_LOCAL_MOVIES'] = json.load(f)
    except FileNotFoundError:
        app.config['MASTER_LOCAL_MOVIES'] = [] # Mudança para lista vazia em caso de erro
    
    try:
        with open('movie_database.json', 'r', encoding='utf-8') as f:
            app.config['MASTER_TITLES_FOR_IA'] = json.load(f)
    except FileNotFoundError:
        app.config['MASTER_TITLES_FOR_IA'] = [] # Mudança para lista vazia em caso de erro

    app.config['PROMPT_TEMPLATES'] = [
        "Em uma única e concisa frase, descreva o objetivo principal do protagonista de '{title}' e o maior obstáculo em seu caminho. Não use nomes de personagens ou lugares.",
        "Resuma a trama de '{title}' como se fosse uma reclamação postada em uma rede social sobre um inconveniente. Não mencione nomes ou o título do filme, seja muito breve.",
        "Resuma '{title}' em uma frase, focando na pior decisão tomada pelo protagonista que inicia toda a confusão. Não mencione nomes.",
        "Como um personagem secundário totalmente confuso descreveria os eventos de '{title}' em uma ou duas frases curtas? Foque na confusão dele. Não mencione nomes.",
        "Resuma a trama de '{title}' do ponto de vista do vilão, que acredita genuinamente ser o herói incompreendido da história. Mantenha em uma ou duas frases e não use nomes.",
        "Resuma a premissa de '{title}' da forma mais burocrática e sem emoção possível, como se fosse um relatório de incidente para uma seguradora. Máximo de duas frases. Não use nomes.",
        "Descreva o problema central de '{title}' como uma avaliação de 1 estrela para um serviço, produto ou local. Exemplo: 'Péssimo serviço de cruzeiro, bateu num iceberg'. Responda em uma frase e não use nomes.",
        "Como um idoso que só assistiu metade de '{title}' descreveria a trama para um amigo? Em uma ou duas frases, com muita imprecisão e confusão. Não mencione nomes e seja breve.",
        "Descreva o enredo de '{title}' como se fosse uma fofoca mal contada em um grupo de mensagens de família. Use tom informal, em até duas frases. Não use nomes.",
        "Descreva o enredo de '{title}' como se fosse uma crítica sarcástica escrita por alguém que claramente não entendeu o filme. Use no máximo duas frases. Não cite nomes.",
        "Descreva o enredo de '{title}' como se tivesse falando com uma criança, usando voz fina e fofinha, exageradamente. Use no máximo duas frases. Não cite nomes. seja breve."
    ]  

    from wtfilm.routes.game import game_bp
    app.register_blueprint(game_bp)

    return app

# Criei a instância do app aqui, no escopo global do arquivo.
# O Gunicorn e outras ferramentas de produção procurarão por esta variável.
app = create_app()

# O bloco if __name__ == '__main__' agora só serve para rodar o servidor de desenvolvimento
# localmente no seu PC com Windows. Ele não será executado no servidor de produção.
if __name__ == '__main__':
    app.run(debug=True)