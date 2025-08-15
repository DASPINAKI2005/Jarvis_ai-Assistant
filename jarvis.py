import json
import random
import datetime
import speech_recognition as sr
import pyttsx3
from difflib import get_close_matches
import logging
import os
import re
import webbrowser
import subprocess
import threading
from typing import Dict, Any, Optional, List, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Jarvis:
    """Advanced Jarvis AI Assistant with multi-modal capabilities"""
    
    def __init__(self, config_file: str = "jarvis_data.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.dataset = self._load_dataset()
        self.engine = None
        self.recognizer = None
        self.commands = self._initialize_commands()
        self.running = False
        self.voice_thread = None
        
        # Initialize components
        self._initialize_speech()
        self._initialize_voice_commands()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with intelligent defaults"""
        default_config = {
            "language": "en",
            "voice_enabled": True,
            "data_file": "jarvis_data.json",
            "hotword": "jarvis",
            "voice_rate": 150,
            "voice_volume": 1.0,
            "features": {
                "web_search": True,
                "system_control": True,
                "multilingual": True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Deep merge for nested dictionaries
                    for key, value in config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _load_dataset(self) -> Dict[str, Any]:
        """Load dataset directly from JSON file"""
        try:
            data_file = self.config.get("data_file", "jarvis_data.json")
            if not os.path.exists(data_file):
                logger.error(f"Data file {data_file} not found")
                return {}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return data
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return {}
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return empty fallback data - no longer used"""
        return {}
    
    def _initialize_speech(self) -> None:
        """Initialize speech engine with robust error handling"""
        try:
            if self.config.get("voice_enabled", True):
                self.engine = pyttsx3.init()
                self.recognizer = sr.Recognizer()
                
                # Configure speech engine properties
                if self.engine:
                    voices = self.engine.getProperty('voices')
                    if voices:
                        # Try to select a natural-sounding voice
                        preferred_voices = [
                            v.id for v in voices 
                            if 'english' in v.id.lower() or 'default' in v.id.lower()
                        ]
                        if preferred_voices:
                            self.engine.setProperty('voice', preferred_voices[0])
                    
                    self.engine.setProperty('rate', self.config.get("voice_rate", 150))
                    self.engine.setProperty('volume', self.config.get("voice_volume", 1.0))
                
                logger.info("Speech engine initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize speech engine: {e}")
            self.config["voice_enabled"] = False
    
    def _initialize_voice_commands(self) -> None:
        """Initialize voice command recognition system"""
        try:
            if self.config.get("voice_enabled", True):
                self.recognizer = sr.Recognizer()
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                logger.info("Voice command system ready")
        except Exception as e:
            logger.error(f"Failed to initialize voice commands: {e}")
    
    def _initialize_commands(self) -> Dict[str, Callable]:
        """Initialize all available commands with metadata"""
        return {
            "help": {
                "function": self._get_help_text,
                "description": "Show help information",
                "keywords": ["help", "assistance", "what can you do"]
            },
            "exit": {
                "function": self._exit_handler,
                "description": "Exit the program",
                "keywords": ["exit", "quit", "goodbye","bye"]
            },
            "voice_toggle": {
                "function": self._toggle_voice,
                "description": "Toggle voice on/off",
                "keywords": ["voice on", "voice off", "toggle voice"]
            },
            "language": {
                "function": self._handle_language_switch,
                "description": "Change language",
                "keywords": ["switch to", "change language", "language"]
            },
            "time": {
                "function": self._get_time_response,
                "description": "Get current time",
                "keywords": ["time", "what time is it", "current time"]
            },
            "search": {
                "function": self._web_search,
                "description": "Search the web",
                "keywords": ["search for", "look up", "find information about"],
                "enabled": self.config["features"]["web_search"]
            },
            "open_app": {
                "function": self._open_application,
                "description": "Open applications",
                "keywords": ["open", "launch", "start application"],
                "enabled": self.config["features"]["system_control"]
            }
        }
    
    def speak(self, text: str, priority: int = 1) -> None:
        """Convert text to speech with priority-based queuing"""
        print(f"Jarvis: {text}")
        if self.config.get("voice_enabled", True) and self.engine:
            try:
                # Simple priority system (1-3, 1 being highest)
                if priority == 1:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    # Lower priority responses can be queued
                    def speak_thread():
                        self.engine.say(text)
                        self.engine.runAndWait()
                    
                    threading.Thread(target=speak_thread).start()
            except Exception as e:
                logger.error(f"Speech synthesis error: {e}")
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """Listen for voice input with adaptive timeout"""
        if not self.config.get("voice_enabled", True) or not self.recognizer:
            return None
            
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info(f"Listening for {timeout} seconds...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
                
                logger.info("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text.lower()
                
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout")
            return None
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def continuous_listen(self) -> None:
        """Continuous listening mode with hotword detection"""
        hotword = self.config.get("hotword", "jarvis").lower()
        pattern = re.compile(rf'\b{hotword}\b', re.IGNORECASE)
        
        while self.running:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    logger.info("Waiting for hotword...")
                    audio = self.recognizer.listen(source, timeout=3)
                    
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        if pattern.search(text):
                            self.speak("Yes? How can I help?", priority=1)
                            command = self.listen(timeout=8)
                            if command:
                                self.process_command(command)
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        logger.error(f"Error in continuous listen: {e}")
                        
            except Exception as e:
                logger.error(f"Error in continuous listening loop: {e}")
                continue
    
    def process_command(self, user_input: str) -> str:
        """Process user input using ML-based similarity matching with JSON data"""
        if not user_input:
            return ""
        
        user_input = user_input.lower().strip()
        
        # First try exact match
        for category_data in self.dataset.values():
            if isinstance(category_data, dict) and "conversations" in category_data:
                conversations = category_data["conversations"]
                for conv in conversations:
                    if conv.get("user", "").lower().strip() == user_input:
                        return conv.get("bot", "")
        
        # If no exact match, use similarity-based matching
        json_response = self._find_similar_response(user_input)
        
        # If no good match found in JSON, search Google
        if not json_response or json_response == "":
            return self._search_google(user_input)
        
        return json_response
    
    def _find_similar_response(self, user_input: str) -> str:
        """Find most similar response using cosine similarity and TF-IDF"""
        import re
        from collections import Counter
        
        # Tokenize and clean input
        input_tokens = re.findall(r'\b\w+\b', user_input.lower())
        
        # Collect all conversations
        all_conversations = []
        for category_data in self.dataset.values():
            if isinstance(category_data, dict) and "conversations" in category_data:
                all_conversations.extend(category_data["conversations"])
        
        if not all_conversations:
            return ""
        
        # Calculate similarity scores
        best_match = None
        best_score = 0
        
        for conv in all_conversations:
            user_text = conv.get("user", "").lower()
            response_text = conv.get("bot", "")
            
            if not user_text or not response_text:
                continue
            
            # Simple word overlap similarity
            conv_tokens = re.findall(r'\b\w+\b', user_text)
            
            # Calculate Jaccard similarity
            input_set = set(input_tokens)
            conv_set = set(conv_tokens)
            
            if not input_set or not conv_set:
                continue
            
            intersection = len(input_set.intersection(conv_set))
            union = len(input_set.union(conv_set))
            
            if union > 0:
                similarity = intersection / union
            else:
                similarity = 0
            
            # Bonus for exact word matches
            exact_matches = sum(1 for word in input_tokens if word in conv_tokens)
            similarity += exact_matches * 0.1
            
            if similarity > best_score:
                best_score = similarity
                best_match = response_text
        
        # Return response if similarity is above threshold
        if best_score > 0.3:  # Adjust threshold as needed
            return best_match
        
        return ""
    
    def _handle_natural_language(self, user_input: str) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _get_category_response(self, category: str) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _get_error_response(self, error_type: str = "general") -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _get_default_response(self) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _get_time_response(self) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _get_fuzzy_response(self, user_input: str) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _exit_handler(self) -> str:
        """Handle exit commands"""
        self.running = False
        if self.voice_thread and self.voice_thread.is_alive():
            self.voice_thread.join(timeout=1)
        return self._get_category_response("farewell")
    
    def _toggle_voice(self, command: str) -> str:
        """Toggle voice on/off based on command"""
        enabled = "on" in command or "enable" in command
        self.config["voice_enabled"] = enabled
        self._save_config()
        
        if enabled:
            self._initialize_speech()
        
        return f"Voice {'enabled' if enabled else 'disabled'}."
    
    def _handle_language_switch(self, command: str) -> str:
        """Handle language switching commands"""
        languages = {
            "english": "en",
            "hindi": "hi",
            "bengali": "bn",
            "spanish": "es",
            "french": "fr"
        }
        
        for lang_name, lang_code in languages.items():
            if lang_name in command:
                if lang_code in self.dataset:
                    self.config["language"] = lang_code
                    self._save_config()
                    return self._get_category_response("greetings")
                else:
                    return f"Sorry, {lang_name} is not available."
        
        return "Please specify a valid language to switch to."
    
    def _web_search(self, query: str) -> str:
        """Perform web search"""
        search_terms = query.replace("search for", "").replace("look up", "").strip()
        if not search_terms:
            return "What would you like me to search for?"
        
        url = f"https://www.google.com/search?q={search_terms.replace(' ', '+')}"
        webbrowser.open(url)
        return f"I've opened a web search for {search_terms}."
    
    def _open_application(self, command: str) -> str:
        """Open system applications"""
        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "browser": "start chrome",
            "terminal": "cmd.exe"
        }
        
        for app_name, app_cmd in apps.items():
            if app_name in command:
                try:
                    subprocess.Popen(app_cmd, shell=True)
                    return f"Opening {app_name}."
                except Exception as e:
                    logger.error(f"Error opening {app_name}: {e}")
                    return f"Failed to open {app_name}."
        
        return "Which application would you like me to open?"

    def _search_google(self, query: str) -> str:
        """Search Google for questions not found in JSON data"""
        try:
            # Clean and format the query
            search_query = query.strip()
            if not search_query:
                return "I couldn't understand your question. Could you please rephrase it?"
            
            # Create Google search URL
            encoded_query = search_query.replace(' ', '+')
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            # Open the search in default browser
            webbrowser.open(search_url)
            
            # Return a helpful response
            return f"I don't have that information in my database, but I've opened a Google search for '{search_query}'. You should find relevant information there!"
            
        except Exception as e:
            logger.error(f"Error during Google search: {e}")
            return "I apologize, but I encountered an issue while trying to search for that information. Please try again later."
    
    def _convert_topic_to_language_structure(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """No longer needed - using direct JSON structure"""
        return {}

    def _get_help_text(self) -> str:
        """No longer needed - responses come only from JSON"""
        return ""
    
    def _save_config(self) -> None:
        """Save configuration with error handling"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def run(self, mode: str = "interactive") -> None:
        """Main execution loop with multiple modes"""
        try:
            self.running = True
            greeting = self._get_category_response("greetings")
            self.speak(greeting, priority=1)
            
            if mode == "interactive":
                self._interactive_mode()
            elif mode == "voice":
                self._voice_mode()
            else:
                logger.error(f"Unknown mode: {mode}")
                self._interactive_mode()
                
        except KeyboardInterrupt:
            self.speak("Shutting down...", priority=1)
        except Exception as e:
            logger.error(f"Fatal error in run: {e}")
            self.speak("I've encountered a serious error. Please restart me.", priority=1)
        finally:
            self.running = False
    
    def _interactive_mode(self) -> None:
        """Text-based interactive mode"""
        while self.running:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit"]:
                    self.speak(self._exit_handler(), priority=1)
                    break
                
                response = self.process_command(user_input)
                self.speak(response, priority=1)
                
            except KeyboardInterrupt:
                self.speak(self._exit_handler(), priority=1)
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                self.speak(self._get_error_response("technical"), priority=1)
    
    def _voice_mode(self) -> None:
        """Voice-activated mode with hotword detection"""
        self.speak("Entering voice mode. Say my name to activate.", priority=1)
        self.voice_thread = threading.Thread(target=self.continuous_listen)
        self.voice_thread.start()
        
        # Keep main thread alive while voice thread runs
        while self.running and self.voice_thread.is_alive():
            try:
                self.voice_thread.join(timeout=0.5)
            except KeyboardInterrupt:
                self.speak(self._exit_handler(), priority=1)
                break

if __name__ == "__main__":
    try:
        assistant = Jarvis()
        
        # Determine run mode
        mode = "interactive"
        if len(os.sys.argv) > 1:
            mode = os.sys.argv[1].lower()
        
        assistant.run(mode=mode)
    except Exception as e:
        logger.error(f"Failed to start Jarvis: {e}")
        print("Failed to start Jarvis. Check jarvis.log for details.")