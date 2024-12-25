from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Appointment:
    id: str
    doctor_id: str
    patient_name: str
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None

class DoctorCalendarView:
    def __init__(self, calendar_manager):
        self.calendar_manager = calendar_manager
    
    async def get_daily_schedule(self, doctor_id: str, date: datetime) -> Dict[str, Any]:
        """Get doctor's schedule for a specific day"""
        try:
            start = date.replace(hour=0, minute=0, second=0)
            end = date.replace(hour=23, minute=59, second=59)
            
            appointments = await self.calendar_manager.get_events(
                doctor_id,
                start,
                end
            )
            
            return {
                'success': True,
                'schedule': self._format_schedule(appointments)
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def get_weekly_schedule(self, doctor_id: str, start_date: datetime) -> Dict[str, Any]:
        """Get doctor's schedule for a week"""
        try:
            end_date = start_date + timedelta(days=7)
            
            appointments = await self.calendar_manager.get_events(
                doctor_id,
                start_date,
                end_date
            )
            
            return {
                'success': True,
                'schedule': self._format_schedule(appointments)
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def get_appointment_details(self, doctor_id: str, appointment_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific appointment"""
        try:
            appointment = await self.calendar_manager.get_event(
                doctor_id,
                appointment_id
            )
            
            return {
                'success': True,
                'appointment': self._format_appointment(appointment)
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def _format_schedule(self, appointments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format appointments for display"""
        formatted = []
        for appt in appointments:
            formatted.append({
                'id': appt['id'],
                'patient_name': appt['summary'].replace('Appointment with ', ''),
                'start_time': appt['start']['dateTime'],
                'end_time': appt['end']['dateTime'],
                'status': appt.get('status', 'confirmed')
            })
        return formatted
    
    def _format_appointment(self, appointment: Dict[str, Any]) -> Dict[str, Any]:
        """Format single appointment details"""
        return {
            'id': appointment['id'],
            'patient_name': appointment['summary'].replace('Appointment with ', ''),
            'start_time': appointment['start']['dateTime'],
            'end_time': appointment['end']['dateTime'],
            'status': appointment.get('status', 'confirmed'),
            'notes': appointment.get('description', '')
        }
