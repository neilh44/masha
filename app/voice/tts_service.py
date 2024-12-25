# tts_service.py
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    LiveOptions,
    LiveTranscriptionEvents
)

class TTSService:
    def __init__(self):
        api_key = os.getenv('DEEPGRAM_API_KEY')
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
            
        self.deepgram_client = DeepgramClient(api_key)  # Updated client initialization
        self.default_config = {
            'voice': 'female-1',
            'speed': 1.0,
            'pitch': 1.0,
            'sample_rate': 24000
        }
            
    async def synthesize_speech(self, text: str, 
                              config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert text to speech using Deepgram
        """
        try:
            # Merge custom config with defaults
            tts_config = {**self.default_config, **(config or {})}
            
            # Validate input text
            if not text or not isinstance(text, str):
                return {
                    'success': False,
                    'message': 'Invalid input text'
                }
            
            # Process text-to-speech
            tts_request = {
                'text': text,
                **tts_config
            }
            
            response = await self.deepgram_client.text_to_speech(tts_request)
            
            if response and response.get('audio'):
                return {
                    'success': True,
                    'audio_data': response['audio'],
                    'duration': response.get('duration'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'success': False,
                'message': 'No audio generated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Speech synthesis failed: {str(e)}'
            }
    
    async def synthesize_batch(self, texts: List[str]) -> Dict[str, Any]:
        """
        Process multiple text-to-speech conversions in batch
        """
        try:
            results = []
            for text in texts:
                result = await self.synthesize_speech(text)
                results.append(result)
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            return {
                'success': True,
                'successful_conversions': successful,
                'failed_conversions': failed,
                'total_processed': len(results),
                'success_rate': len(successful) / len(results) if results else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Batch processing failed: {str(e)}'
            }
    
    def _optimize_audio_output(self, audio_data: bytes) -> bytes:
        """
        Optimize audio output for better quality and smaller size
        """
        # Implementation for audio optimization
        # This would involve audio processing logic
        return audio_data

