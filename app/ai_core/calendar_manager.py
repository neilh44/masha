from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz

class CalendarManager:
    """
    A comprehensive calendar management class using Google Calendar API with service account authentication.
    """
    
    def __init__(self, service_account_file: str = 'service-account.json'):
        """
        Initialize the calendar manager with service account credentials.
        
        Args:
            service_account_file: Path to the service account JSON file
        """
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.service = self._authenticate(service_account_file)
        
    def _authenticate(self, service_account_file: str):
        """
        Authenticate using service account credentials.
        
        Args:
            service_account_file: Path to the service account JSON file
            
        Returns:
            Google Calendar API service
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=self.SCOPES
            )
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

    async def check_availability(
        self,
        calendar_id: str,
        start_time: datetime,
        duration_minutes: int = 30
    ) -> bool:
        """
        Check if a time slot is available in the calendar.
        
        Args:
            calendar_id: ID of the calendar to check
            start_time: Start time of the slot to check
            duration_minutes: Duration of the appointment in minutes
            
        Returns:
            bool: True if the slot is available, False otherwise
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Ensure times are in UTC
            if start_time.tzinfo is None:
                start_time = pytz.UTC.localize(start_time)
            if end_time.tzinfo is None:
                end_time = pytz.UTC.localize(end_time)
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True
            ).execute()
            
            return len(events_result.get('items', [])) == 0
        except Exception as e:
            raise Exception(f"Error checking availability: {str(e)}")

    async def create_appointment(
        self,
        calendar_id: str,
        summary: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 30,
        attendees: Optional[List[str]] = None,
        send_notifications: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new calendar appointment.
        
        Args:
            calendar_id: ID of the calendar
            summary: Title of the appointment
            description: Detailed description of the appointment
            start_time: Start time of the appointment
            duration_minutes: Duration in minutes
            attendees: List of attendee email addresses
            send_notifications: Whether to send email notifications
            
        Returns:
            Dict containing the created event details
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Ensure times are in UTC
            if start_time.tzinfo is None:
                start_time = pytz.UTC.localize(start_time)
            if end_time.tzinfo is None:
                end_time = pytz.UTC.localize(end_time)
            
            event_data = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]
            
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_data,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            return event
        except Exception as e:
            raise Exception(f"Error creating appointment: {str(e)}")

    async def update_appointment(
        self,
        calendar_id: str,
        event_id: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        attendees: Optional[List[str]] = None,
        send_notifications: bool = True
    ) -> Dict[str, Any]:
        """
        Update an existing calendar appointment.
        
        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to update
            summary: New title of the appointment (optional)
            description: New description (optional)
            start_time: New start time (optional)
            duration_minutes: New duration in minutes (optional)
            attendees: New list of attendee emails (optional)
            send_notifications: Whether to send email notifications
            
        Returns:
            Dict containing the updated event details
        """
        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            
            if start_time:
                if start_time.tzinfo is None:
                    start_time = pytz.UTC.localize(start_time)
                event['start']['dateTime'] = start_time.isoformat()
                
                end_time = start_time + timedelta(minutes=duration_minutes or 30)
                if end_time.tzinfo is None:
                    end_time = pytz.UTC.localize(end_time)
                event['end']['dateTime'] = end_time.isoformat()
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            return updated_event
        except Exception as e:
            raise Exception(f"Error updating appointment: {str(e)}")

    async def cancel_appointment(
        self,
        calendar_id: str,
        event_id: str,
        send_notifications: bool = True
    ) -> None:
        """
        Cancel/delete a calendar appointment.
        
        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to cancel
            send_notifications: Whether to send cancellation notifications
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
        except Exception as e:
            raise Exception(f"Error canceling appointment: {str(e)}")

    async def get_calendar_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all accessible calendars.
        
        Returns:
            List of calendar details
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except Exception as e:
            raise Exception(f"Error getting calendar list: {str(e)}")

    async def get_upcoming_appointments(
        self,
        calendar_id: str,
        days: int = 7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming appointments for the specified calendar.
        
        Args:
            calendar_id: ID of the calendar to check
            days: Number of days to look ahead
            max_results: Maximum number of events to return
            
        Returns:
            List of upcoming appointments
        """
        try:
            now = datetime.utcnow()
            time_max = now + timedelta(days=days)
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            raise Exception(f"Error getting upcoming appointments: {str(e)}")

# Example usage
if __name__ == '__main__':
    # Initialize the calendar manager
    calendar = CalendarManager('service-account.json')
    
    # Test the connection by listing calendars
    import asyncio
    
    async def test_calendar():
        calendars = await calendar.get_calendar_list()
        print("Accessible Calendars:")
        for cal in calendars:
            print(f"- {cal['summary']} ({cal['id']})")
    
    asyncio.run(test_calendar())