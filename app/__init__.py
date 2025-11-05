# app/__init__.py

import os
import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from .config import Config

# Inisialisasi SocketIO di sini agar bisa diimpor oleh file lain
socketio = SocketIO()

def create_app():
    """Membuat dan mengkonfigurasi instance aplikasi Flask."""
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # Pastikan direktori static (dan static/css, static/js) ada
    static_dir = os.path.join(app.root_path, 'static')
    os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)

    # Inisialisasi SocketIO dengan aplikasi
    socketio.init_app(app, async_mode='eventlet')

    with app.app_context():
        # Impor rute dan event handler
        # Impor ini harus ada di dalam 'with' agar app context ada
        from . import routes
        from . import sockets
        from . import image_handler
        from . import git_updater

        # Buat file kanvas awal jika tidak ada,
        # gunakan path dari konfigurasi
        image_handler.create_initial_canvas(app.config['CANVAS_SAVE_PATH'])

    return app