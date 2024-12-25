# llama_engine.py
from typing import Dict, Any, List, Optional
from datetime import datetime
import groq
import os

class LlamaEngine:
    def __init__(self):
        self.client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3-8b-8192"
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language query using Llama model
        Returns intent and extracted parameters
        """
        prompt = self._create_prompt(query)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        return self._parse_response(response.choices[0].message.content)
    
    def _create_prompt(self, query: str) -> str:
        return f"""
        Extract appointment related information from the following query:
        Query: {query}
        
        Return a JSON with:
        - intent: booking/rescheduling/canceling
        - doctor_name: extracted doctor name
        - date: extracted date
        - time: extracted time
        - patient_name: extracted patient name (if available)
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        # Parse JSON response and return structured data
        try:
            import json
            return json.loads(response)
        except:
            return {
                "intent": None,
                "doctor_name": None,
                "date": None,
                "time": None,
                "patient_name": None
            }

# calendar_manager.py
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class CalendarManager:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
        
    def _authenticate(self):
        """Handle Google Calendar authentication"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
                
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    async def check_availability(self, doctor_id: str, date: datetime, 
                               duration: int = 30) -> bool:
        """Check if timeslot is available for doctor"""
        time_min = date.isoformat() + 'Z'
        time_max = (date + timedelta(minutes=duration)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId=doctor_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True
        ).execute()
        
        return len(events_result.get('items', [])) == 0
    
    async def create_appointment(self, doctor_id: str, patient_name: str,
                               date: datetime, duration: int = 30) -> Dict[str, Any]:
        """Create calendar appointment"""
        event = {
            'summary': f'Appointment with {patient_name}',
            'start': {
                'dateTime': date.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (date + timedelta(minutes=duration)).isoformat(),
                'timeZone': 'UTC',
            }
        }
        
        return self.service.events().insert(
            calendarId=doctor_id,
            body=event
        ).execute()
    
    async def update_appointment(self, doctor_id: str, event_id: str,
                               new_date: datetime, duration: int = 30) -> Dict[str, Any]:
        """Update existing calendar appointment"""
        event = self.service.events().get(
            calendarId=doctor_id,
            eventId=event_id
        ).execute()
        
        event['start'] = {
            'dateTime': new_date.isoformat(),
            'timeZone': 'UTC',
        }
        event['end'] = {
            'dateTime': (new_date + timedelta(minutes=duration)).isoformat(),
            'timeZone': 'UTC',
        }
        
        return self.service.events().update(
            calendarId=doctor_id,
            eventId=event_id,
            body=event
        ).execute()
    
    async def cancel_appointment(self, doctor_id: str, event_id: str) -> None:
        """Cancel calendar appointment"""
        self.service.events().delete(
            calendarId=doctor_id,
            eventId=event_id
        ).execute()

# appointment_manager.py
from datetime import datetime
from typing import Dict, Any, Optional

class AppointmentManager:
    def __init__(self, llama_engine: LlamaEngine, calendar_manager: CalendarManager):
        self.llama = llama_engine
        self.calendar = calendar_manager
        
    async def process_appointment_request(self, query: str) -> Dict[str, Any]:
        """Process appointment request and take appropriate action"""
        # Extract intent and parameters from query
        parsed_query = await self.llama.process_query(query)
        
        if not parsed_query['intent']:
            return {
                'success': False,
                'message': 'Could not understand the request'
            }
            
        try:
            if parsed_query['intent'] == 'booking':
                return await self._handle_booking(parsed_query)
            elif parsed_query['intent'] == 'rescheduling':
                return await self._handle_rescheduling(parsed_query)
            elif parsed_query['intent'] == 'canceling':
                return await self._handle_canceling(parsed_query)
            else:
                return {
                    'success': False,
                    'message': 'Invalid intent'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _handle_booking(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new appointment booking"""
        date = datetime.fromisoformat(parsed_query['date'])
        
        # Check availability
        is_available = await self.calendar.check_availability(
            parsed_query['doctor_name'],
            date
        )
        
        if not is_available:
            return {
                'success': False,
                'message': 'Selected time slot is not available'
            }
            
        # Create appointment
        appointment = await self.calendar.create_appointment(
            parsed_query['doctor_name'],
            parsed_query['patient_name'],
            date
        )
        
        return {
            'success': True,
            'message': 'Appointment booked successfully',
            'appointment': appointment
        }
    
    async def _handle_rescheduling(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment rescheduling"""
        new_date = datetime.fromisoformat(parsed_query['date'])
        
        # Check availability for new time
        is_available = await self.calendar.check_availability(
            parsed_query['doctor_name'],
            new_date
        )
        
        if not is_available:
            return {
                'success': False,
                'message': 'New time slot is not available'
            }
            
        # Update appointment
        appointment = await self.calendar.update_appointment(
            parsed_query['doctor_name'],
            parsed_query.get('appointment_id'),
            new_date
        )
        
        return {
            'success': True,
            'message': 'Appointment rescheduled successfully',
            'appointment': appointment
        }
    
    async def _handle_canceling(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment cancellation"""
        await self.calendar.cancel_appointment(
            parsed_query['doctor_name'],
            parsed_query.get('appointment_id')
        )
        
        return {
            'success': True,
            'message': 'Appointment canceled successfully'
        }
