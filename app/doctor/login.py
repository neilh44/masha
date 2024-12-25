from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import jwt
from dataclasses import dataclass

@dataclass
class Doctor:
    id: str
    name: str
    email: str
    specialty: str
    calendar_id: str
    available_hours: Dict[str, list]

class DoctorAuth:
    def __init__(self, db_connection):
        self.db = db_connection
        self.SECRET_KEY = os.getenv('JWT_SECRET_KEY')
        self.GOOGLE_SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
    async def login_doctor(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate doctor and return JWT token"""
        try:
            # Verify doctor credentials from database
            doctor = await self._verify_credentials(email, password)
            if not doctor:
                return {
                    'success': False,
                    'message': 'Invalid credentials'
                }
            
            # Generate JWT token
            token = self._generate_token(doctor)
            
            return {
                'success': True,
                'token': token,
                'doctor': doctor
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def google_oauth_login(self) -> Dict[str, Any]:
        """Handle Google OAuth login flow"""
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.GOOGLE_SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.GOOGLE_SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            # Get doctor info from Google profile
            doctor = await self._get_google_profile(creds)
            
            # Generate JWT token
            token = self._generate_token(doctor)
            
            return {
                'success': True,
                'token': token,
                'doctor': doctor
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return doctor info"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=['HS256'])
            doctor = await self._get_doctor_by_id(payload['doctor_id'])
            return doctor if doctor else None
        except:
            return None
    
    def _generate_token(self, doctor: Doctor) -> str:
        """Generate JWT token for doctor"""
        payload = {
            'doctor_id': doctor.id,
            'email': doctor.email,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm='HS256')
    
    async def _verify_credentials(self, email: str, password: str) -> Optional[Doctor]:
        """Verify doctor credentials against database"""
        # Implementation would depend on your database schema
        # This is a placeholder
        query = "SELECT * FROM doctors WHERE email = %s"
        result = await self.db.fetch_one(query, (email,))
        if result and self._verify_password(password, result['password_hash']):
            return Doctor(**result)
        return None
    
    async def _get_google_profile(self, creds: Credentials) -> Doctor:
        """Get doctor profile from Google"""
        # Implementation would involve calling Google's userinfo API
        # This is a placeholder
        pass
    
    async def _get_doctor_by_id(self, doctor_id: str) -> Optional[Doctor]:
        """Get doctor info from database"""
        query = "SELECT * FROM doctors WHERE id = %s"
        result = await self.db.fetch_one(query, (doctor_id,))
        return Doctor(**result) if result else None
