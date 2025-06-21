# WTFilm: Jogo de Adivinhar Filmes

Um jogo de navegador onde o jogador deve adivinhar o nome de um filme famoso a partir de uma sinopse intencionalmente ruim, engraçada ou excessivamente literal gerada por Inteligência Artificial.

## Sobre o Projeto

O WTFilm é uma aplicação web full-stack desenvolvida em Python com o micro-framework Flask no backend, e HTML, CSS e JavaScript puros no frontend. O principal diferencial do projeto é o uso da API do Google Gemini para gerar dinamicamente os desafios (as sinopses), garantindo uma experiência de jogo sempre nova e imprevisível. O projeto foi construído com foco em boas práticas, incluindo gerenciamento de estado por sessão, tratamento de erros, normalização de strings para uma experiência de usuário mais tolerante, e uma arquitetura de dados flexível.

## Captura de Tela

[Insira aqui uma captura de tela do jogo em funcionamento. Você pode fazer o upload da imagem para o seu repositório do GitHub e depois editar este arquivo para adicionar o link.]

## Funcionalidades

* **Sinopses Geradas por IA:** Utiliza a API do Google Gemini para criar sinopses únicas e desafiadoras a cada rodada.
* **Lógica de Jogo Híbrida:** Os primeiros desafios vêm de uma lista local para garantir velocidade, e os seguintes são gerados pela IA para garantir variedade.
* **Sistema de Chances por Rodada:** O jogador tem 3 tentativas para adivinhar cada filme, tornando o jogo dinâmico e contínuo, sem um "Game Over" final.
* **Tolerância de Resposta Avançada:** O sistema de verificação normaliza as respostas, ignorando maiúsculas/minúsculas, acentos e pontuações.
* **Suporte a Múltiplos Títulos:** Aceita diferentes nomes para o mesmo filme (ex: título em português e o original em inglês) graças a uma estrutura de dados com aliases.
* **Feedback Inteligente:** Informa ao jogador não apenas se ele errou, mas também se está "perto" da resposta correta.
* **Sistema Anti-Repetição:** Um sistema de "baralho de cartas" garante que um filme não seja repetido até que toda a lista de desafios tenha sido apresentada ao jogador.
* **Interface Reativa:** Frontend construído com JavaScript puro (Vanilla JS) que se comunica com o backend de forma assíncrona, atualizando a interface sem recarregar a página.
* **Histórico de Jogo:** Mantém um histórico visual das últimas 15 respostas certas e erradas/puladas.
* **Design Responsivo:** Interface adaptada para uma boa experiência tanto em desktops quanto em dispositivos móveis.

## Tecnologias Utilizadas

**Backend:**
* Python
* Flask (Micro-framework web)
* Gunicorn (Servidor WSGI para produção)

**Frontend:**
* HTML5
* CSS3
* JavaScript (Vanilla JS)

**APIs e Ferramentas:**
* Google Gemini API
* Git & GitHub
* Render.com (Plataforma de deploy)

## Como Executar Localmente

Siga os passos abaixo para executar o projeto no seu ambiente de desenvolvimento.

**Pré-requisitos:**
* Python 3.8+
* Git

**Passos:**

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SeuUsuario/wtfilm-app.git](https://github.com/SeuUsuario/wtfilm-app.git)
    cd wtfilm-app
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Para Windows
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Copie o conteúdo abaixo para dentro do `.env` e substitua pelos seus valores.
    ```
    # Chave para a API do Google Gemini
    GEMINI_API_KEY="SUA_CHAVE_DO_GEMINI_AQUI"

    # Chave secreta para a segurança das sessões do Flask
    FLASK_SECRET_KEY="SUA_CHAVE_SECRETA_GERADA_COM_OS.URANDOM_AQUI"
    ```

5.  **Execute a aplicação:**
    ```bash
    flask run
    ```

6.  Abra seu navegador e acesse `http://127.0.0.1:5000`.

## Próximos Passos

* Implementar a funcionalidade de revelar o pôster do filme após um acerto.
* Adicionar um sistema de pontuação ou ranking.
* Criar um modo de jogo com tempo limitado.