class JarvisUI {
    constructor() {
        this.isListening = false;
        this.isVoiceEnabled = true;
        this.dataset = null;
        this.recognition = null;
        this.initializeElements();
        this.bindEvents();
        this.setupAudioVisualizer();
        this.loadDataset();
    }

    async loadDataset() {
        try {
            const response = await fetch('jarvis_data.json');
            this.dataset = await response.json();
            console.log('Dataset loaded successfully');
        } catch (error) {
            console.error('Error loading dataset:', error);
            this.dataset = {};
        }
    }

    initializeElements() {
        this.elements = {
            avatar: document.getElementById('avatar'),
            statusText: document.getElementById('statusText'),
            statusIndicator: document.getElementById('statusIndicator'),
            chatMessages: document.getElementById('chatMessages'),
            chatInput: document.getElementById('chatInput'),
            sendBtn: document.getElementById('sendBtn'),
            micBtn: document.getElementById('micBtn'),
            voiceToggle: document.getElementById('voiceToggle'),
            settingsBtn: document.getElementById('settingsBtn'),
            settingsModal: document.getElementById('settingsModal'),
            modalClose: document.getElementById('modalClose'),
            listeningIndicator: document.getElementById('listeningIndicator'),
            voiceEnabled: document.getElementById('voiceEnabled'),
            voiceRate: document.getElementById('voiceRate'),
            voiceRateValue: document.getElementById('voiceRateValue'),
            themeSelect: document.getElementById('themeSelect'),
            audioVisualizer: document.getElementById('audioVisualizer')
        };
    }

