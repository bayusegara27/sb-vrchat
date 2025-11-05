// --- Variabel Global & Konstanta ---
const RESOLUTION_X = 3840;
const RESOLUTION_Y = 2160;
// PERBAIKAN: Gunakan 'window.location.origin' untuk mendapatkan URL server secara dinamis
const serverBaseUrl = window.location.origin;

const loadingIndicator = document.getElementById("loading-indicator");
const userInfoDiv = document.getElementById("user-info");
const instructionText = document.getElementById("instruction-text");

const uploadImageInput = document.getElementById("upload-image-input");
const uploadLabel = document.getElementById("upload-label");
const saveBtn = document.getElementById("save-btn");
const cancelBtn = document.getElementById("cancel-btn");

let canvas;
let socket;

let isUpdatingFromServer = false;
let stagingSticker = null;

// --- Fungsi Memuat Latar Belakang ---
function setCanvasBackground(timestamp) {
  // Gunakan path relatif dari serverBaseUrl
  const imageUrl = `${serverBaseUrl}/static/canvas_board_latest.png?t=${timestamp}`;

  loadingIndicator.textContent = "Memuat papan stiker...";
  loadingIndicator.classList.remove("hidden");
  console.log("Memuat latar belakang:", imageUrl);

  fabric.Image.fromURL(
    imageUrl,
    (img) => {
      canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
        scaleX: canvas.width / img.width,
        scaleY: canvas.height / img.height,
        originX: "left",
        originY: "top",
      });
      console.log("Latar belakang kanvas diperbarui.");
      loadingIndicator.classList.add("hidden");
    },
    { crossOrigin: "anonymous" }
  );
}

// --- Fungsi Setup SocketIO ---
function setupSocketIO() {
  // Tidak perlu URL jika server & klien di domain yang sama
  socket = io();

  socket.on("connect", () => {
    userInfoDiv.textContent = `Terhubung ke server`;
    // Sembunyikan loading jika muncul saat koneksi awal
    if (loadingIndicator.textContent === "Memuat papan stiker...") {
      loadingIndicator.classList.add("hidden");
    }
  });

  socket.on("canvas_updated", (data) => {
    console.log("Menerima pembaruan kanvas dari server...");
    // Selalu muat ulang jika ada pembaruan
    setCanvasBackground(data.timestamp);
  });

  socket.on("disconnect", () => {
    userInfoDiv.textContent = "Terputus. Mencoba menghubungkan kembali...";
  });
}

// --- ROMBAK: Fungsi Mengirim PNG (Menjadi Promise) ---
function generateAndSendCanvasImage() {
  // Dibungkus dalam Promise agar kita bisa 'await'
  return new Promise((resolve, reject) => {
    console.log("Membuat OVERLAY stiker 4K untuk dikirim ke server...");

    // Teks loading sudah diatur oleh saveBtn listener

    const currentViewport = canvas.viewportTransform;
    const currentBackground = canvas.backgroundImage;

    // 1. Reset zoom untuk render 4K
    canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);

    // 2. Hapus latar belakang (ASYNCHRONOUS)
    canvas.setBackgroundImage(null, () => {
      // --- BERIKUTNYA DIJALANKAN DI DALAM CALLBACK ---

      // 3. Render kanvas (sekarang HANYA stiker di atas transparan)
      const dataURL = canvas.toDataURL({
        format: "png",
        quality: 1.0,
        width: RESOLUTION_X,
        height: RESOLUTION_Y,
        multiplier: 1,
      });

      // 4. KEMBALIKAN latar belakang & viewport (ASYNCHRONOUS)
      canvas.setBackgroundImage(currentBackground, () => {
        // Kembalikan viewport SETELAH background juga kembali
        canvas.setViewportTransform(currentViewport);
        canvas.renderAll();

        // 5. Kirim data ke server
        fetch(`${serverBaseUrl}/save_image`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_data: dataURL }),
        })
          .then((res) => res.json())
          .then((result) => {
            if (result.success) {
              console.log("OVERLAY stiker berhasil DIKIRIM ke server.");

              // Panggil setCanvasBackground dengan jeda
              console.log(
                "Memuat ulang kanvas untuk si pengirim (dengan jeda 1 detik)..."
              );
              setTimeout(() => {
                setCanvasBackground(new Date().getTime());
                resolve(); // <-- Selesaikan Promise di sini
              }, 1000);
            } else {
              console.error("Gagal mengirim overlay ke server:", result.error);
              loadingIndicator.classList.add("hidden");
              reject(new Error(result.error)); // <-- Tolak Promise
            }
          })
          .catch((error) => {
            console.error("Error mengirim overlay ke server:", error);
            loadingIndicator.classList.add("hidden");
            instructionText.textContent = "Gagal menyimpan stiker. Coba lagi.";
            reject(error); // <-- Tolak Promise
          });
      }); // Akhir dari callback setBackgroundImage (kembali)
    }); // Akhir dari callback setBackgroundImage(null)
  }); // Akhir dari Promise
}

