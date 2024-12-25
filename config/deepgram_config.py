
# deepgram_config.py
class DeepgramConfig:
    # API Configuration
    API_KEY = os.getenv("DEEPGRAM_API_KEY")
    API_URL = "https://api.deepgram.com/v1"
    
    # Speech-to-Text Configuration
    STT_CONFIG = {
        'punctuate': True,
        'model': 'general',
        'language': 'en-US',
        'tier': 'enhanced',
        'filler_words': False,
        'profanity_filter': True,
        'redact': None,
        'diarize': False,
        'multi_channel': False,
        'alternatives': 1
    }
    
    # Text-to-Speech Configuration
    TTS_CONFIG = {
        'voice': os.getenv("DEEPGRAM_VOICE", "female-1"),
        'speed': float(os.getenv("DEEPGRAM_SPEED", "1.0")),
        'pitch': float(os.getenv("DEEPGRAM_PITCH", "1.0")),
        'sample_rate': int(os.getenv("DEEPGRAM_SAMPLE_RATE", "24000"))
    }
    
    # Audio Processing
    AUDIO_CONFIG = {
        'format': 'wav',
        'channels': 1,
        'sample_rate': 16000,
        'bit_depth': 16
    }
    
    # Streaming Configuration
    STREAMING_CONFIG = {
        'interim_results': True,
        'endpointing': True,
        'vad_turnoff': 500,  # milliseconds
        'max_duration': 305  # seconds (5 minutes + 5 seconds buffer)
    }
    
    # Language Detection
    LANGUAGE_DETECTION_CONFIG = {
        'detect_language': True,
        'model': 'general'
    }
    
    # Error Handling
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    TIMEOUT = 30     # seconds
    
    @classmethod
    def get_stt_config(cls, **kwargs) -> Dict[str, Any]:
        """Get STT configuration with optional overrides"""
        config = cls.STT_CONFIG.copy()
        config.update(kwargs)
        return config
    
    @classmethod
    def get_tts_config(cls, **kwargs) -> Dict[str, Any]:
        """Get TTS configuration with optional overrides"""
        config = cls.TTS_CONFIG.copy()
        config.update(kwargs)
        return config
    
    @classmethod
    def get_streaming_config(cls, **kwargs) -> Dict[str, Any]:
        """Get streaming configuration with optional overrides"""
        config = cls.STREAMING_CONFIG.copy()
        config.update(kwargs)
        return config