    bindEvents() {
        if (this.elements.sendBtn) {
            this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.elements.chatInput) {
            this.elements.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }

        if (this.elements.micBtn) {
            this.elements.micBtn.addEventListener('click', () => this.toggleListening());
        }

        if (this.elements.voiceToggle) {
            this.elements.voiceToggle.addEventListener('click', () => this.toggleVoice());
        }

        if (this.elements.settingsBtn) {
            this.elements.settingsBtn.addEventListener('click', () => this.openSettings());
        }

        if (this.elements.modalClose) {
            this.elements.modalClose.addEventListener('click', () => this.closeSettings());
        }

        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const command = e.currentTarget.dataset.command;
                this.processCommand(command);
            });
        });

        window.addEventListener('click', (e) => {
            if (this.elements.settingsModal && e.target === this.elements.settingsModal) {
                this.closeSettings();
            }
        });
    }

    async sendMessage() {
        const message = this.elements.chatInput?.value?.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        if (this.elements.chatInput) {
            this.elements.chatInput.value = '';
        }

        try {
            this.setStatus('Processing...');
            const response = await this.processCommand(message);
            this.addMessage(response, 'bot');
            this.setStatus('Ready to assist');
        } catch (error) {
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            this.setStatus('Error occurred');
        }
    }

    async processCommand(userInput) {
        if (!this.dataset) {
            return "I'm still loading my knowledge base. Please try again in a moment.";
        }

        const input = userInput.toLowerCase().trim();
        
        // Handle Quick Actions
        if (input.includes('time') || input.includes('what time is it')) {
            return this.getCurrentTime();
        }
        
        if (input.includes('news') || input.includes('latest news')) {
            return await this.getLatestNews();
        }
        
        if (input.includes('calculator') || input.includes('math')) {
            return this.openCalculator();
        }
        
        if (input.includes('joke') || input.includes('tell me a joke')) {
            return this.getRandomJoke();
        }
        
        // Handle math calculations
        if (this.isMathExpression(userInput)) {
            return this.calculateMath(userInput);
        }
        
        // Handle dataset conversations
        for (const categoryData of Object.values(this.dataset)) {
            if (categoryData.conversations) {
                for (const conv of categoryData.conversations) {
                    if (conv.user && conv.user.toLowerCase().trim() === input) {
                        return conv.bot || "I understand, but I don't have a specific response for that.";
                    }
                }
            }
        }

        const fuzzyResponse = this.findFuzzyMatch(input);
        if (fuzzyResponse) {
            return fuzzyResponse;
        }

        return this.getGenericResponse(input);
    }

    isMathExpression(input) {
        // Check if input contains math operators
        const mathPattern = /^[\d\s+\-*/().]+$/;
        return mathPattern.test(input.trim()) && /[+\-*/]/.test(input);
    }

    getCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        const dateString = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        return `The current time is ${timeString} on ${dateString}.`;
    }

    async getLatestNews() {
        try {
            // Simulated news - in real implementation, fetch from news API
            const newsItems = [
                "Latest technology breakthrough: AI systems now achieve 99% accuracy in medical diagnosis.",
                "Space exploration: New Mars rover discovers evidence of ancient water systems.",
                "Climate update: Global renewable energy capacity increased by 50% this year.",
                "Science news: Scientists successfully create artificial photosynthesis system.",
                "Tech industry: Major breakthrough in quantum computing announced by leading research lab."
            ];
            const randomNews = newsItems[Math.floor(Math.random() * newsItems.length)];
            return `Here are the latest news headlines: ${randomNews}`;
        } catch (error) {
            return "I'm unable to fetch news at the moment. Please try again later.";
        }
    }

    openCalculator() {
        return "I can help you with calculations! Just type your math expression like '2 + 2' or 'sqrt(16)' and I'll calculate it for you.";
    }

    getRandomJoke() {
        const jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't some couples go to the gym? Because some relationships don't work out!",
            "What do you call a pile of cats? A meow-ntain!"
        ];
        return jokes[Math.floor(Math.random() * jokes.length)];
    }

    // Enhanced math calculation
    calculateMath(expression) {
        try {
            // Basic safety check for math expressions
            const sanitized = expression.replace(/[^0-9+\-*/().\s]/g, '');
            if (sanitized !== expression) {
                return "Please use only numbers and basic math operators (+, -, *, /, parentheses).";
            }
            
            // Use Function constructor for safe evaluation
            const result = Function(`"use strict"; return (${sanitized})`)();
            return `The result is: ${result}`;
        } catch (error) {
            return "I couldn't calculate that. Please check your math expression.";
        }
    }

    findFuzzyMatch(userInput) {
        let bestMatch = null;
        let bestScore = 0;

        for (const categoryData of Object.values(this.dataset)) {
            if (categoryData.conversations) {
                for (const conv of categoryData.conversations) {
                    if (conv.user) {
                        const score = this.calculateSimilarity(userInput, conv.user.toLowerCase());
                        if (score > bestScore && score > 0.3) {
                            bestScore = score;
                            bestMatch = conv.bot;
                        }
                    }
                }
            }
        }

        return bestMatch;
    }

    calculateSimilarity(str1, str2) {
        const set1 = new Set(str1.split(' '));
        const set2 = new Set(str2.split(' '));
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        return intersection.size / union.size;
    }

    getGenericResponse(input) {
        const responses = [
            "That's an interesting question. Let me think about it.",
            "I understand you're asking about that. Could you tell me more?",
            "That's a thoughtful question. What would you like to know specifically?",
            "I see what you're getting at. Let me process that.",
            "Interesting perspective. Tell me more about what you're thinking."
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }

    addMessage(text, type) {
        if (!this.elements.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <p>${text}</p>
                <span class="message-time">${time}</span>
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    toggleListening() {
        if (!this.checkSpeechRecognitionSupport()) {
            this.addMessage('Speech recognition requires HTTPS or localhost. Please type your messages instead.', 'bot');
            return;
        }

        this.isListening = !this.isListening;
        
        if (this.isListening) {
            this.startSpeechRecognition();
        } else {
            this.stopSpeechRecognition();
        }
    }

    checkSpeechRecognitionSupport() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }

    startSpeechRecognition() {
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            if (this.elements.micBtn) {
                this.elements.micBtn.classList.add('active');
            }
            if (this.elements.listeningIndicator) {
                this.elements.listeningIndicator.classList.add('active');
            }
            this.setStatus('Listening...');

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                if (this.elements.chatInput) {
                    this.elements.chatInput.value = transcript;
                }
                this.sendMessage();
                this.stopSpeechRecognition();
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                let errorMessage = 'Speech recognition error: ';
                
                switch(event.error) {
                    case 'not-allowed':
                        errorMessage += 'Microphone access denied. Please allow microphone access and try again.';
                        break;
                    case 'no-speech':
                        errorMessage += 'No speech detected. Please try again.';
                        break;
                    case 'audio-capture':
                        errorMessage += 'Audio capture failed. Please check your microphone.';
                        break;
                    case 'network':
                        errorMessage += 'Network error. Please check your connection.';
                        break;
                    default:
                        errorMessage += event.error;
                }
                
                this.addMessage(errorMessage, 'bot');
                this.stopSpeechRecognition();
            };

            this.recognition.onend = () => {
                this.stopSpeechRecognition();
            };

            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.addMessage('Error starting speech recognition. Please type your message instead.', 'bot');
            this.stopSpeechRecognition();
        }
    }

    stopSpeechRecognition() {
        if (this.recognition) {
            this.recognition.stop();
            this.recognition = null;
        }
        
        this.isListening = false;
        
        if (this.elements.micBtn) {
            this.elements.micBtn.classList.remove('active');
        }
        if (this.elements.listeningIndicator) {
            this.elements.listeningIndicator.classList.remove('active');
        }
        this.setStatus('Ready to assist');
    }

    toggleVoice() {
        this.isVoiceEnabled = !this.isVoiceEnabled;
        if (this.elements.voiceEnabled) {
            this.elements.voiceEnabled.checked = this.isVoiceEnabled;
        }
        
        const voiceToggle = document.getElementById('voiceToggle');
        if (voiceToggle) {
            const icon = voiceToggle.querySelector('i');
            if (icon) {
                icon.className = this.isVoiceEnabled ? 'fas fa-microphone' : 'fas fa-microphone-slash';
            }
        }
        
        this.addMessage(`Voice ${this.isVoiceEnabled ? 'enabled' : 'disabled'}`, 'bot');
    }

    setStatus(text) {
        if (this.elements.statusText) {
            this.elements.statusText.textContent = text;
        }
    }

    openSettings() {
        if (this.elements.settingsModal) {
            this.elements.settingsModal.classList.add('active');
        }
    }

    closeSettings() {
        if (this.elements.settingsModal) {
            this.elements.settingsModal.classList.remove('active');
        }
    }

    updateVoiceRate(e) {
        if (this.elements.voiceRateValue) {
            this.elements.voiceRateValue.textContent = e.target.value;
        }
    }

    changeTheme(e) {
        const theme = e.target.value;
        document.body.setAttribute('data-theme', theme);
        this.addMessage(`Theme changed to ${theme}`, 'bot');
    }

    setupAudioVisualizer() {
        const canvas = this.elements.audioVisualizer;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        let time = 0;
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
            gradient.addColorStop(0, 'rgba(0, 212, 255, 0.02)');
            gradient.addColorStop(0.5, 'rgba(255, 0, 110, 0.02)');
            gradient.addColorStop(1, 'rgba(121, 40, 202, 0.02)');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            for (let i = 0; i < 50; i++) {
                const x = Math.sin(time + i * 0.1) * 100 + canvas.width / 2;
                const y = Math.cos(time + i * 0.1) * 100 + canvas.height / 2;
                const size = Math.sin(time + i) * 2 + 3;
                
                ctx.beginPath();
                ctx.arc(x, y, size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 212, 255, ${Math.sin(time + i) * 0.5 + 0.5})`;
                ctx.fill();
            }
            
            time += 0.01;
            requestAnimationFrame(animate);
        };
        
        animate();
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.toggleListening();
            }
            if (e.ctrlKey && e.key === 'k') {
                if (this.elements.chatInput) {
                    this.elements.chatInput.focus();
                }
            }
        });
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    const jarvisUI = new JarvisUI();
    jarvisUI.setupKeyboardShortcuts();
    
    setTimeout(() => {
        if (jarvisUI.elements.avatar) {
            jarvisUI.elements.avatar.classList.add('loaded');
        }
    }, 500);
});
