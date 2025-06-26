document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const synopsisEl = document.getElementById('synopsis');
    const guessInput = document.getElementById('guess-input');
    const guessButton = document.getElementById('guess-button');
    const skipButton = document.getElementById('skip-button');
    const correctListUl = document.querySelector('#correct-list ul');
    const wrongListUl = document.querySelector('#wrong-list ul');
    const newSynopsisButton = document.getElementById('new-synopsis-button');
    const mainFeedbackEl = document.getElementById('main-feedback');
    const subFeedbackEl = document.getElementById('sub-feedback');

    // <<< MUDANÇA: Seletores para o modal de ajuda >>>
    const helpModal = document.getElementById('help-modal');
    const openHelpModalButton = document.getElementById('open-help-modal');
    const closeHelpModalButton = document.getElementById('close-help-modal');

    // State
    let isLoading = false;
    let feedbackFadeoutTimer = null;

    // <<< MUDANÇA: Funções para controlar o modal >>>
    function openModal() {
        helpModal.classList.remove('hidden');
    }
    function closeModal() {
        helpModal.classList.add('hidden');
    }

    // Funções auxiliares... (o resto do seu script.js continua aqui)
    guessInput.addEventListener('animationend', () => {
        guessInput.classList.remove('shake-element');
    });

    function addToHistory(listElement, text) {
        const li = document.createElement('li');
        li.textContent = text;
        listElement.prepend(li);
        if (listElement.children.length > 15) {
            listElement.removeChild(listElement.lastChild);
        }
    }

    function lockGame(state) {
        isLoading = state;
        guessInput.disabled = state;
        guessButton.disabled = state;
        skipButton.disabled = state;
        newSynopsisButton.disabled = state;
    }

    function clearFeedback() {
        if (feedbackFadeoutTimer) clearTimeout(feedbackFadeoutTimer);
        mainFeedbackEl.classList.remove('fade-out-element');
        subFeedbackEl.classList.remove('fade-out-element');
        mainFeedbackEl.textContent = '';
        subFeedbackEl.textContent = '';
        mainFeedbackEl.style.color = '';
    }

    function updateSynopsisHTML(htmlContent) {
        synopsisEl.classList.remove('fade-in-element');
        synopsisEl.style.opacity = 0;
        setTimeout(() => {
            synopsisEl.innerHTML = htmlContent;
            synopsisEl.classList.add('fade-in-element');
        }, 50);
    }
    
    // Funções de Ação
    async function getNewSynopsis() {
        if (isLoading) return;
        lockGame(true);
        clearFeedback();
        mainFeedbackEl.textContent = 'Gerando outra descrição...';

        try {
            const response = await fetch('/api/new_synopsis', { method: 'POST' });
            const data = await response.json();

            clearFeedback();

            if (response.ok) {
                updateSynopsisHTML(data.newSynopsis);

                mainFeedbackEl.textContent = 'Nova descrição gerada!';
                mainFeedbackEl.style.color = '#f1c40f';
                
                const remainingSynopsisChances = Math.max(0, data.chancesLeft - 1);
                subFeedbackEl.textContent = `Descrições restantes: ${remainingSynopsisChances}`;

                feedbackFadeoutTimer = setTimeout(() => {
                    mainFeedbackEl.classList.add('fade-out-element');
                    subFeedbackEl.classList.add('fade-out-element');
                }, 5000);

                if (data.chancesLeft <= 1) {
                    newSynopsisButton.disabled = true;
                }
            } else {
                mainFeedbackEl.textContent = data.error || 'Ocorreu um erro.';
                mainFeedbackEl.style.color = '#e74c3c';
            }
        } catch (error) {
            clearFeedback();
            mainFeedbackEl.textContent = 'Erro de conexão ao pedir nova descrição.';
            mainFeedbackEl.style.color = '#e74c3c';
        }

        lockGame(false);
    }
    
    async function startNewGame() {
        lockGame(true);
        clearFeedback();
        guessInput.value = '';
        synopsisEl.classList.remove('fade-in-element');
        synopsisEl.textContent = 'Gerando uma nova sinopse ruim...';
        synopsisEl.classList.add('loading-text');

        const response = await fetch('/api/new_game');
        const data = await response.json();
        
        if (data.isIAGame && !data.error) {
            newSynopsisButton.classList.remove('hidden');
            newSynopsisButton.disabled = false;
        } else {
            newSynopsisButton.classList.add('hidden');
        }

        synopsisEl.classList.remove('loading-text');

        if (data.error) {
            synopsisEl.innerHTML = data.synopsis; // Usando innerHTML para o caso de erro
            synopsisEl.style.color = '#f1c40f';
            synopsisEl.classList.add('fade-in-element');
            guessInput.disabled = true;
            guessButton.disabled = true;
            skipButton.disabled = false;
            isLoading = false;
        } else {
            updateSynopsisHTML(data.synopsis);
            lockGame(false);
            guessInput.focus();
            if (data.chancesLeft <= 1) {
                newSynopsisButton.disabled = true;
            }
        }
    }

    async function checkGuess() {
        if (isLoading || !guessInput.value) return;
        lockGame(true);
        clearFeedback();

        const response = await fetch('/api/check_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guess: guessInput.value }),
        });
        const data = await response.json();
        
        if (data.chancesLeft <= 1) {
            newSynopsisButton.disabled = true;
        }

        switch (data.result) {
            case "correct":
                mainFeedbackEl.textContent = 'Você acertou! 🎉';
                mainFeedbackEl.style.color = '#2ecc71';
                addToHistory(correctListUl, data.correctAnswer);
                setTimeout(startNewGame, 2000);
                break;
            
            case "close":
                guessInput.classList.add('shake-element');
                mainFeedbackEl.textContent = `Quase lá! Você está perto...`;
                mainFeedbackEl.style.color = '#f1c40f';
                guessInput.value = '';
                lockGame(false);
                guessInput.focus();
                break;

            case "wrong":
                if (!data.outOfChances) {
                    guessInput.classList.add('shake-element');
                    mainFeedbackEl.textContent = `Errado! Tente novamente.`;
                    subFeedbackEl.textContent = `(${data.chancesLeft} chances restantes)`;
                    mainFeedbackEl.style.color = '#e74c3c';
                    guessInput.value = '';
                    lockGame(false);
                    guessInput.focus();
                } else {
                    mainFeedbackEl.textContent = `Acabaram as chances! O filme era: ${data.correctAnswer}`;
                    mainFeedbackEl.style.color = '#e74c3c';
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

    // Event Listeners
    guessButton.addEventListener('click', checkGuess);
    guessInput.addEventListener('keyup', (event) => { if (event.key === 'Enter') checkGuess(); });
    skipButton.addEventListener('click', skipQuestion);
    newSynopsisButton.addEventListener('click', getNewSynopsis);

    // <<< MUDANÇA: Event listeners para o modal >>>
    openHelpModalButton.addEventListener('click', openModal);
    closeHelpModalButton.addEventListener('click', closeModal);
    // Fecha o modal se o usuário clicar no fundo escuro
    helpModal.addEventListener('click', (event) => {
        if (event.target === helpModal) {
            closeModal();
        }
    });


    // Iniciar o jogo
    startNewGame();
});