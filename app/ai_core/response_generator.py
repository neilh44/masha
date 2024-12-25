from typing import Dict, Any

class ResponseGenerator:
    def __init__(self):
        self.response_templates = {
            'booking_success': "Your appointment with {doctor} has been scheduled for {date} at {time}.",
            'booking_failure': "Sorry, I couldn't book your appointment. {reason}",
            'rescheduling_success': "Your appointment with {doctor} has been rescheduled to {date} at {time}.",
            'rescheduling_failure': "Sorry, I couldn't reschedule your appointment. {reason}",
            'cancellation_success': "Your appointment with {doctor} for {date} at {time} has been canceled.",
            'cancellation_failure': "Sorry, I couldn't cancel your appointment. {reason}",
            'error': "I apologize, but there was an error processing your request: {error_message}"
        }
    
    def generate_response(self, result: Dict[str, Any]) -> str:
        """Generate natural language response based on operation result"""
        try:
            if not result['success']:
                return self._generate_error_response(result)
                
            intent = result.get('intent', '')
            if 'booking' in intent:
                template = self.response_templates['booking_success']
            elif 'rescheduling' in intent:
                template = self.response_templates['rescheduling_success']
            elif 'canceling' in intent:
                template = self.response_templates['cancellation_success']
            else:
                return self.response_templates['error'].format(
                    error_message="Unknown operation type"
                )
                
            return template.format(**self._extract_response_params(result))
            
        except Exception as e:
            return self.response_templates['error'].format(
                error_message=str(e)
            )
    
    def _generate_error_response(self, result: Dict[str, Any]) -> str:
        """Generate error response"""
        intent = result.get('intent', '')
        if 'booking' in intent:
            template = self.response_templates['booking_failure']
        elif 'rescheduling' in intent:
            template = self.response_templates['rescheduling_failure']
        elif 'canceling' in intent:
            template = self.response_templates['cancellation_failure']
        else:
            template = self.response_templates['error']
            
        return template.format(
            reason=result.get('message', 'Unknown error'),
            error_message=result.get('message', 'Unknown error')
        )
    
    def _extract_response_params(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for response template"""
        appointment = result.get('appointment', {})
        return {
            'doctor': appointment.get('doctor', 'Unknown'),
            'date': appointment.get('date', 'Unknown'),
            'time': appointment.get('time', 'Unknown')
        }
