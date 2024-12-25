from typing import Dict, Any, Optional
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    LiveOptions,
    LiveTranscriptionEvents
)
import os
import json
from datetime import datetime

class STTService:
    def __init__(self):
        api_key = os.getenv('DEEPGRAM_API_KEY')
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
            
        self.deepgram_client = DeepgramClient(api_key)
        self.default_config = {
            'punctuate': True,
            'model': 'general',
            'language': 'en-US',
            'tier': 'enhanced',
            'filler_words': False
        }
    
    async def transcribe_audio(self, audio_data: bytes, 
                             config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transcribe audio data to text using Deepgram
        
        Args:
            audio_data: Raw audio data in bytes (WAV format)
            config: Optional configuration to override defaults
            
        Returns:
            Dictionary containing transcription results or error information
        """
        try:
            # Merge custom config with defaults
            transcription_config = {**self.default_config, **(config or {})}
            
            # Validate audio data
            if not self._validate_audio_data(audio_data):
                return {
                    'success': False,
                    'message': 'Invalid audio data format'
                }
            
            # Create options for transcription
            options = PrerecordedOptions(
                model=transcription_config['model'],
                smart_format=transcription_config['punctuate'],
                language=transcription_config['language'],
                tier=transcription_config['tier'],
                filler_words=transcription_config['filler_words']
            )
            
            # Process transcription
            response = await self.deepgram_client.transcribe_file(
                audio_data,
                mimetype='audio/wav',
                options=options
            )
            
            # Extract transcript from response
            if response and response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    return {
                        'success': True,
                        'transcript': channel.alternatives[0].transcript,
                        'confidence': channel.alternatives[0].confidence,
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            return {
                'success': False,
                'message': 'No transcription results'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Transcription failed: {str(e)}'
            }
    
    async def start_realtime_transcription(self, callback) -> Dict[str, Any]:
        """
        Initialize real-time transcription session
        
        Args:
            callback: Async function to handle transcription results
            
        Returns:
            Dictionary containing streaming client or error information
        """
        try:
            # Configure real-time settings
            options = LiveOptions(
                model=self.default_config['model'],
                smart_format=self.default_config['punctuate'],
                language=self.default_config['language'],
                tier=self.default_config['tier'],
                interim_results=True,
                endpointing=True
            )
            
            # Initialize streaming
            connection = await self.deepgram_client.listen.live.v1(options)
            
            # Set up event handlers
            @connection.on(LiveTranscriptionEvents.TRANSCRIPT)
            async def handle_transcript(transcript):
                if transcript.is_final:
                    await callback({
                        'transcript': transcript.channel.alternatives[0].transcript,
                        'confidence': transcript.channel.alternatives[0].confidence,
                        'words': transcript.channel.alternatives[0].words
                    })
            
            return {
                'success': True,
                'streaming_client': connection
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to start real-time transcription: {str(e)}'
            }
    
    def _validate_audio_data(self, audio_data: bytes) -> bool:
        """
        Validate audio data format and quality
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            bool: True if audio data appears valid, False otherwise
        """
        try:
            # Basic WAV format validation
            if len(audio_data) < 44:  # Minimum WAV header size
                return False
            
            if audio_data[:4] != b'RIFF':
                return False
                
            if audio_data[8:12] != b'WAVE':
                return False
            
            return True
        except:
            return False