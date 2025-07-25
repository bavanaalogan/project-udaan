import httpx
import asyncio
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import langcodes

load_dotenv()

class TranslationServices:
    def __init__(self):
        self.mymemory_api_key = os.getenv("MYMEMORY_API_KEY")
        self.mymemory_base_url = os.getenv("MYMEMORY_BASE_URL", "https://api.mymemory.translated.net")
        self.libretranslate_base_url = os.getenv("LIBRETRANSLATE_BASE_URL", "https://libretranslate.de")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.enable_mock_fallback = os.getenv("ENABLE_MOCK_FALLBACK", "true").lower() == "true"
        
        # Comprehensive mock dictionary with Indian languages for fallback
        self.mock_translations = {
            # Basic greetings
            "hello": {
                "hi": "नमस्ते",           # Hindi
                "ta": "வணக்கம்",          # Tamil
                "te": "హలో",             # Telugu
                "kn": "ಹಲೋ",             # Kannada
                "ml": "ഹലോ",             # Malayalam
                "bn": "হ্যালো",           # Bengali
                "gu": "હેલો",             # Gujarati
                "mr": "नमस्कार",          # Marathi
                "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ",      # Punjabi
                "or": "ନମସ୍କାର",         # Odia
                "as": "নমস্কাৰ"           # Assamese
            },
            "good morning": {
                "hi": "सुप्रभात",
                "ta": "காலை வணக்கம்",
                "te": "శుభోదయం",
                "kn": "ಶುಭೋದಯ",
                "ml": "സുപ്രഭാതം",
                "bn": "সুপ্রভাত",
                "gu": "શુભ સવાર",
                "mr": "शुभ प्रभात",
                "pa": "ਸ਼ੁਭ ਸਵੇਰ",
                "or": "ଶୁଭ ପ୍ରଭାତ",
                "as": "শুভ প্ৰভাত"
            },
            "good evening": {
                "hi": "शुभ संध्या",
                "ta": "மாலை வணக்கம்",
                "te": "శుభ సాయంత్రం",
                "kn": "ಶುಭ ಸಾಯಂಕಾಲ",
                "ml": "സന്ധ്യാശുഭാശയങ്ങൾ",
                "bn": "শুভ সন্ধ্যা",
                "gu": "શુભ સાંજ",
                "mr": "शुभ संध्या",
                "pa": "ਸ਼ੁਭ ਸ਼ਾਮ",
                "or": "ଶୁଭ ସନ୍ଧ୍ୟା",
                "as": "শুভ সন্ধিয়া"
            },
            "good night": {
                "hi": "शुभ रात्रि",
                "ta": "இனிய இரவு",
                "te": "శుభ రాత్రి",
                "kn": "ಶುಭ ರಾತ್ರಿ",
                "ml": "ശുഭ രാത്രി",
                "bn": "শুভ রাত্রি",
                "gu": "શુભ રાત્રી",
                "mr": "शुभ रात्री",
                "pa": "ਸ਼ੁਭ ਰਾਤ",
                "or": "ଶୁଭ ରାତ୍ରି",
                "as": "শুভ ৰাতি"
            },
            "thank you": {
                "hi": "धन्यवाद",
                "ta": "நன்றி",
                "te": "ధన్యవాదాలు",
                "kn": "ಧನ್ಯವಾದಗಳು",
                "ml": "നന്ദി",
                "bn": "ধন্যবাদ",
                "gu": "આભાર",
                "mr": "धन्यवाद",
                "pa": "ਧੰਨਵਾਦ",
                "or": "ଧନ୍ୟବାଦ",
                "as": "ধন্যবাদ"
            },
            "goodbye": {
                "hi": "अलविदा",
                "ta": "விடை",
                "te": "వీడ్కోలు",
                "kn": "ವಿದಾಯ",
                "ml": "വിട",
                "bn": "বিদায়",
                "gu": "આવજો",
                "mr": "निरोप",
                "pa": "ਅਲਵਿਦਾ",
                "or": "ବିଦାୟ",
                "as": "বিদায়"
            },
            "please": {
                "hi": "कृपया",
                "ta": "தயவுசெய்து",
                "te": "దయచేసి",
                "kn": "ದಯವಿಟ್ಟು",
                "ml": "ദയവായി",
                "bn": "দয়া করে",
                "gu": "કૃપા કરીને",
                "mr": "कृपया",
                "pa": "ਕਿਰਪਾ ਕਰਕੇ",
                "or": "ଦୟାକରି",
                "as": "অনুগ্ৰহ কৰি"
            },
            "yes": {
                "hi": "हाँ",
                "ta": "ஆம்",
                "te": "అవును",
                "kn": "ಹೌದು",
                "ml": "അതെ",
                "bn": "হ্যাঁ",
                "gu": "હા",
                "mr": "होय",
                "pa": "ਹਾਂ",
                "or": "ହଁ",
                "as": "হয়"
            },
            "no": {
                "hi": "नहीं",
                "ta": "இல்லை",
                "te": "లేదు",
                "kn": "ಇಲ್ಲ",
                "ml": "ഇല്ല",
                "bn": "না",
                "gu": "ના",
                "mr": "नाही",
                "pa": "ਨਹੀਂ",
                "or": "ନାହିଁ",
                "as": "নাই"
            },
            "welcome": {
                "hi": "स्वागत है",
                "ta": "வரவேற்கிறோம்",
                "te": "స్వాగతం",
                "kn": "ಸ್ವಾಗತ",
                "ml": "സ്വാഗതം",
                "bn": "স্বাগতম",
                "gu": "સ્વાગત છે",
                "mr": "स्वागत आहे",
                "pa": "ਜੀ ਆਇਆਂ ਨੂੰ",
                "or": "ସ୍ୱାଗତ",
                "as": "স্বাগতম"
            },
            
            # Numbers (1-10)
            "one": {
                "hi": "एक", "ta": "ஒன்று", "te": "ఒకటి", "kn": "ಒಂದು", "ml": "ഒന്ന്",
                "bn": "এক", "gu": "એક", "mr": "एक", "pa": "ਇੱਕ", "or": "ଏକ", "as": "এক"
            },
            "two": {
                "hi": "दो", "ta": "இரண்டு", "te": "రెండు", "kn": "ಎರಡು", "ml": "രണ്ട്",
                "bn": "দুই", "gu": "બે", "mr": "दोन", "pa": "ਦੋ", "or": "ଦୁଇ", "as": "দুই"
            },
            "three": {
                "hi": "तीन", "ta": "மூன்று", "te": "మూడు", "kn": "ಮೂರು", "ml": "മൂന്ന്",
                "bn": "তিন", "gu": "ત્રણ", "mr": "तीन", "pa": "ਤਿੰਨ", "or": "ତିନି", "as": "তিনি"
            },
            "four": {
                "hi": "चार", "ta": "நான்கு", "te": "నాలుగు", "kn": "ನಾಲ್ಕು", "ml": "നാല്",
                "bn": "চার", "gu": "ચાર", "mr": "चार", "pa": "ਚਾਰ", "or": "ଚାରି", "as": "চাৰি"
            },
            "five": {
                "hi": "पांच", "ta": "ஐந்து", "te": "ఐదు", "kn": "ಐದು", "ml": "അഞ്ച്",
                "bn": "পাঁচ", "gu": "પાંચ", "mr": "पाच", "pa": "ਪੰਜ", "or": "ପାଞ୍ଚ", "as": "পাঁচ"
            },
            
            # Family terms
            "mother": {
                "hi": "मां", "ta": "அம்மா", "te": "అమ్మ", "kn": "ಅಮ್ಮ", "ml": "അമ്മ",
                "bn": "মা", "gu": "મા", "mr": "आई", "pa": "ਮਾਂ", "or": "ମା", "as": "মা"
            },
            "father": {
                "hi": "पिता", "ta": "அப்பா", "te": "నాన్న", "kn": "ಅಪ್ಪ", "ml": "അച്ഛൻ",
                "bn": "বাবা", "gu": "પપ્પા", "mr": "बाबा", "pa": "ਪਿਤਾ", "or": "ବାପା", "as": "দেউতা"
            },
            "brother": {
                "hi": "भाई", "ta": "அண்ணா", "te": "అన్న", "kn": "ಅಣ್ಣ", "ml": "ചേട്ടൻ",
                "bn": "ভাই", "gu": "ભાઈ", "mr": "भाऊ", "pa": "ਭਰਾ", "or": "ଭାଇ", "as": "ভাই"
            },
            "sister": {
                "hi": "बहन", "ta": "அக்கா", "te": "అక్క", "kn": "ಅಕ್ಕ", "ml": "ചേച്ചി",
                "bn": "বোন", "gu": "બહેન", "mr": "बहीण", "pa": "ਭੈਣ", "or": "ଭଉଣୀ", "as": "ভনী"
            },
            
            # Common travel/daily terms
            "water": {
                "hi": "पानी", "ta": "தண்ணீர்", "te": "నీళ్లు", "kn": "ನೀರು", "ml": "വെള്ളം",
                "bn": "পানি", "gu": "પાણી", "mr": "पाणी", "pa": "ਪਾਣੀ", "or": "ପାଣି", "as": "পানী"
            },
            "food": {
                "hi": "खाना", "ta": "உணவு", "te": "ఆహారం", "kn": "ಆಹಾರ", "ml": "ഭക്ഷണം",
                "bn": "খাবার", "gu": "ખાણું", "mr": "अन्न", "pa": "ਖਾਣਾ", "or": "ଖାଦ୍ୟ", "as": "খাদ্য"
            },
            "house": {
                "hi": "घर", "ta": "வீடு", "te": "ఇల్లు", "kn": "ಮನೆ", "ml": "വീട്",
                "bn": "ঘর", "gu": "ઘર", "mr": "घर", "pa": "ਘਰ", "or": "ଘର", "as": "ঘৰ"
            },
            "school": {
                "hi": "स्कूल", "ta": "பள்ளி", "te": "పాఠశాల", "kn": "ಶಾಲೆ", "ml": "സ്കൂൾ",
                "bn": "স্কুল", "gu": "શાળા", "mr": "शाळा", "pa": "ਸਕੂਲ", "or": "ସ୍କୁଲ", "as": "বিদ্যালয়"
            },
            "hospital": {
                "hi": "अस्पताल", "ta": "மருத்துவமனை", "te": "ఆసుపత్రి", "kn": "ಆಸ್ಪತ್ರೆ", "ml": "ആശുപത്രി",
                "bn": "হাসপাতাল", "gu": "હોસ્પિટલ", "mr": "रुग्णालय", "pa": "ਹਸਪਤਾਲ", "or": "ହସ୍ପିତାଲ", "as": "চিকিৎসালয়"
            },
            
            # Business/professional terms
            "money": {
                "hi": "पैसा", "ta": "பணம்", "te": "డబ్బు", "kn": "ಹಣ", "ml": "പണം",
                "bn": "টাকা", "gu": "પૈસા", "mr": "पैसा", "pa": "ਪੈਸਾ", "or": "ଟଙ୍କା", "as": "টকা"
            },
            "work": {
                "hi": "काम", "ta": "வேலை", "te": "పని", "kn": "ಕೆಲಸ", "ml": "ജോലി",
                "bn": "কাজ", "gu": "કામ", "mr": "काम", "pa": "ਕੰਮ", "or": "କାମ", "as": "কাম"
            },
            "office": {
                "hi": "कार्यालय", "ta": "அலுவலகம்", "te": "కార్యాలయం", "kn": "ಕಛೇರಿ", "ml": "ഓഫീസ്",
                "bn": "অফিস", "gu": "ઑફિસ", "mr": "कार्यालय", "pa": "ਦਫ਼ਤਰ", "or": "କାର୍ଯ୍ୟାଳୟ", "as": "কাৰ্যালয়"
            },
            "meeting": {
                "hi": "बैठक", "ta": "கூட்டம்", "te": "సభ", "kn": "ಸಭೆ", "ml": "യോഗം",
                "bn": "বৈঠক", "gu": "મીટિંગ", "mr": "सभा", "pa": "ਮੀਟਿੰਗ", "or": "ସଭା", "as": "সভা"
            },
            
            # Emergency/help terms
            "help": {
                "hi": "मदद", "ta": "உதவி", "te": "సహాయం", "kn": "ಸಹಾಯ", "ml": "സഹായം",
                "bn": "সাহায্য", "gu": "મદદ", "mr": "मदत", "pa": "ਮਦਦ", "or": "ସାହାଯ୍ୟ", "as": "সহায়"
            },
            "doctor": {
                "hi": "डॉक्टर", "ta": "டாக்டர்", "te": "వైద్యుడు", "kn": "ವೈದ್ය", "ml": "ഡോക്ടർ",
                "bn": "ডাক্তার", "gu": "ડૉક્ટર", "mr": "डॉक्टर", "pa": "ਡਾਕਟਰ", "or": "ଡାକ୍ତର", "as": "চিকিৎসক"
            },
            "police": {
                "hi": "पुलिस", "ta": "போலீஸ்", "te": "పోలీసు", "kn": "ಪೊಲೀಸ್", "ml": "പോലീസ്",
                "bn": "পুলিশ", "gu": "પોલીસ", "mr": "पोलिस", "pa": "ਪੁਲਿਸ", "or": "ପୋଲିସ", "as": "আৰক্ষী"
            },
            "emergency": {
                "hi": "आपातकाल", "ta": "அவசரம்", "te": "అత్యవసరం", "kn": "ತುರ್ತು", "ml": "അത്യാവശ്യം",
                "bn": "জরুরি", "gu": "કટોકટી", "mr": "आपत्कालीन", "pa": "ਐਮਰਜੈਂਸੀ", "or": "ଜରୁରୀକାଳୀନ", "as": "জৰুৰীকালীন"
            },
            
            # Transportation
            "bus": {
                "hi": "बस", "ta": "பேருந்து", "te": "బస్సు", "kn": "ಬಸ್", "ml": "ബസ്",
                "bn": "বাস", "gu": "બસ", "mr": "बस", "pa": "ਬੱਸ", "or": "ବସ୍", "as": "বাছ"
            },
            "train": {
                "hi": "ट्रेन", "ta": "ரயில்", "te": "రైలు", "kn": "ರೈಲು", "ml": "ട്രെയിൻ",
                "bn": "ট্রেন", "gu": "ટ્રેન", "mr": "ट्रेन", "pa": "ਰੇਲ", "or": "ଟ୍ରେନ୍", "as": "ৰেল"
            },
            "station": {
                "hi": "स्टेशन", "ta": "நிலையம்", "te": "స్టేషన్", "kn": "ನಿಲ್ದಾಣ", "ml": "സ്റ്റേഷൻ",
                "bn": "স্টেশন", "gu": "સ્ટેશન", "mr": "स्थानक", "pa": "ਸਟੇਸ਼ਨ", "or": "ଷ୍ଟେସନ୍", "as": "ষ্টেচন"
            },
            
            # Time expressions
            "today": {
                "hi": "आज", "ta": "இன்று", "te": "ఈరోజు", "kn": "ಇಂದು", "ml": "ഇന്ന്",
                "bn": "আজ", "gu": "આજે", "mr": "आज", "pa": "ਅੱਜ", "or": "ଆଜି", "as": "আজি"
            },
            "tomorrow": {
                "hi": "कल", "ta": "நாளை", "te": "రేపు", "kn": "ನಾಳೆ", "ml": "നാളെ",
                "bn": "কাল", "gu": "કાલે", "mr": "उद्या", "pa": "ਕੱਲ", "or": "କାଲି", "as": "কাইলৈ"
            },
            "yesterday": {
                "hi": "कल", "ta": "நேற்று", "te": "నిన్న", "kn": "ನಿನ್ನೆ", "ml": "ഇന്നലെ",
                "bn": "গতকাল", "gu": "ગઈકાલે", "mr": "काल", "pa": "ਕੱਲ੍ਹ", "or": "ଗତକାଲି", "as": "কালি"
            },
            
            # Common questions/responses
            "how are you": {
                "hi": "आप कैसे हैं", "ta": "நீங்கள் எப்படி இருக்கிறீர்கள்", "te": "మీరు ఎలా ఉన్నారు", 
                "kn": "ನೀವು ಹೇಗಿದ್ದೀರಿ", "ml": "നിങ്ങൾ എങ്ങനെയുണ്ട്", "bn": "আপনি কেমন আছেন",
                "gu": "તમે કેમ છો", "mr": "तुम्ही कसे आहात", "pa": "ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ", 
                "or": "ଆପଣ କେମିତି ଅଛନ୍ତି", "as": "আপুনি কেনেকুৱা আছে"
            },
            "i am fine": {
                "hi": "मैं ठीक हूं", "ta": "நான் நலமாக இருக்கிறேன்", "te": "నేను బాగున్నాను", 
                "kn": "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ", "ml": "ഞാൻ സുഖമായിരിക്കുന്നു", "bn": "আমি ভালো আছি",
                "gu": "હું સારો છું", "mr": "मी बरा आहे", "pa": "ਮੈਂ ਠੀਕ ਹਾਂ", 
                "or": "ମୁଁ ଭଲ ଅଛି", "as": "মই ভাল আছোঁ"
            },
            "what is your name": {
                "hi": "आपका नाम क्या है", "ta": "உங்கள் பெயர் என்ன", "te": "మీ పేరు ఏమిటి", 
                "kn": "ನಿಮ್ಮ ಹೆಸರು ಏನು", "ml": "നിങ്ങളുടെ പേര് എന്താണ്", "bn": "আপনার নাম কি",
                "gu": "તમારું નામ શું છે", "mr": "तुमचे नाव काय आहे", "pa": "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ", 
                "or": "ଆପଣଙ୍କ ନାମ କଣ", "as": "আপোনাৰ নাম কি"
            },
            "sorry": {
                "hi": "माफ करना", "ta": "மன்னிக்கவும்", "te": "క్షమించండి", "kn": "ಕ್ಷಮಿಸಿ", "ml": "ക്ഷമിക്കണം",
                "bn": "দুঃখিত", "gu": "માફ કરશો", "mr": "माफ करा", "pa": "ਮਾਫ ਕਰਨਾ", "or": "କ୍ଷମା କରନ୍ତୁ", "as": "ক্ষমা কৰিব"
            },
            "excuse me": {
                "hi": "माफ करिए", "ta": "மன்னிக்கவும்", "te": "క్షమించండి", "kn": "ಕ್ಷಮಿಸಿ", "ml": "ക്ഷമിക്കണം",
                "bn": "মাফ করবেন", "gu": "માફ કરશો", "mr": "माफ करा", "pa": "ਮਾਫ਼ ਕਰੋ", "or": "କ୍ଷମା କରନ୍ତୁ", "as": "ক্ষমা কৰিব"
            }
        }
    
    def _normalize_language_code(self, lang_code: str) -> str:
        """Normalize language code to ISO 639-1 format"""
        try:
            lang = langcodes.Language.make(language=lang_code)
            return lang.language
        except:
            return lang_code.lower()
    

    def _chunk_text(self, text: str, max_length: int = 450) -> list:
        """Split text into chunks under the character limit"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + ". ") <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Handle cases where even single sentences are too long
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                # Split by character count as last resort
                for i in range(0, len(chunk), max_length):
                    final_chunks.append(chunk[i:i+max_length])
        
        return final_chunks
    
    async def translate_with_mymemory(self, text: str, target_language: str, source_language: str = "auto") -> Optional[Dict[str, Any]]:
        """Translate using MyMemory API (fallback service)"""
        try:
            target_lang = self._normalize_language_code(target_language)
            source_lang = self._normalize_language_code(source_language)

            params = {
                "q": text,
                "langpair": f"{source_lang}|{target_lang}",
            }

            if self.mymemory_api_key:
                params["key"] = self.mymemory_api_key

            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(f"{self.mymemory_base_url}/get", params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("responseStatus") == 200:
                    # Prefer exact segment match with high quality, prioritizing native script
                    input_clean = text.strip().lower()
                    best_match = None
                    native_script_match = None
                    transliterated_match = None
                    
                    def is_native_script(text, target_lang):
                        """Check if text uses native script for the target language"""
                        if target_lang == "ta":  # Tamil
                            return any(ord(char) >= 0x0B80 and ord(char) <= 0x0BFF for char in text)
                        elif target_lang == "hi":  # Hindi
                            return any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in text)
                        elif target_lang == "te":  # Telugu
                            return any(ord(char) >= 0x0C00 and ord(char) <= 0x0C7F for char in text)
                        elif target_lang == "kn":  # Kannada
                            return any(ord(char) >= 0x0C80 and ord(char) <= 0x0CFF for char in text)
                        elif target_lang == "ml":  # Malayalam
                            return any(ord(char) >= 0x0D00 and ord(char) <= 0x0D7F for char in text)
                        elif target_lang == "bn":  # Bengali
                            return any(ord(char) >= 0x0980 and ord(char) <= 0x09FF for char in text)
                        elif target_lang == "gu":  # Gujarati
                            return any(ord(char) >= 0x0A80 and ord(char) <= 0x0AFF for char in text)
                        elif target_lang == "pa":  # Punjabi
                            return any(ord(char) >= 0x0A00 and ord(char) <= 0x0A7F for char in text)
                        return True  # Default to accepting for other languages
                    
                    for match in data.get("matches", []):
                        segment = match.get("segment", "").strip().lower()
                        translation = match.get("translation", "").strip()
                        quality = int(match.get("quality", 0))

                        if segment == input_clean and translation and translation != "Test123" and quality >= 75:
                            match_data = {
                                "translated_text": translation,
                                "confidence": quality
                            }
                            
                            if is_native_script(translation, target_lang):
                                if not native_script_match or quality > native_script_match["confidence"]:
                                    native_script_match = match_data
                            else:
                                if not transliterated_match or quality > transliterated_match["confidence"]:
                                    transliterated_match = match_data
                    
                    # Prioritize native script, then transliterated, then responseData
                    if native_script_match:
                        best_match = native_script_match
                    elif transliterated_match:
                        best_match = transliterated_match
                    else:
                        # Fall back to responseData if no good match found
                        response_text = data["responseData"].get("translatedText", "")
                        # MyMemory returns match as decimal (0.85) but we need percentage (85)
                        raw_match = data["responseData"].get("match", 0)
                        confidence_score = int(float(raw_match) * 100) if raw_match else 75
                        
                        if response_text and is_native_script(response_text, target_lang):
                            best_match = {
                                "translated_text": response_text,
                                "confidence": confidence_score
                            }
                        else:
                            best_match = {
                                "translated_text": response_text,
                                "confidence": confidence_score
                            }

                    return {
                        "translated_text": best_match["translated_text"],
                        "source_language": source_lang,
                        "target_language": target_lang,
                        "service": "mymemory",
                        "confidence": best_match["confidence"],
                        "original_text": text
                    }

        except Exception as e:
            print(f"⚠️ MyMemory translation failed: {e}")
            return None

    
    async def translate_with_libretranslate(self, text: str, target_language: str, source_language: str = "auto") -> Optional[Dict[str, Any]]:
        """Translate using LibreTranslate free API (primary service) - LIMITED LANGUAGE SUPPORT"""
        try:
            target_lang = self._normalize_language_code(target_language)
            
            # LibreTranslate has limited language support - check if target language is supported
            # Common supported languages in most public instances
            supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'ar', 'zh', 'hi']
            
            if target_lang not in supported_languages:
                print(f"⚠️ LibreTranslate doesn't support target language: {target_lang}")
                return None
            
            # LibreTranslate doesn't support "auto", so detect or default to English
            if source_language == "auto":
                source_lang = "en"  # Default to English for auto-detection
            else:
                source_lang = self._normalize_language_code(source_language)
            
            if source_lang not in supported_languages:
                print(f"⚠️ LibreTranslate doesn't support source language: {source_lang}")
                return None
            
            # Validate that we have different source and target languages
            if source_lang == target_lang:
                return {
                    "translated_text": text,  # Return original text if same language
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "service": "libretranslate",
                    "confidence": 100,
                    "original_text": text
                }
            
            payload = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text"
            }
            
            async with httpx.AsyncClient(timeout=self.request_timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.libretranslate_base_url}/translate", 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "translatedText" in data and data["translatedText"].strip():
                    return {
                        "translated_text": data["translatedText"],
                        "source_language": data.get("detectedLanguage", {}).get("language", source_lang) if isinstance(data.get("detectedLanguage"), dict) else source_lang,
                        "target_language": target_lang,
                        "service": "libretranslate",
                        "confidence": 80,  # Higher confidence for LibreTranslate
                        "original_text": text
                    }
                else:
                    print(f"⚠️ LibreTranslate returned empty translation for: {text}")
                    return None
                    
        except httpx.HTTPStatusError as e:
            print(f"⚠️ LibreTranslate HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.TimeoutException:
            print(f"⚠️ LibreTranslate timeout after {self.request_timeout}s")
            return None
        except Exception as e:
            print(f"⚠️ LibreTranslate translation failed: {e}")
            return None
    
    async def translate_with_mock(self, text: str, target_language: str) -> Optional[Dict[str, Any]]:
        """Mock translation using Indian language dictionary (final fallback)"""
        if not self.enable_mock_fallback:
            return None
            
        try:
            normalized_text = text.lower().strip()
            target_lang = self._normalize_language_code(target_language)
            
            if normalized_text in self.mock_translations:
                if target_lang in self.mock_translations[normalized_text]:
                    translated_text = self.mock_translations[normalized_text][target_lang]
                    
                    return {
                        "translated_text": translated_text,
                        "source_language": "auto",
                        "target_language": target_lang,
                        "service": "mock_indian",
                        "confidence": 60,
                        "original_text": text
                    }
        except Exception as e:
            print(f"⚠️ Mock translation failed: {e}")
            
        return None
    
    async def _translate_single_chunk(self, text: str, target_language: str, source_language: str = "auto") -> Dict[str, Any]:
        """Translate a single chunk of text, handling chunking if needed"""
        # Check if text needs chunking
        if len(text) > 450:
            chunks = self._chunk_text(text)
            translated_chunks = []
            
            for chunk in chunks:
                result = await self.translate(chunk, source_language, target_language)
                if result.get("error"):
                    return result  # Return error if any chunk fails
                translated_chunks.append(result["translated_text"])
            
            return {
                "translated_text": " ".join(translated_chunks),
                "source_language": source_language,
                "target_language": target_language,
                "service": "chunked",
                "confidence": 75,
                "original_text": text
            }
        else:
            return await self.translate(text, source_language, target_language)
    
    async def translate_batch(self, texts: list, target_language: str, source_language: str = "auto") -> list:
        """Translate multiple texts in parallel for maximum speed"""
        max_workers = int(os.getenv("PARALLEL_WORKERS", 10))
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def translate_single(text: str):
            async with semaphore:
                return await self.translate(text, source_language, target_language)
        
        # Execute translations in parallel
        tasks = [translate_single(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        return results

    async def translate(self, text: str, source_language: str, target_language: str) -> 'TranslationResponse':
        # Try MyMemory first (primary service) - Better language support including Tamil
        try:
            result = await self.translate_with_mymemory(text, target_language, source_language)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ MyMemory (primary) failed: {e}")
        
        # Try LibreTranslate as fallback (limited language support)
        try:
            result = await self.translate_with_libretranslate(text, target_language, source_language)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ LibreTranslate (fallback) failed: {e}")
        
        # Try mock dictionary as final fallback
        try:
            result = await self.translate_with_mock(text, target_language)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Mock dictionary (final fallback) failed: {e}")
        
        # If all services fail, return error response
        return {
            "translated_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "service": "none",
            "confidence": 0,
            "original_text": text,
            "error": "All translation services failed"
        }


# Global translation service instance
translation_service = TranslationServices()
