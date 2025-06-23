# tests/test_game.py

import pytest
from flask import session
from app import create_app

# --- Fixtures (app, client) - sem mudanças ---
@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

# --- Testes para normalize_string - sem mudanças ---
from wtfilm.routes.game import normalize_string

def test_normalize_string_com_maiusculas_e_acentos():
    input_text = "Star Wars: O Despertar da Força!"
    expected_output = "star wars o despertar da forca"
    actual_output = normalize_string(input_text)
    assert actual_output == expected_output

def test_normalize_string_com_numeros_e_espacos_extras():
    input_text = "  Velozes & Furiosos 9  "
    expected_output = "velozes furiosos 9"
    actual_output = normalize_string(input_text)
    assert actual_output == expected_output

def test_normalize_string_com_string_vazia():
    input_text = ""
    expected_output = ""
    actual_output = normalize_string(input_text)
    assert actual_output == expected_output


# --- NOVOS TESTES para a rota check_answer (COM A CORREÇÃO) ---

def test_check_answer_correct(client):
    """Testa se a rota retorna 'correct' para um palpite exato."""
    # <<< MUDANÇA: Usando session_transaction para garantir que a sessão seja salva >>>
    with client.session_transaction() as sess:
        sess['current_movie'] = {
            "display_title": "Matrix",
            "aliases": ["Matrix", "The Matrix"]
        }
        sess['current_chances'] = 3
        sess['correct_movies'] = []

    # A ação é feita FORA do bloco 'with', após a sessão ser configurada.
    response = client.post('/api/check_answer', json={'guess': 'matrix'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['result'] == 'correct'
    assert data['correctAnswer'] == 'Matrix'
    
    # Para verificar a sessão final, abrimos outra transação
    with client.session_transaction() as sess:
        assert sess['correct_movies'] == ['Matrix']

def test_check_answer_close_match(client):
    """Testa se a rota retorna 'close' para um palpite com erro de digitação."""
    # <<< MUDANÇA: Usando session_transaction >>>
    with client.session_transaction() as sess:
        sess['current_movie'] = {
            "display_title": "Jurassic Park",
            "aliases": ["Jurassic Park", "Parque dos Dinossauros"]
        }
        sess['current_chances'] = 3

    response = client.post('/api/check_answer', json={'guess': 'jurassik park'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['result'] == 'close'
    assert data['chancesLeft'] == 2
    
    with client.session_transaction() as sess:
        assert sess['current_chances'] == 2

def test_check_answer_wrong_match(client):
    """Testa se a rota retorna 'wrong' para um palpite incorreto."""
    # <<< MUDANÇA: Usando session_transaction >>>
    with client.session_transaction() as sess:
        sess['current_movie'] = {
            "display_title": "Titanic",
            "aliases": ["Titanic"]
        }
        sess['current_chances'] = 2

    response = client.post('/api/check_answer', json={'guess': 'A Origem'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['result'] == 'wrong'
    assert data['chancesLeft'] == 1
    
    with client.session_transaction() as sess:
        assert sess['current_chances'] == 1