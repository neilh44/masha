
# google_calendar_config.py
class GoogleCalendarConfig:
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    
    # Scopes required for Google Calendar
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.settings.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    # Calendar Settings
    DEFAULT_TIMEZONE = "UTC"
    APPOINTMENT_DURATION = 30  # minutes
    MAX_BOOKING_DAYS_AHEAD = 30
    MIN_BOOKING_NOTICE = 24  # hours
    
    # Calendar Colors (for different types of events)
    CALENDAR_COLORS = {
        'available': '#2ecc71',     # Green
        'booked': '#e74c3c',        # Red
        'blocked': '#95a5a6',       # Gray
        'holiday': '#f1c40f'        # Yellow
    }
    
    # Token Management
    TOKEN_FILE_PATH = "credentials/token.json"
    CREDENTIALS_FILE_PATH = "credentials/credentials.json"
    TOKEN_EXPIRY_MARGIN = 300  # seconds
    
    @classmethod
    def get_credentials_path(cls) -> str:
        """Get the absolute path to credentials file"""
        base_dir = Path(__file__).resolve().parent.parent
        return str(base_dir / cls.CREDENTIALS_FILE_PATH)
    
    @classmethod
    def get_token_path(cls) -> str:
        """Get the absolute path to token file"""
        base_dir = Path(__file__).resolve().parent.parent
        return str(base_dir / cls.TOKEN_FILE_PATH)
