# app/image_handler.py

import os
import re
import base64
import time
from io import BytesIO
from flask import current_app
from . import socketio
from . import git_updater 

try:
    from PIL import Image
except ImportError:
    print("PERINGATAN: 'Pillow' tidak terinstal. Aplikasi akan gagal saat menyimpan.")
    print("Silakan instal dengan: pip install Pillow")
    Image = None

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_canvas_image_logic(data):
    """
    Logika inti untuk menerima data stiker, menempelkannya, 
    dan menyimpan hasilnya.
    """
    if Image is None:
        raise ImportError("Pillow (PIL) tidak terinstal. Tidak bisa memproses gambar.")

    # Ini adalah data stiker (overlay) transparan
    data_url = data['image_data']
    overlay_data_b64 = re.sub('^data:image/.+;base64,', '', data_url)
    overlay_data = base64.b64decode(overlay_data_b64)
    
    # Path ke file latar belakang dari config
    bg_filepath = current_app.config['CANVAS_SAVE_PATH']

    # Buka gambar latar belakang yang ada
    # Gunakan 'RGBA' untuk memastikan mode-nya sama
    with Image.open(bg_filepath) as bg_image:
        bg_image = bg_image.convert('RGBA')

        # Buka stiker (overlay)
        with Image.open(BytesIO(overlay_data)) as overlay_image:
            overlay_image = overlay_image.convert('RGBA')
            
            # Tempelkan stiker ke latar belakang
            # Argumen ketiga (overlay_image) berfungsi sebagai mask
            # untuk menangani transparansi
            bg_image.paste(overlay_image, (0, 0), overlay_image)

        # Simpan gambar yang sudah digabung
        bg_image.save(bg_filepath, 'PNG')

    # --- 2. INI BLOK LOGIKA BARU UNTUK GIT ---
    # Tepat setelah gambar disimpan, panggil update Git
    try:
        print("Menjadwalkan pembaruan Git di latar belakang...")
        git_updater.schedule_git_update()
    except Exception as e:
        # Ini seharusnya tidak gagal, tapi untuk jaga-jaga
        print(f"FATAL: Gagal menjadwalkan pembaruan Git: {e}")
    # --- AKHIR BLOK BARU ---

    print(f"Gambar kanvas DISATUKAN dan disimpan ke: {bg_filepath}")

    # Beri tahu semua client (termasuk pengirim) bahwa gambar telah diperbarui
    timestamp = int(time.time() * 1000)
    # Tidak perlu 'broadcast=True' saat diemit dari server seperti ini
    socketio.emit('canvas_updated', {'timestamp': timestamp})

def create_initial_canvas(path):
    """Membuat file kanvas putih awal jika belum ada."""
    if not os.path.exists(path):
        try:
            if Image is None:
                raise ImportError("Pillow tidak terinstal, tidak bisa membuat file awal.")
            
            # Buat file PNG putih kosong jika tidak ada
            img = Image.new('RGB', (3840, 2160), 'white')
            
            # Pastikan direktori 'static' ada
            static_dir = os.path.dirname(path)
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)
                
            img.save(path, 'PNG')
            print(f"Membuat file latar belakang kosong di: {path}")
        except ImportError:
            print("PERINGATAN: 'Pillow' tidak terinstal. Tidak dapat membuat file latar belakang awal.")
            print("Silakan instal dengan: pip install Pillow")
        except Exception as e:
            print(f"Error membuat file latar belakang awal: {e}")