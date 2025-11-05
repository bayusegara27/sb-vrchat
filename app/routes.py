import os
import base64
import mimetypes
from flask import (
    render_template, request, jsonify, current_app
)
from werkzeug.utils import secure_filename
from . import image_handler # Impor helper kita

# Dapatkan 'app' dari context flask
from flask import current_app as app

@app.route('/')
def index():
    """Menyajikan halaman HTML utama."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Menerima file gambar, mengubahnya menjadi Base64, dan mengirimkannya kembali."""
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada bagian file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tidak ada file yang dipilih'}), 400
    
    if file and image_handler.allowed_file(file.filename):
        try:
            # Baca data file dan ubah ke Base64
            img_data = file.read()
            b64_data = base64.b64encode(img_data).decode('utf-8')
            # Tentukan mimetype
            mimetype = file.mimetype or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            # Buat data URL
            data_url = f"data:{mimetype};base64,{b64_data}"
            return jsonify({'success': True, 'url': data_url})
        except Exception as e:
            print(f"Error mengubah file ke base64: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Tipe file tidak diizinkan'}), 400

@app.route('/save_image', methods=['POST'])
def save_canvas_image():
    """Endpoint untuk menyimpan gambar."""
    try:
        data = request.get_json()
        image_handler.save_canvas_image_logic(data) # Panggil logika terpisah
        return jsonify({'success': True, 'message': 'Gambar berhasil disimpan'})
    except Exception as e:
        print(f"Error saat menyimpan gambar: {e}")
        return jsonify({'error': str(e)}), 500