// --- Fungsi Mode Edit ---
function setEditingMode(isEditing) {
  if (isEditing) {
    uploadLabel.classList.add("hidden");
    saveBtn.classList.remove("hidden");
    cancelBtn.classList.remove("hidden");
    // ROMBAK: Aktifkan tombol saat mode edit
    saveBtn.disabled = false;
    cancelBtn.disabled = false;
    instructionText.textContent =
      "Atur posisi, ukuran, dan rotasi stiker, lalu tekan Simpan.";
  } else {
    uploadLabel.classList.remove("hidden");
    saveBtn.classList.add("hidden");
    cancelBtn.classList.add("hidden");
    // ROMBAK: Nonaktifkan tombol saat tidak mode edit
    saveBtn.disabled = true;
    cancelBtn.disabled = true;
    instructionText.textContent = "Pilih gambar untuk ditambahkan ke papan.";
    stagingSticker = null;
    canvas.discardActiveObject();
    canvas.renderAll();
  }
}

// --- Fungsi Setup Fabric.js ---
function initializeFabricCanvas() {
  const canvasWrapper = document.getElementById("canvas-wrapper");
  canvas = new fabric.Canvas("sticker-canvas");

  // Fungsi resize (logika sudah benar)
  function resizeCanvas() {
    const containerWidth = canvasWrapper.clientWidth;
    const scale = containerWidth / RESOLUTION_X;
    canvas.setViewportTransform([scale, 0, 0, scale, 0, 0]);
    canvas.renderAll();
  }

  window.addEventListener("resize", resizeCanvas, false);
  resizeCanvas();
}

