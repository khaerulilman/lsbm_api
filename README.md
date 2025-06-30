# 🔐 LSB Matching Steganography dengan GUI

Ini adalah aplikasi steganografi desktop yang memungkinkan Anda untuk menyembunyikan pesan teks rahasia di dalam file gambar (`.png`, `.bmp`) dan mengekstraknya kembali. Aplikasi ini dibangun dengan Python menggunakan `tkinter` untuk antarmuka grafis (GUI).

![Screenshot (913)](https://github.com/user-attachments/assets/d1553438-c81b-4a3a-98e1-f12273644ff2)
![Screenshot (914)](https://github.com/user-attachments/assets/bfd8f7d3-8ef2-4e67-a2c9-33f68f4bb70c)
![Screenshot (915)](https://github.com/user-attachments/assets/37f51320-35da-42d2-b73b-6f4ce6f3574f)

## ✨ Fitur Utama

-   **Antarmuka Modern**: GUI yang ramah pengguna dibuat dengan `tkinter` dan `ttk`, dengan gaya kustom untuk memberikan tampilan yang lebih modern.
-   **Dua Mode Operasi**:
    -   **Encoding**: Menyisipkan pesan teks ke dalam gambar.
    -   **Decoding**: Mengekstrak pesan teks dari gambar.
-   **Keamanan Berbasis Kata Sandi**: Urutan piksel untuk penyisipan data diacak berdasarkan *hash* (SHA-256) dari kata sandi yang diberikan. Ini membuat pesan tidak dapat diekstrak tanpa kata sandi yang benar.
-   **Teknik LSB Matching**: Menggunakan metode *Least Significant Bit (LSB) Matching* untuk memodifikasi bit terakhir dari salah satu channel warna (R, G, atau B) secara acak.
-   **Penamaan File Otomatis**: Gambar yang telah disisipi pesan akan disimpan secara otomatis dengan nama baru yang mengandung sufiks `_stego` untuk identifikasi yang mudah.
-   **Validasi & Umpan Balik**: Memberikan notifikasi jika input kurang, proses berhasil, atau terjadi error.

## 🛠️ Teknik yang Digunakan

Aplikasi ini mengimplementasikan steganografi dengan pendekatan yang lebih aman daripada LSB sekuensial standar.

1.  **Pengacakan Berbasis Kata Sandi**:
    -   Kata sandi yang Anda masukkan diubah menjadi *hash* menggunakan algoritma `SHA-256`.
    -   *Hash* ini digunakan sebagai *seed* untuk generator angka acak (`random`).
    -   Urutan semua koordinat piksel (x, y) dalam gambar kemudian diacak berdasarkan *seed* tersebut. Ini memastikan bahwa data disembunyikan dalam pola yang pseudo-acak dan unik untuk setiap kata sandi.

2.  **Proses Encoding**:
    -   Pesan teks diubah menjadi representasi biner.
    -   Panjang pesan (dalam bit) juga diubah menjadi string biner 32-bit dan disisipkan di awal. Ini memberitahu decoder berapa banyak bit yang harus dibaca.
    -   Setiap bit dari pesan disisipkan ke dalam *Least Significant Bit* (LSB) dari salah satu *channel* warna (Merah, Hijau, atau Biru) yang dipilih secara acak untuk setiap piksel.

3.  **Proses Decoding**:
    -   Prosesnya dibalik. Kata sandi yang sama digunakan untuk menghasilkan urutan piksel acak yang identik.
    -   Aplikasi membaca 32 bit pertama untuk menentukan panjang pesan, kemudian membaca sisa bit dari lokasi piksel yang benar untuk merekonstruksi pesan asli.

## 🚀 Cara Menjalankan

1.  **Clone repositori ini:**
    ```bash
    git clone [https://github.com/USERNAME/REPOSITORY_NAME.git](https://github.com/USERNAME/REPOSITORY_NAME.git)
    cd REPOSITORY_NAME
    ```
    *(Ganti `USERNAME` dan `REPOSITORY_NAME` dengan milik Anda)*

2.  **Instal dependensi yang diperlukan:**
    Aplikasi ini membutuhkan library `Pillow`.
    ```bash
    pip install Pillow
    ```

3.  **Jalankan aplikasi:**
    ```bash
    python nama_file_utama.py
    ```
    *(Ganti `nama_file_utama.py` dengan nama file Python Anda)*

4.  **Gunakan aplikasi:**
    -   Pilih **Encoding** untuk menyembunyikan pesan atau **Decoding** untuk mengekstraknya.
    -   Ikuti instruksi pada setiap layar (pilih gambar, masukkan pesan/kata sandi).

## 📦 Kebutuhan

-   Python 3.x
-   `tkinter`
-   `Pillow`

---
Dibuat dengan Python dan Tkinter.
