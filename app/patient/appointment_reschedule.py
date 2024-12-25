# appointment_booking.py
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class Patient:
    id: str
    name: str
    email: str
    phone: str
    date_of_birth: datetime

class AppointmentBooking:
    def __init__(self, calendar_manager, db_connection):
        self.calendar_manager = calendar_manager
        self.db = db_connection
        
    async def find_available_slots(self, doctor_id: str, 
                                 start_date: datetime,
                                 end_date: datetime) -> Dict[str, Any]:
        """Find available appointment slots for a doctor"""
        try:
            # Get doctor's working hours
            working_hours = await self._get_doctor_working_hours(doctor_id)
            
            # Get existing appointments
            booked_slots = await self.calendar_manager.get_events(
                doctor_id,
                start_date,
                end_date
            )
            
            # Generate available slots
            available_slots = self._generate_available_slots(
                working_hours,
                booked_slots,
                start_date,
                end_date
            )
            
            return {
                'success': True,
                'slots': available_slots
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def book_appointment(self, patient_id: str, doctor_id: str,
                             slot_time: datetime) -> Dict[str, Any]:
        """Book an appointment for a patient"""
        try:
            # Verify slot is still available
            is_available = await self.calendar_manager.check_availability(
                doctor_id,
                slot_time
            )
            
            if not is_available:
                return {
                    'success': False,
                    'message': 'Selected time slot is no longer available'
                }
            
            # Get patient details
            patient = await self._get_patient_details(patient_id)
            
            # Create calendar event
            event = {
                'summary': f'Appointment with {patient.name}',
                'description': f'Patient: {patient.name}\nPhone: {patient.phone}',
                'start': {
                    'dateTime': slot_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (slot_time + timedelta(minutes=30)).isoformat(),
                    'timeZone': 'UTC',
                }
            }
            
            appointment = await self.calendar_manager.create_event(doctor_id, event)
            
            # Save appointment to database
            await self._save_appointment_to_db(
                patient_id,
                doctor_id,
                appointment['id'],
                slot_time
            )
            
            return {
                'success': True,
                'message': 'Appointment booked successfully',
                'appointment': appointment
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _get_doctor_working_hours(self, doctor_id: str) -> Dict[str, Dict[str, str]]:
        """Get doctor's working hours from database"""
        query = "SELECT working_hours FROM doctors WHERE id = %s"
        result = await self.db.fetch_one(query, (doctor_id,))
        return result['working_hours']
    
    async def _get_patient_details(self, patient_id: str) -> Patient:
        """Get patient details from database"""
        query = "SELECT * FROM patients WHERE id = %s"
        result = await self.db.fetch_one(query, (patient_id,))
        return Patient(**result)
    
    async def _save_appointment_to_db(self, patient_id: str, doctor_id: str,
                                    event_id: str, slot_time: datetime) -> None:
        """Save appointment details to database"""
        query = """
            INSERT INTO appointments (patient_id, doctor_id, event_id, slot_time)
            VALUES (%s, %s, %s, %s)
        """
        await self.db.execute(query, (patient_id, doctor_id, event_id, slot_time))
    
    def _generate_available_slots(self, working_hours: Dict[str, Dict[str, str]],
                                booked_slots: List[Dict[str, Any]],
                                start_date: datetime,
                                end_date: datetime) -> List[datetime]:
        """Generate list of available time slots"""
        available_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_name = current_date.strftime('%A').lower()
            if day_name in working_hours:
                day_hours = working_hours[day_name]
                start_time = datetime.strptime(day_hours['start'], '%H:%M').time()
                end_time = datetime.strptime(day_hours['end'], '%H:%M').time()
                
                slot_time = datetime.combine(current_date.date(), start_time)
                while slot_time.time() <= end_time:
                    if not self._is_slot_booked(slot_time, booked_slots):
                        available_slots.append(slot_time)
                    slot_time += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def _is_slot_booked(self, slot_time: datetime,
                        booked_slots: List[Dict[str, Any]]) -> bool:
        """Check if a time slot is already booked"""
        slot_end = slot_time + timedelta(minutes=30)
        for event in booked_slots:
            event_start = datetime.fromisoformat(event['start']['dateTime'].rstrip('Z'))
            event_end = datetime.fromisoformat(event['end']['dateTime'].rstrip('Z'))
            
            if (slot_time >= event_start and slot_time < event_end) or \
               (slot_end > event_start and slot_end <= event_end):
                return True
        return False

# appointment_reschedule.py
class AppointmentReschedule:
    def __init__(self, calendar_manager, db_connection):
        self.calendar_manager = calendar_manager
        self.db = db_connection
        
    async def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Get appointment details"""
        try:
            query = """
                SELECT a.*, p.name as patient_name, d.name as doctor_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.id = %s
            """
            appointment = await self.db.fetch_one(query, (appointment_id,))
            
            if not appointment:
                return {
                    'success': False,
                    'message': 'Appointment not found'
                }
            
            return {
                'success': True,
                'appointment': appointment
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def reschedule_appointment(self, appointment_id: str,
                                   new_slot_time: datetime) -> Dict[str, Any]:
        """Reschedule an existing appointment"""
        try:
            # Get appointment details
            appointment = await self.get_appointment(appointment_id)
            if not appointment['success']:
                return appointment
            
            # Verify new slot is available
            is_available = await self.calendar_manager.check_availability(
                appointment['appointment']['doctor_id'],
                new_slot_time
            )
            
            if not is_available:
                return {
                    'success': False,
                    'message': 'Selected time slot is not available'
                }
            
            # Update calendar event
            event = await self.calendar_manager.update_event(
                appointment['appointment']['doctor_id'],
                appointment['appointment']['event_id'],
                new_slot_time,
                new_slot_time + timedelta(minutes=30)
            )
            
            # Update database
            await self._update_appointment_in_db(appointment_id, new_slot_time)
            
            return {
                'success': True,
                'message': 'Appointment rescheduled successfully',
                'appointment': event
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _update_appointment_in_db(self, appointment_id: str,
                                      new_slot_time: datetime) -> None:
        """Update appointment time in database"""
        query = """
            UPDATE appointments
            SET slot_time = %s
            WHERE id = %s
        """
        await self.db.execute(query, (new_slot_time, appointment_id))
