// static/script.js (versão com limite de 15 itens no histórico)

document.addEventListener('DOMContentLoaded', () => {
    // Mapeamento dos elementos (continua igual)
    const synopsisEl = document.getElementById('synopsis');
    const guessInput = document.getElementById('guess-input');
    const guessButton = document.getElementById('guess-button');
    const feedbackMessageEl = document.getElementById('feedback-message');
    const skipButton = document.getElementById('skip-button');
    const correctListUl = document.querySelector('#correct-list ul');
    const wrongListUl = document.querySelector('#wrong-list ul');

    let isLoading = false;

    guessInput.addEventListener('animationend', () => {
        guessInput.classList.remove('shake-element');
    });

    // --- FUNÇÃO ATUALIZADA COM O LIMITE DE 15 ITENS ---
    function addToHistory(listElement, text) {
        const li = document.createElement('li');
        li.textContent = text;
        
        // 1. Adiciona o novo item no topo da lista
        listElement.prepend(li);

        // 2. Verifica se a lista agora tem mais de 15 itens
        if (listElement.children.length > 15) {
            // 3. Se tiver, remove o último item (o mais antigo)
            listElement.removeChild(listElement.lastChild);
        }
    }

    function lockGame(state) {
        isLoading = state;
        guessInput.disabled = state;
        guessButton.disabled = state;
        skipButton.disabled = state;
    }

    async function startNewGame() {
        lockGame(true);
        feedbackMessageEl.textContent = '';
        guessInput.value = '';
        
        synopsisEl.classList.remove('fade-in-element');
        synopsisEl.textContent = 'Gerando uma nova sinopse...';
        synopsisEl.classList.add('loading-text');

        const response = await fetch('/api/new_game');
        const data = await response.json();
        
        synopsisEl.classList.remove('loading-text');

        if (data.error) {
            synopsisEl.textContent = data.synopsis;
            synopsisEl.style.color = '#f1c40f';
            synopsisEl.classList.add('fade-in-element');
            guessInput.disabled = true;
            guessButton.disabled = true;
            skipButton.disabled = false;
            isLoading = false;
        } else {
            synopsisEl.style.color = '#b0b0b0';
            synopsisEl.style.opacity = 0;
            synopsisEl.textContent = data.synopsis;
            setTimeout(() => {
                synopsisEl.classList.add('fade-in-element');
            }, 20);
            lockGame(false);
            guessInput.focus();
        }
    }

    async function checkGuess() {
        if (isLoading || !guessInput.value) return;
        lockGame(true);

        const response = await fetch('/api/check_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guess: guessInput.value }),
        });
        const data = await response.json();

        switch (data.result) {
            case "correct":
                feedbackMessageEl.textContent = 'Você acertou!';
                feedbackMessageEl.style.color = '#2ecc71';
                addToHistory(correctListUl, data.correctAnswer);
                setTimeout(startNewGame, 2000);
                break;
            
            case "close":
                guessInput.classList.add('shake-element');
                feedbackMessageEl.textContent = `Quase lá! Você está perto... (${data.chancesLeft} restantes)`;
                feedbackMessageEl.style.color = '#f1c40f';
                guessInput.value = '';
                lockGame(false);
                guessInput.focus();
                break;

            case "wrong":
                if (!data.outOfChances) {
                    guessInput.classList.add('shake-element');
                    feedbackMessageEl.textContent = `Errado! Tente novamente. (${data.chancesLeft} restantes)`;
                    feedbackMessageEl.style.color = '#e74c3c';
                    guessInput.value = '';
                    lockGame(false);
                    guessInput.focus();
                } else {
                    feedbackMessageEl.textContent = `Acabaram as chances! O filme era: ${data.correctAnswer}`;
                    feedbackMessageEl.style.color = '#e74c3c';
                    addToHistory(wrongListUl, data.correctAnswer);
                    setTimeout(startNewGame, 3000);
                }
                break;
        }
    }

    async function skipQuestion() {
        if (isLoading) return;
        lockGame(true);
        const response = await fetch('/api/skip', { method: 'POST' });
        const data = await response.json();
        if (data.success && data.skippedTitle) {
            addToHistory(wrongListUl, data.skippedTitle);
        }
        startNewGame();
    }

    // Adiciona os "escutadores" de eventos
    guessButton.addEventListener('click', checkGuess);
    guessInput.addEventListener('keyup', (event) => { if (event.key === 'Enter') checkGuess(); });
    skipButton.addEventListener('click', skipQuestion);

    startNewGame();
});