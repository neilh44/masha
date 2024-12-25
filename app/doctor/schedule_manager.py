# schedule_manager.py
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz

class DoctorScheduleManager:
    def __init__(self, calendar_manager, db_connection):
        self.calendar_manager = calendar_manager
        self.db = db_connection
    
    async def set_availability(self, doctor_id: str, 
                             availability: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
        """Set doctor's available time slots"""
        try:
            # Update availability in database
            await self._update_doctor_availability(doctor_id, availability)
            
            # Create availability blocks in calendar
            await self._create_calendar_blocks(doctor_id, availability)
            
            return {
                'success': True,
                'message': 'Availability updated successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def get_availability(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor's current availability settings"""
        try:
            query = "SELECT available_hours FROM doctors WHERE id = %s"
            result = await self.db.fetch_one(query, (doctor_id,))
            
            return {
                'success': True,
                'availability': result['available_hours']
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def block_time_slot(self, doctor_id: str, start_time: datetime,
                            end_time: datetime, reason: str) -> Dict[str, Any]:
        """Block specific time slot as unavailable"""
        try:
            event = {
                'summary': 'Blocked Time',
                'description': reason,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'transparency': 'opaque'  # Shows as busy
            }
            
            await self.calendar_manager.create_event(doctor_id, event)
            
            return {
                'success': True,
                'message': 'Time slot blocked successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def set_working_hours(self, doctor_id: str, 
                              working_hours: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Set doctor's regular working hours"""
        try:
            # Update working hours in database
            query = """
                UPDATE doctors 
                SET working_hours = %s 
                WHERE id = %s
            """
            await self.db.execute(query, (working_hours, doctor_id))
            
            return {
                'success': True,
                'message': 'Working hours updated successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _update_doctor_availability(self, doctor_id: str,
                                        availability: Dict[str, List[Dict[str, str]]]) -> None:
        """Update doctor's availability in database"""
        query = """
            UPDATE doctors 
            SET available_hours = %s 
            WHERE id = %s
        """
        await self.db.execute(query, (availability, doctor_id))
    
    async def _create_calendar_blocks(self, doctor_id: str,
                                    availability: Dict[str, List[Dict[str, str]]]) -> None:
        """Create availability blocks in Google Calendar"""
        # Clear existing availability blocks
        await self._clear_availability_blocks(doctor_id)
        
        # Create new availability blocks
        for day, slots in availability.items():
            for slot in slots:
                start_time = datetime.strptime(f"{day} {slot['start']}", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{day} {slot['end']}", "%Y-%m-%d %H:%M")
                
                event = {
                    'summary': 'Available for Appointments',
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'transparency': 'transparent'  # Shows as free
                }
                
                await self.calendar_manager.create_event(doctor_id, event)
    
    async def _clear_availability_blocks(self, doctor_id: str) -> None:
        """Clear existing availability blocks from calendar"""
        events = await self.calendar_manager.get_events(
            doctor_id,
            datetime.now(pytz.UTC),
            datetime.now(pytz.UTC) + timedelta(days=30)
        )
        
        for event in events:
            if event['summary'] == 'Available for Appointments':
                await self.calendar_manager.delete_event(doctor_id, event['id'])