// --- Fungsi Setup Tombol ---
function setupButtonListeners() {
  uploadImageInput.addEventListener("change", async (e) => {
    if (stagingSticker) return;
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    loadingIndicator.textContent = "Mengunggah gambar...";
    loadingIndicator.classList.remove("hidden");
    instructionText.textContent = "Mengunggah gambar...";
    uploadLabel.classList.add("opacity-50", "pointer-events-none"); // Nonaktifkan tombol pilih

    try {
      const response = await fetch(`${serverBaseUrl}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        addImageToCanvas(data.url);
        uploadImageInput.value = "";
      } else {
        alert("Gagal mengunggah gambar: " + data.error);
        loadingIndicator.classList.add("hidden"); // Sembunyikan jika gagal
        instructionText.textContent =
          "Pilih gambar untuk ditambahkan ke papan."; // Reset teks
        uploadLabel.classList.remove("opacity-50", "pointer-events-none"); // Aktifkan kembali
      }
    } catch (error) {
      console.error("Error saat mengunggah:", error);
      alert("Terjadi kesalahan saat mengunggah gambar.");
      loadingIndicator.classList.add("hidden"); // Sembunyikan jika gagal
      instructionText.textContent = "Pilih gambar untuk ditambahkan ke papan."; // Reset teks
      uploadLabel.classList.remove("opacity-50", "pointer-events-none"); // Aktifkan kembali
    }
  });

  //
  // *** INI ADALAH FUNGSI YANG DIPERBAIKI ***
  //
  const addImageToCanvas = (imageUrl) => {
    fabric.Image.fromURL(
      imageUrl,
      (img) => {
        if (img.width === 0 || img.height === 0) {
          alert("Gagal memuat gambar.");
          loadingIndicator.classList.add("hidden"); // Sembunyikan jika gagal
          instructionText.textContent =
            "Pilih gambar untuk ditambahkan ke papan."; // Reset teks
          uploadLabel.classList.remove("opacity-50", "pointer-events-none"); // Aktifkan kembali
          return;
        }

        // --- AWAL PERBAIKAN UNTUK GAMBAR BURAM ---
        // Tetapkan batas maksimum (misal, setengah lebar kanvas)
        // agar stiker tidak terlalu besar, tapi pertahankan resolusi aslinya jika kecil.

        const MAX_STICKER_WIDTH = RESOLUTION_X / 2; // Batas maks 1920px

        if (img.width > MAX_STICKER_WIDTH) {
          // Hanya kecilkan jika stiker ASLINYA lebih besar dari 1920px
          img.scaleToWidth(MAX_STICKER_WIDTH);
        } else {
          // Jika gambar aslinya sudah pas (misal 1000px),
          // biarkan saja. Jangan di-scale sama sekali.
          // Ini akan mempertahankan kualitas 1:1
        }
        // --- AKHIR PERBAIKAN ---

        canvas.add(img);
        canvas.centerObject(img);
        stagingSticker = img;
        canvas.setActiveObject(img);
        setEditingMode(true);
        canvas.renderAll();
        loadingIndicator.classList.add("hidden"); // Sembunyikan setelah stiker muncul
        uploadLabel.classList.remove("opacity-50", "pointer-events-none"); // Aktifkan kembali
      },
      { crossOrigin: "anonymous" }
    );
  };

  // --- ROMBAK: Save Button Listener (Async) ---
  saveBtn.addEventListener("click", async () => {
    if (!stagingSticker) return;

    // 1. Set UI ke mode "Menyimpan"
    loadingIndicator.textContent =
      "Menyimpan stiker... Ini mungkin perlu beberapa detik.";
    loadingIndicator.classList.remove("hidden");
    saveBtn.disabled = true; // Nonaktifkan tombol
    cancelBtn.disabled = true; // Nonaktifkan tombol
    instructionText.textContent = "Sedang menyimpan stiker ke papan...";

    try {
      // 2. Await fungsi async
      await generateAndSendCanvasImage();

      // 3. Hapus stiker dari kanvas (setelah save berhasil & reload dimulai)
      canvas.remove(stagingSticker);

      // 4. Kembali ke mode normal (akan menyembunyikan & menonaktifkan tombol)
      setEditingMode(false);
    } catch (error) {
      console.error("Gagal menyimpan stiker:", error);
      alert("Terjadi kegagalan saat menyimpan stiker. Coba lagi.");
      // 4b. Kembali ke mode normal (editing) jika gagal
      setEditingMode(true); // Biarkan mereka coba lagi
      instructionText.textContent =
        "Gagal menyimpan. Coba atur ulang stiker dan simpan lagi.";
    }
    // 'finally' tidak diperlukan karena setEditingMode menangani status tombol
  });

  cancelBtn.addEventListener("click", () => {
    if (stagingSticker) {
      canvas.remove(stagingSticker);
      canvas.renderAll();
    }
    setEditingMode(false);
  });
}

// --- Mulai Aplikasi ---
document.addEventListener("DOMContentLoaded", () => {
  // Nonaktifkan tombol Simpan/Batal saat muat
  saveBtn.disabled = true;
  cancelBtn.disabled = true;

  initializeFabricCanvas();
  setupButtonListeners();
  setCanvasBackground(new Date().getTime());
  setupSocketIO();
});
