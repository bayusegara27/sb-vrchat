import os
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

class Config:
    """Kelas konfigurasi untuk Flask."""
    # Ambil SECRET_KEY dari .env, atau gunakan nilai default jika tidak ada
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-darurat-jika-env-tidak-ada'
    
    # Konfigurasi aplikasi lainnya
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # Ambil CANVAS_SAVE_PATH dari .env, atau gunakan nilai default jika tidak ada
    CANVAS_SAVE_PATH = os.environ.get('CANVAS_SAVE_PATH') or 'app/static/canvas_board_latest.png'