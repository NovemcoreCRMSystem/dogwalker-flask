import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dogwalker-flask-secret-key-change-in-production')
    N8N_BOOKING_URL = os.getenv('N8N_BOOKING_URL', 'https://novemcore.app.n8n.cloud/webhook/booking-confirm')
    N8N_COMPLETION_URL = os.getenv('N8N_COMPLETION_URL', 'https://novemcore.app.n8n.cloud/webhook/walk-complete')
