# voice_input_handler.py
from deepgram import DeepgramClient, DeepgramClientOptions
from typing import Dict, Any, Optional
import base64
import os
import json

class VoiceInputHandler:
    def __init__(self):
        api_key = os.getenv('DEEPGRAM_API_KEY')
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
            
        # Configure Deepgram client with options
        config = DeepgramClientOptions(options={"keepalive": "true"})
        self.deepgram_client = DeepgramClient(api_key, config)
                                              
    async def convert_speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech audio to text using Deepgram"""
        try:
            response = await self.deepgram_client.transcription.prerecorded(
                {'buffer': audio_data, 'mimetype': 'audio/wav'},
                self.voice_config
            )
            
            if response and response.get('results'):
                return response['results']['channels'][0]['alternatives'][0]['transcript']
            
            return ''
        
        except Exception as e:
            raise Exception(f"Speech to text conversion failed: {str(e)}")
    
    async def convert_text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using Deepgram"""
        try:
            # Configure TTS parameters
            tts_config = {
                'text': text,
                'voice': 'female-1',  # or any other available voice
                'speed': 1.0,
                'pitch': 1.0
            }
            
            # Call Deepgram TTS API
            response = await self.deepgram_client.text_to_speech(tts_config)
            
            return response['audio']
        
        except Exception as e:
            raise Exception(f"Text to speech conversion failed: {str(e)}")
    
    async def handle_streaming_audio(self, audio_stream) -> Dict[str, Any]:
        """Handle streaming audio input"""
        try:
            # Configure streaming parameters
            streaming_config = {
                **self.voice_config,
                'interim_results': True
            }
            
            # Initialize streaming client
            streaming = await self.deepgram_client.transcription.live(streaming_config)
            
            # Set up event handlers
            async def handle_message(self, message):
                transcript = json.loads(message)
                if transcript.get('is_final'):
                    return transcript['channel']['alternatives'][0]['transcript']
            
            streaming.addListener('transcriptReceived', handle_message)
            
            # Process audio stream
            while True:
                chunk = await audio_stream.read(8000)
                if not chunk:
                    break
                streaming.send(chunk)
            
            await streaming.finish()
            
            return {
                'success': True,
                'message': 'Streaming audio processed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Streaming audio processing failed: {str(e)}"
            }
    
    def _validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate audio format and quality"""
        try:
            # Check audio file header
            if audio_data[:4] != b'RIFF':
                return False
            
            # Check audio format (WAV)
            if audio_data[8:12] != b'WAVE':
                return False
            
            # Additional format checks can be added here
            
            return True
        except:
            return False
    
    async def detect_language(self, audio_data: bytes) -> str:
        """Detect spoken language in audio"""
        try:
            # Configure language detection
            lang_config = {
                'detect_language': True,
                'model': 'general'
            }
            
            response = await self.deepgram_client.transcription.prerecorded(
                {'buffer': audio_data, 'mimetype': 'audio/wav'},
                lang_config
            )
            
            if response and response.get('results'):
                return response['results']['channels'][0]['detected_language']
            
            return 'en'  # Default to English if detection fails
            
        except Exception as e:
            raise Exception(f"Language detection failed: {str(e)}")
    
    async def enhance_audio(self, audio_data: bytes) -> bytes:
        """Enhance audio quality if needed"""
        try:
            # Configure audio enhancement
            enhance_config = {
                'enhance': True,
                'remove_background': True
            }
            
            response = await self.deepgram_client.audio.enhance(
                {'buffer': audio_data, 'mimetype': 'audio/wav'},
                enhance_config
            )
            
            return response['audio']
            
        except Exception as e:
            raise Exception(f"Audio enhancement failed: {str(e)}")
