from . import socketio # Impor dari __init__.py

@socketio.on('connect')
def handle_connect():
    """Mencatat koneksi klien baru."""
    print('Client baru terhubung')

@socketio.on('disconnect')
def handle_disconnect():
    """Mencatat klien yang terputus."""
    print('Client terputus')