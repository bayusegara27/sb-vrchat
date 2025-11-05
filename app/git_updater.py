# app/git_updater.py

import subprocess
import threading
import os
from flask import current_app

# Lock ini PENTING untuk mencegah dua orang menyimpan
# dan menjalankan 'git push' secara bersamaan (race condition).
git_lock = threading.Lock()

def run_git_commands(repo_path, file_to_add):
    """
    Menjalankan perintah Git (pull, add, commit, push) di background thread.
    """
    # Coba dapatkan lock. Jika gagal (karena sudah ada update lain),
    # lewati saja update kali ini.
    if not git_lock.acquire(blocking=False):
        print("GIT UPDATE: Sudah ada proses update lain yang berjalan. Melewatkan...")
        return

    try:
        print(f"GIT UPDATE: Memulai update Git di latar belakang untuk {file_to_add}...")

        def run_cmd(cmd_list):
            """Helper untuk menjalankan perintah subprocess dengan aman."""
            # Menjalankan perintah sebagai list, lebih aman daripada shell=True
            return subprocess.run(
                cmd_list,
                cwd=repo_path,  # Menjalankan perintah dari direktori root repo
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

        # 1. Selalu 'git pull' dulu untuk menghindari konflik
        print("GIT UPDATE: Menjalankan git pull...")
        run_cmd(["git", "pull"])

        # 2. Tambahkan file kanvas yang spesifik
        print(f"GIT UPDATE: Menjalankan git add {file_to_add}...")
        run_cmd(["git", "add", file_to_add])

        # 3. Cek apakah ada yang perlu di-commit
        status_result = run_cmd(["git", "status", "--porcelain"])
        
        # Jika file kita tidak ada di output status, berarti tidak ada perubahan
        if file_to_add not in status_result.stdout:
            print("GIT UPDATE: Tidak ada perubahan terdeteksi pada file kanvas. Membatalkan commit.")
            return  # Keluar dari fungsi

        # 4. Jika ada perubahan, commit
        print("GIT UPDATE: Menjalankan git commit...")
        commit_msg = "Update: canvas_board_latest.png [auto-commit]"
        run_cmd(["git", "commit", "-m", commit_msg])

        # 5. Push ke remote
        print("GIT UPDATE: Menjalankan git push...")
        run_cmd(["git", "push"])

        print("GIT UPDATE: Proses update Git selesai dengan sukses.")

    except subprocess.CalledProcessError as e:
        # Jika salah satu perintah Git gagal (misal: konflik, auth gagal)
        print(f"GIT UPDATE GAGAL: Perintah gagal dieksekusi.")
        print(f"ERROR: {e.stderr}")
    except Exception as e:
        print(f"GIT UPDATE GAGAL: Terjadi kesalahan tak terduga: {e}")
    finally:
        # PENTING: Selalu lepaskan lock, baik sukses maupun gagal
        git_lock.release()


def schedule_git_update():
    """
    Fungsi utama yang dipanggil oleh endpoint untuk memulai thread.
    """
    # Asumsi: Repo Git Anda adalah folder DI ATAS folder 'app'
    # app.root_path menunjuk ke /.../papan-stiker-pro/app
    repo_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
    
    # Dapatkan path file dari config, cth: 'app/static/canvas_board_latest.png'
    # Ini sudah merupakan path relatif dari root repo
    file_path_relative = current_app.config['CANVAS_SAVE_PATH']

    print(f"GIT UPDATE: Menjadwalkan update untuk {file_path_relative} di repo {repo_root}")
    
    # Buat dan mulai background thread
    thread = threading.Thread(
        target=run_git_commands,
        args=(repo_root, file_path_relative)
    )
    thread.daemon = True # Pastikan thread mati jika aplikasi utama mati
    thread.start()