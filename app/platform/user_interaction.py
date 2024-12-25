# user_interaction.py
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import json

class UserInteraction:
    def __init__(self, ai_engine, voice_handler, response_generator):
        self.ai_engine = ai_engine
        self.voice_handler = voice_handler
        self.response_generator = response_generator
        self.session_data = {}
    
    async def process_user_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input and generate appropriate response"""
        try:
            # If input is voice, convert to text
            if input_data.get('type') == 'voice':
                text = await self.voice_handler.convert_speech_to_text(
                    input_data['audio_data']
                )
            else:
                text = input_data.get('text', '')
            
            if not text:
                return {
                    'success': False,
                    'message': 'No input text provided'
                }
            
            # Process with AI engine
            ai_response = await self.ai_engine.process_query(text)
            
            # Generate response
            response = self.response_generator.generate_response(ai_response)
            
            # Convert response to speech if needed
            if input_data.get('type') == 'voice':
                audio_response = await self.voice_handler.convert_text_to_speech(response)
                return {
                    'success': True,
                    'text_response': response,
                    'audio_response': audio_response
                }
            
            return {
                'success': True,
                'text_response': response
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def handle_conversation_context(self, user_id: str, 
                                        context_data: Dict[str, Any]) -> None:
        """Maintain conversation context for better responses"""
        self.session_data[user_id] = {
            'context': context_data,
            'last_updated': datetime.utcnow()
        }
    
    async def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation context for a user"""
        session = self.session_data.get(user_id)
        if session:
            return session['context']
        return None
    
    def _clean_expired_sessions(self) -> None:
        """Clean up expired session data"""
        current_time = datetime.utcnow()
        expired_users = []
        
        for user_id, session in self.session_data.items():
            if (current_time - session['last_updated']).hours >= 1:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.session_data[user_id]

