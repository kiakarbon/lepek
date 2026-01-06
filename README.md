# NaNote - Aplikasi Catatan Praktikum & Kalkulator PSA

Aplikasi web berbasis Streamlit untuk mencatat hasil praktikum dan mengkalkulasi hasil PSA (Particle Size Analysis) nanomaterial.

## 🌟 Fitur Utama

### 📝 Catatan Praktikum
- Input data praktikum lengkap (tujuan, alat, prosedur, hasil, analisis, kesimpulan)
- Template otomatis untuk berbagai jenis praktikum
- Simpan catatan dalam format Microsoft Word (.docx)
- Penyimpanan data lokal di browser

### 🧮 Kalkulator PSA
- Input data PDI, %vol, dan diameter untuk multiple sampel
- Perhitungan diameter rata-rata berbobot volume
- Analisis PDI rata-rata dan kualitas nanomaterial
- Visualisasi distribusi ukuran partikel
- Ekspor hasil dalam format PDF profesional

### 📊 Manajemen Data
- Penyimpanan data catatan dan hasil perhitungan
- Ekspor data backup dalam format JSON
- Pencarian dan filter data tersimpan
- Integrasi antara catatan dan hasil PSA

### Jalankan Lokal
```bash
# Clone repository
git clone https://github.com/username/nanote.git
cd nanote

# Install dependencies
pip install -r requirements.txt

# Run aplikasi
streamlit run app.py
