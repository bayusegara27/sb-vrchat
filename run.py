from app import create_app, socketio

# Panggil app factory untuk membuat aplikasi
app = create_app()

if __name__ == '__main__':
    # Mode DEVELOPMENT (Pengembangan)
    # Cukup jalankan: python run.py
    print("Menjalankan server DEVELOPMENT di http://0.0.0.0:4321")
    # host='0.0.0.0' agar bisa diakses dari jaringan lokal
    socketio.run(app, host='0.0.0.0', port=4321, debug=True)