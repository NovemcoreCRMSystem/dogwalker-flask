import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dogwalker-flask-secret-key-change-in-production')
    N8N_BOOKING_URL = os.getenv('N8N_BOOKING_URL', 'https://novemcore.app.n8n.cloud/webhook/booking-confirm')
    N8N_COMPLETION_URL = os.getenv('N8N_COMPLETION_URL', 'https://novemcore.app.n8n.cloud/webhook/walk-complete')
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://xbanjubmkjqgryoiridz.supabase.co/rest/v1')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYW5qdWJta2pxZ3J5b2lyaWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODIwODEsImV4cCI6MjA5NzU1ODA4MX0.uCy1x-clCRbCirv2c2rigM--z6SAJcvOf6GRskT-XCs')
