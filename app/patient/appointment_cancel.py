
# appointment_cancel.py
from typing import Dict, Any

class AppointmentCancel:
    def __init__(self, calendar_manager, db_connection):
        self.calendar_manager = calendar_manager
        self.db = db_connection
    
    async def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an existing appointment"""
        try:
            # Get appointment details
            query = """
                SELECT * FROM appointments
                WHERE id = %s
            """
            appointment = await self.db.fetch_one(query, (appointment_id,))
            
            if not appointment:
                return {
                    'success': False,
                    'message': 'Appointment not found'
                }
            
            # Delete calendar event
            await self.calendar_manager.delete_event(
                appointment['doctor_id'],
                appointment['event_id']
            )
            
            # Update database
            await self._update_appointment_status(appointment_id, 'cancelled')
            
            return {
                'success': True,
                'message': 'Appointment cancelled successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def get_cancellation_policy(self, doctor_id: str) -> Dict[str, Any]:
        """Get doctor's cancellation policy"""
        try:
            query = "SELECT cancellation_policy FROM doctors WHERE id = %s"
            result = await self.db.fetch_one(query, (doctor_id,))
            
            return {
                'success': True,
                'policy': result['cancellation_policy']
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    async def _update_appointment_status(self, appointment_id: str,
                                       status: str) -> None:
        """Update appointment status in database"""
        query = """
            UPDATE appointments
            SET status = %s
            WHERE id = %s
        """
        await self.db.execute(query, (status, appointment_id))
    
    async def get_cancellation_history(self, patient_id: str) -> Dict[str, Any]:
        """Get patient's appointment cancellation history"""
        try:
            query = """
                SELECT a.*, d.name as doctor_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = %s AND a.status = 'cancelled'
                ORDER BY a.slot_time DESC
            """
            history = await self.db.fetch_all(query, (patient_id,))
            
            return {
                'success': True,
                'history': history
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }