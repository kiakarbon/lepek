# 🔬 NaNote - Aplikasi Catatan & Kalkulator PSA Nanomaterial

![NaNote](https://img.shields.io/badge/NaNote-v1.0-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-red)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

**NaNote** adalah aplikasi web berbasis Streamlit untuk mencatat hasil praktik dan mengkalkulasi hasil PSA (Particle Size Analysis) nanomaterial dalam bahasa Indonesia.

## ✨ Fitur Utama

### 📝 **Sistem Pencatatan Praktik**
- Form input lengkap untuk eksperimen nanomaterial
- Penyimpanan data terstruktur
- **Ekspor ke format Word (.docx)**

### 🧮 **Kalkulator PSA**
- Input data distribusi ukuran (Diameter, % Volume, PDI)
- Analisis statistik lengkap
- Visualisasi interaktif dengan Plotly
- Klasifikasi kualitas otomatis berdasarkan PDI
- **Ekspor ke format PDF**

### 📊 **Manajemen Data**
- Penyimpanan data dalam session
- Filter dan pencarian data
- Organisasi catatan dan hasil
- Interface user-friendly dalam bahasa Indonesia

## 🚀 Instalasi & Deployment

### **1. Instalasi Lokal**
```bash
# Clone repository
git clone https://github.com/username/nanote-app.git
cd nanote-app

# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
streamlit run app.py
