# main.py
import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
from datetime import datetime
import json
from fastapi import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import AI Core components
from app.ai_core.llama_engine import LlamaEngine
from app.ai_core.calendar_manager import CalendarManager
from app.ai_core.appointment_manager import AppointmentManager
from app.ai_core.response_generator import ResponseGenerator


# Import Doctor components
from app.doctor.login import DoctorAuth
from app.doctor.calendar_view import DoctorCalendarView
from app.doctor.schedule_manager import DoctorScheduleManager

# Import Patient components
from app.patient.appointment_booking import AppointmentBooking
from app.patient.appointment_reschedule import AppointmentReschedule
from app.patient.appointment_cancel import AppointmentCancel

# Import Platform components
from app.platform.user_interaction import UserInteraction
from app.platform.voice_input_handler import VoiceInputHandler

# Import Voice components
from app.voice.stt_service import STTService
from app.voice.tts_service import TTSService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app with your configurations
app = FastAPI(
    title="AI Appointment Management System",
    description="AI-powered system for managing medical appointments",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")

# Add debug logging
logger.info(f"Base Directory: {BASE_DIR}")
logger.info(f"Static Directory: {STATIC_DIR}")
logger.info(f"Index path: {os.path.join(STATIC_DIR, 'index.html')}")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    try:
        return FileResponse(
            index_path,
            media_type='text/html'
        )
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return {"error": str(e)}

@app.get("/test")
async def test():
    return {"message": "API is working"}

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Appointment Management System")
    # Log if index.html exists
    index_path = os.path.join(STATIC_DIR, "index.html")
    logger.info(f"Index.html exists: {os.path.exists(index_path)}")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for active connections
active_connections: Dict[str, WebSocket] = {}

class AppointmentSystem:
    def __init__(self):
        # Initialize database connection (placeholder)
        self.db_connection = None
        
        # Initialize core components
        self.llama_engine = LlamaEngine()
        self.calendar_manager = CalendarManager()
        self.appointment_manager = AppointmentManager(self.llama_engine, self.calendar_manager)
        self.response_generator = ResponseGenerator()
        
        # Initialize doctor components
        self.doctor_auth = DoctorAuth(self.db_connection)
        self.doctor_calendar = DoctorCalendarView(self.calendar_manager)
        self.doctor_schedule = DoctorScheduleManager(self.calendar_manager, self.db_connection)
        
        # Initialize patient components
        self.appointment_booking = AppointmentBooking(self.calendar_manager, self.db_connection)
        self.appointment_reschedule = AppointmentReschedule(self.calendar_manager, self.db_connection)
        self.appointment_cancel = AppointmentCancel(self.calendar_manager, self.db_connection)
        
        # Initialize voice components
        self.stt_service = STTService()
        self.tts_service = TTSService()
        self.voice_handler = VoiceInputHandler()
        
        # Initialize platform components
        self.user_interaction = UserInteraction(
            self.llama_engine,
            self.voice_handler,
            self.response_generator
        )

system = AppointmentSystem()

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    try:
        await websocket.accept()
        active_connections[client_id] = websocket
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id
        })
        
        while True:
            try:
                # Accept both text and json messages
                message = await websocket.receive_text()
                
                # Parse the message
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                    continue
                
                # Process the message
                await handle_websocket_message(websocket, client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        if client_id in active_connections:
            del active_connections[client_id]
        logger.info(f"Connection closed for client {client_id}")


async def handle_websocket_message(websocket: WebSocket, client_id: str, message: str):
    """Handle incoming WebSocket messages"""
    logger.debug(f"Received message from client {client_id}: {message}")
    try:
        data = json.loads(message)
        message_type = data.get('type')
        
        if not message_type:
            await websocket.send_json({
                'type': 'error',
                'message': 'Message type is required'
            })
            return
            
        if message_type == 'transcription':
            response = await system.user_interaction.process_user_input({
                'type': message_type,
                'text': data.get('text', ''),
                'audio_data': data.get('audio', None)
            })
            
            await websocket.send_json({
                'type': 'response',
                'text': response.get('text', ''),
                'audio': response.get('audio', None)
            })
        else:
            await websocket.send_json({
                'type': 'error',
                'message': f'Unsupported message type: {message_type}'
            })
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'message': 'Invalid JSON format'
        })
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'message': 'Error processing request'
        })


# Doctor endpoints
@app.post("/doctor/login")
async def doctor_login(credentials: Dict[str, str]):
    """Doctor login endpoint"""
    response = await system.doctor_auth.login_doctor(
        credentials['email'],
        credentials['password']
    )
    if not response['success']:
        raise HTTPException(status_code=401, detail=response['message'])
    return response

@app.get("/doctor/{doctor_id}/schedule")
async def get_doctor_schedule(doctor_id: str, date: str):
    """Get doctor's schedule for a specific date"""
    schedule_date = datetime.fromisoformat(date)
    response = await system.doctor_calendar.get_daily_schedule(doctor_id, schedule_date)
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

@app.post("/doctor/{doctor_id}/availability")
async def set_doctor_availability(doctor_id: str, availability: Dict[str, Any]):
    """Set doctor's availability"""
    response = await system.doctor_schedule.set_availability(doctor_id, availability)
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

# Patient endpoints
@app.get("/patient/slots/{doctor_id}")
async def get_available_slots(doctor_id: str, start_date: str, end_date: str):
    """Get available appointment slots"""
    response = await system.appointment_booking.find_available_slots(
        doctor_id,
        datetime.fromisoformat(start_date),
        datetime.fromisoformat(end_date)
    )
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

@app.post("/patient/appointment/book")
async def book_appointment(booking_data: Dict[str, Any]):
    """Book a new appointment"""
    response = await system.appointment_booking.book_appointment(
        booking_data['patient_id'],
        booking_data['doctor_id'],
        datetime.fromisoformat(booking_data['slot_time'])
    )
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

@app.put("/patient/appointment/{appointment_id}/reschedule")
async def reschedule_appointment(appointment_id: str, new_slot: Dict[str, str]):
    """Reschedule an existing appointment"""
    response = await system.appointment_reschedule.reschedule_appointment(
        appointment_id,
        datetime.fromisoformat(new_slot['slot_time'])
    )
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

@app.delete("/patient/appointment/{appointment_id}")
async def cancel_appointment(appointment_id: str):
    """Cancel an appointment"""
    response = await system.appointment_cancel.cancel_appointment(appointment_id)
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

# Voice processing endpoints
@app.post("/voice/transcribe")
async def transcribe_audio(audio_data: bytes):
    """Transcribe audio to text"""
    response = await system.stt_service.transcribe_audio(audio_data)
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

@app.post("/voice/synthesize")
async def synthesize_speech(text_data: Dict[str, str]):
    """Convert text to speech"""
    response = await system.tts_service.synthesize_speech(text_data['text'])
    if not response['success']:
        raise HTTPException(status_code=400, detail=response['message'])
    return response

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "success": False,
        "message": str(exc.detail),
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    return {
        "success": False,
        "message": "An unexpected error occurred",
        "status_code": 500
    }

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Appointment Management System")
    yield
    # Shutdown
    logger.info("Shutting down AI Appointment Management System")

# Update the FastAPI initialization
app = FastAPI(
    title="AI Appointment Management System",
    description="AI-powered system for managing medical appointments",
    version="1.0.0",
    lifespan=lifespan
)




if __name__ == "__main__":
    # Load environment variables
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
        workers=4     # Number of worker processes
    )