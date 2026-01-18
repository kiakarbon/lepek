import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import sqlite3
from pathlib import Path
import hashlib
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import matplotlib.pyplot as plt

# ============================================
# KONFIGURASI AWAL
# ============================================

# Konfigurasi halaman
st.set_page_config(
    page_title="NaNote - Catatan Praktikum & Kalkulasi PSA",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom untuk tampilan yang lebih baik
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1E3A8A;
        font-size: 2.8rem;
        margin-bottom: 1rem;
    }
    .sub-title {
        text-align: center;
        color: #4B5563;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #1D546D;
        border-left: 5px solid #3B82F6;
        padding-left: 15px;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .data-box {
        background-color: #C0C9EE;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
    }
    .result-box {
        background-color: #C0C9EE;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #10B981;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #F59E0B;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        background-color: white;
        text-align: center;
    }
    .login-title {
        color: #1E3A8A;
        font-size: 2rem;
        margin-bottom: 10px;
    }
    .login-subtitle {
        color: #4B5563;
        margin-bottom: 30px;
    }
    .stButton > button {
        width: 100%;
        background-color: #3B82F6;
        color: white;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        border: none;
        margin-top: 20px;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #6B7280;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNGSI KEAMANAN SEDERHANA
# ============================================

def hash_password(password):
    """Hash password sederhana"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================
# FUNGSI DATABASE SEDERHANA
# ============================================

def init_database():
    """Inisialisasi database SQLite sederhana"""
    conn = sqlite3.connect('nanote_simple.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabel untuk pengguna
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk catatan praktikum
    c.execute('''
        CREATE TABLE IF NOT EXISTS catatan_praktikum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            judul TEXT,
            praktikan TEXT,
            mata_praktikum TEXT,
            tanggal TEXT,
            kelompok TEXT,
            pic TEXT,
            tujuan TEXT,
            alat_bahan TEXT,
            prosedur TEXT,
            hasil TEXT,
            analisis TEXT,
            kesimpulan TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabel untuk hasil PSA
    c.execute('''
        CREATE TABLE IF NOT EXISTS hasil_psa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            data_input TEXT,
            diameter_rata REAL,
            pdi_rata REAL,
            total_vol REAL,
            kualitas TEXT,
            distribusi TEXT,
            jumlah_partikel INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Buat user default jika belum ada
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Buat user demo
        c.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', ('demo', hash_password('demo123')))
        
        # Buat user admin
        c.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', ('admin', hash_password('admin123')))
    
    conn.commit()
    return conn

# ============================================
# FUNGSI LOGIN SEDERHANA
# ============================================

def login_user(conn, username, password):
    """Login pengguna sederhana"""
    c = conn.cursor()
    
    # Cari pengguna berdasarkan username
    c.execute('''
        SELECT id, password_hash 
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    user = c.fetchone()
    
    if not user:
        return False, "Username tidak ditemukan"
    
    user_id, password_hash = user
    
    # Verifikasi password
    if hash_password(password) != password_hash:
        return False, "Password salah"
    
    return True, user_id

def register_user(conn, username, password):
    """Registrasi pengguna baru sederhana"""
    c = conn.cursor()
    
    # Cek apakah username sudah ada
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        return False, "Username sudah digunakan"
    
    # Simpan pengguna ke database
    try:
        c.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', (username, hash_password(password)))
        
        user_id = c.lastrowid
        conn.commit()
        
        return True, user_id
    
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================
# HALAMAN LOGIN SEDERHANA
# ============================================

def show_login_page(conn):
    """Menampilkan halaman login sederhana"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo dan judul
        st.markdown('<h1 class="login-title">🔬 NaNote</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Login untuk mulai menggunakan aplikasi</p>', unsafe_allow_html=True)
        
        # Tab untuk login dan register
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("### Masuk ke Akun")
            
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            if st.button("Login", key="login_button"):
                if not username or not password:
                    st.error("Username dan password harus diisi")
                else:
                    success, result = login_user(conn, username, password)
                    
                    if success:
                        st.session_state.user_id = result
                        st.session_state.username = username
                        st.success("Login berhasil!")
                        st.rerun()
                    else:
                        st.error(result)
            
            st.markdown("---")
            st.markdown("**Akun demo untuk mencoba:**")
            st.code("Username: demo\nPassword: demo123")
        
        with tab2:
            st.markdown("### Buat Akun Baru")
            
            new_username = st.text_input("Username Baru", placeholder="Pilih username")
            new_password = st.text_input("Password Baru", type="password", placeholder="Pilih password")
            confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
            
            if st.button("Daftar", key="register_button"):
                if not new_username or not new_password:
                    st.error("Username dan password harus diisi")
                elif len(new_username) < 3:
                    st.error("Username minimal 3 karakter")
                elif len(new_password) < 6:
                    st.error("Password minimal 6 karakter")
                elif new_password != confirm_password:
                    st.error("Password tidak cocok")
                else:
                    success, result = register_user(conn, new_username, new_password)
                    
                    if success:
                        st.success(f"Akun berhasil dibuat! Silakan login dengan username: {new_username}")
                    else:
                        st.error(result)
            
            st.markdown("---")
            st.markdown("**Catatan:**")
            st.markdown("- Data akan tersimpan secara lokal")
            st.markdown("- Jangan gunakan password yang sama dengan akun lain")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown("🔬 **NaNote** • Catatan Praktikum & Kalkulasi PSA")
    st.markdown(f"© {datetime.now().year} • Versi Sederhana")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FUNGSI UTAMA APLIKASI
# ============================================

# (Fungsi-fungsi kalkulasi PSA dan pembuatan file tetap sama seperti sebelumnya)
def kalkulasi_hasil_psa(pdi, vol, diameter):
    """Kalkulasi hasil PSA berdasarkan parameter input"""
    try:
        pdi_array = np.array(pdi)
        vol_array = np.array(vol)
        diameter_array = np.array(diameter)
        
        total_vol = np.sum(vol_array)
        if total_vol == 0:
            return None
            
        diameter_rata = np.sum(diameter_array * vol_array) / total_vol
        pdi_rata = np.sum(pdi_array * vol_array) / total_vol
        
        distribusi = {
            '<10 nm': np.sum(vol_array[diameter_array < 10]),
            '10-50 nm': np.sum(vol_array[(diameter_array >= 10) & (diameter_array < 50)]),
            '50-100 nm': np.sum(vol_array[(diameter_array >= 50) & (diameter_array < 100)]),
            '100-500 nm': np.sum(vol_array[(diameter_array >= 100) & (diameter_array < 500)]),
            '>500 nm': np.sum(vol_array[diameter_array >= 500])
        }
        
        if pdi_rata < 0.1:
            kualitas = "Sangat Baik (Monodispers)"
            warna_kualitas = "green"
        elif pdi_rata < 0.2:
            kualitas = "Baik"
            warna_kualitas = "lightgreen"
        elif pdi_rata < 0.3:
            kualitas = "Cukup"
            warna_kualitas = "orange"
        else:
            kualitas = "Kurang (Polydispers Tinggi)"
            warna_kualitas = "red"
        
        hasil = {
            'diameter_rata': float(diameter_rata),
            'pdi_rata': float(pdi_rata),
            'total_vol': float(total_vol),
            'distribusi': distribusi,
            'kualitas': kualitas,
            'warna_kualitas': warna_kualitas,
            'jumlah_partikel': len(pdi)
        }
        
        return hasil
        
    except Exception as e:
        st.error(f"Error dalam perhitungan: {str(e)}")
        return None

def buat_file_word(catatan_data):
    doc = Document()
    doc.add_heading('Catatan Praktikum NaNote', 0)
    doc.add_paragraph(f"Judul: {catatan_data.get('judul', 'Tanpa Judul')}")
    doc.add_paragraph(f"Tanggal: {catatan_data.get('tanggal', datetime.now().strftime('%Y-%m-%d'))}")
    doc.add_paragraph(f"Praktikan: {catatan_data.get('praktikan', 'Tidak Diketahui')}")
    doc.add_paragraph(f"Mata Praktikum: {catatan_data.get('mata_praktikum', 'Tidak Diketahui')}")
    doc.add_paragraph()
    
    doc.add_heading('Isi Catatan', level=1)
    for bagian, isi in catatan_data.get('isi', {}).items():
        doc.add_heading(bagian, level=2)
        doc.add_paragraph(isi)
    
    if 'data_psa' in catatan_data:
        doc.add_heading('Data PSA', level=1)
        for key, value in catatan_data['data_psa'].items():
            doc.add_paragraph(f"{key}: {value}")
    
    return doc

def buat_file_pdf(hasil_psa, data_input):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "LAPORAN HASIL PSA NANOMATERIAL")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"Tanggal: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
    
    c.line(50, 720, 550, 720)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 690, "HASIL PERHITUNGAN PSA")
    
    y_position = 670
    c.setFont("Helvetica", 10)
    
    hasil_items = [
        ("Diameter Rata-rata", f"{hasil_psa['diameter_rata']:.2f} nm"),
        ("PDI Rata-rata", f"{hasil_psa['pdi_rata']:.3f}"),
        ("Kualitas Nanomaterial", hasil_psa['kualitas']),
        ("Total Volume", f"{hasil_psa['total_vol']:.1f}%"),
        ("Jumlah Partikel", str(hasil_psa['jumlah_partikel']))
    ]
    
    for item, value in hasil_items:
        c.drawString(70, y_position, f"{item}: {value}")
        y_position -= 20
    
    y_position -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "DISTRIBUSI UKURAN PARTIKEL")
    y_position -= 20
    
    c.setFont("Helvetica", 10)
    for ukuran, persentase in hasil_psa['distribusi'].items():
        c.drawString(70, y_position, f"{ukuran}: {persentase:.1f}%")
        y_position -= 15
    
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "DATA INPUT")
    y_position -= 20
    
    data = [["No", "PDI", "%Vol", "Diameter (nm)"]] + data_input
    table = Table(data, colWidths=[50, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    table.wrapOn(c, 400, 200)
    table.drawOn(c, 50, y_position - len(data_input) * 20)
    
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, f"Dibuat dengan NaNote v1.0 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def buat_grafik_distribusi(distribusi):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    labels = list(distribusi.keys())
    values = list(distribusi.values())
    
    bars = ax.bar(labels, values, color=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'])
    
    ax.set_xlabel('Rentang Ukuran', fontsize=12)
    ax.set_ylabel('Persentase Volume (%)', fontsize=12)
    ax.set_title('Distribusi Ukuran Partikel', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

# ============================================
# FUNGSI DATABASE UNTUK APLIKASI UTAMA
# ============================================

def save_catatan_to_db(conn, user_id, catatan_data):
    """Menyimpan catatan ke database"""
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO catatan_praktikum 
            (user_id, judul, praktikan, mata_praktikum, tanggal, kelompok, pic, 
             tujuan, alat_bahan, prosedur, hasil, analisis, kesimpulan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            catatan_data['judul'],
            catatan_data['praktikan'],
            catatan_data['mata_praktikum'],
            catatan_data['tanggal'],
            catatan_data.get('kelompok', ''),
            catatan_data.get('pic', ''),
            catatan_data['isi']['tujuan'],
            catatan_data['isi']['alat_bahan'],
            catatan_data['isi']['prosedur'],
            catatan_data['isi']['hasil'],
            catatan_data['isi'].get('analisis', ''),
            catatan_data['isi'].get('kesimpulan', '')
        ))
        
        catatan_id = c.lastrowid
        conn.commit()
        
        return catatan_id
    
    except Exception as e:
        return None

def save_psa_to_db(conn, user_id, psa_data, data_input):
    """Menyimpan hasil PSA ke database"""
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO hasil_psa 
            (user_id, data_input, diameter_rata, pdi_rata, total_vol, 
             kualitas, distribusi, jumlah_partikel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            json.dumps(data_input),
            psa_data['diameter_rata'],
            psa_data['pdi_rata'],
            psa_data['total_vol'],
            psa_data['kualitas'],
            json.dumps(psa_data['distribusi']),
            psa_data['jumlah_partikel']
        ))
        
        psa_id = c.lastrowid
        conn.commit()
        
        return psa_id
    
    except Exception as e:
        return None

def get_user_catatan(conn, user_id):
    """Mendapatkan catatan pengguna dari database"""
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM catatan_praktikum 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    
    rows = c.fetchall()
    catatan_list = []
    
    for row in rows:
        catatan_list.append({
            'id': row[0],
            'judul': row[2],
            'praktikan': row[3],
            'mata_praktikum': row[4],
            'tanggal': row[5],
            'kelompok': row[6],
            'pic': row[7],
            'isi': {
                'tujuan': row[8],
                'alat_bahan': row[9],
                'prosedur': row[10],
                'hasil': row[11],
                'analisis': row[12],
                'kesimpulan': row[13]
            },
            'created_at': row[14]
        })
    
    return catatan_list

def get_user_psa_history(conn, user_id):
    """Mendapatkan riwayat PSA pengguna dari database"""
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM hasil_psa 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    
    rows = c.fetchall()
    psa_list = []
    
    for row in rows:
        psa_list.append({
            'id': row[0],
            'data_input': json.loads(row[2]),
            'diameter_rata': row[3],
            'pdi_rata': row[4],
            'total_vol': row[5],
            'kualitas': row[6],
            'distribusi': json.loads(row[7]),
            'jumlah_partikel': row[8],
            'created_at': row[9]
        })
    
    return psa_list

# ============================================
# APLIKASI UTAMA SETELAH LOGIN
# ============================================

def main_app(conn, user_id, username):
    """Aplikasi utama setelah login"""
    
    # Inisialisasi session state
    if 'catatan_list' not in st.session_state:
        st.session_state.catatan_list = []
    if 'current_note' not in st.session_state:
        st.session_state.current_note = {}
    if 'current_psa' not in st.session_state:
        st.session_state.current_psa = {}
    
    # Sidebar
    with st.sidebar:
        st.image("https://i.pinimg.com/1200x/8b/06/a8/8b06a832394c6d214729546d6888d0d0.jpg", width=80)
        st.title("NaNote")
        st.markdown(f"**User:** {username}")
        
        st.markdown("---")
        
        # Menu navigasi
        menu = st.radio(
            "Pilih Menu:",
            ["🏠 Beranda", "📝 Catatan Praktikum", "🧮 Kalkulasi PSA", "📊 Data Tersimpan", "ℹ️ Panduan", "🚪 Logout"]
        )
        
        if menu == "🚪 Logout":
            if 'user_id' in st.session_state:
                del st.session_state.user_id
            if 'username' in st.session_state:
                del st.session_state.username
            st.success("Logout berhasil!")
            st.rerun()
    
    # Konten utama berdasarkan menu
    if menu == "🏠 Beranda":
        st.markdown('<h1 class="main-title">🔬 NaNote</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">Aplikasi Catatan Praktikum & Kalkulator PSA untuk Nanomaterial</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="data-box">
                <h3>📝 Catatan Praktikum</h3>
                <p>Buat dan simpan catatan praktikum Anda dalam format Microsoft Word (.docx).</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="data-box">
                <h3>🧮 Kalkulasi PSA</h3>
                <p>Hitung hasil Particle Size Analysis dari data PDI, %vol, dan diameter.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="data-box">
                <h3>📊 Ekspor Data</h3>
                <p>Ekspor hasil dalam format standar untuk laporan.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Statistik sederhana
        st.markdown("### 📊 Statistik Anda")
        
        c = conn.cursor()
        
        # Hitung jumlah catatan
        c.execute("SELECT COUNT(*) FROM catatan_praktikum WHERE user_id = ?", (user_id,))
        catatan_count = c.fetchone()[0]
        
        # Hitung jumlah PSA
        c.execute("SELECT COUNT(*) FROM hasil_psa WHERE user_id = ?", (user_id,))
        psa_count = c.fetchone()[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Catatan", catatan_count)
        
        with col2:
            st.metric("Total Perhitungan PSA", psa_count)
    
    elif menu == "📝 Catatan Praktikum":
        st.markdown('<h2 class="section-header">📝 Buat Catatan Praktikum</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Buat Catatan Baru", "Lihat Catatan Tersimpan"])
        
        with tab1:
            with st.form("catatan_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    judul = st.text_input("Judul Catatan*", placeholder="Contoh: Praktikum Sintesis Nanopartikel Fe3O4")
                    praktikan = st.text_input("Nama Praktikan*", placeholder="Nama lengkap Anda")
                    mata_praktikum = st.text_input("Mata Praktikum*", placeholder="Contoh: Nanomaterial 2")
                
                with col2:
                    tanggal = st.date_input("Tanggal Praktikum*", datetime.now())
                    kelompok = st.text_input("Kelompok", placeholder="Contoh: Kelompok 5")
                    pic = st.text_input("PIC Praktikum", placeholder="Nama PIC Praktikum")
                
                st.markdown("### Isi Catatan")
                
                col1, col2 = st.columns(2)
                with col1:
                    tujuan = st.text_area("Tujuan Praktikum*", height=150, 
                                        placeholder="Tuliskan tujuan praktikum...")
                    alat_bahan = st.text_area("Alat dan Bahan*", height=150,
                                            placeholder="Daftar alat dan bahan...")
                
                with col2:
                    prosedur = st.text_area("Prosedur Kerja*", height=150,
                                          placeholder="Langkah-langkah percobaan...")
                    hasil = st.text_area("Hasil Pengamatan*", height=150,
                                       placeholder="Hasil yang diamati...")
                
                analisis = st.text_area("Analisis Data", height=120,
                                      placeholder="Analisis dari hasil yang diperoleh...")
                kesimpulan = st.text_area("Kesimpulan", height=100,
                                        placeholder="Kesimpulan praktikum...")
                
                submitted = st.form_submit_button("💾 Simpan Catatan", use_container_width=True)
                
                if submitted:
                    if not all([judul, praktikan, mata_praktikum, tujuan, 
                              alat_bahan, prosedur, hasil]):
                        st.error("Harap isi semua field yang wajib diisi (*)")
                    else:
                        catatan_data = {
                            'judul': judul,
                            'praktikan': praktikan,
                            'mata_praktikum': mata_praktikum,
                            'tanggal': tanggal.strftime("%Y-%m-%d"),
                            'kelompok': kelompok,
                            'pic': pic,
                            'isi': {
                                'tujuan': tujuan,
                                'alat_bahan': alat_bahan,
                                'prosedur': prosedur,
                                'hasil': hasil,
                                'analisis': analisis,
                                'kesimpulan': kesimpulan
                            }
                        }
                        
                        # Simpan ke database
                        catatan_id = save_catatan_to_db(conn, user_id, catatan_data)
                        
                        if catatan_id:
                            st.success(f"✅ Catatan berhasil disimpan!")
                            
                            # Update session state
                            catatan_data['id'] = catatan_id
                            catatan_data['waktu_buat'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.current_note = catatan_data
                            
                            # Tombol download
                            doc = buat_file_word(catatan_data)
                            doc_buffer = io.BytesIO()
                            doc.save(doc_buffer)
                            doc_buffer.seek(0)
                            
                            st.download_button(
                                label="⬇️ Download sebagai Word (.docx)",
                                data=doc_buffer,
                                file_name=f"catatan_{catatan_data['judul'].replace(' ', '_')}_{catatan_data['tanggal']}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        else:
                            st.error("❌ Gagal menyimpan catatan")
        
        with tab2:
            # Ambil data dari database
            catatan_list = get_user_catatan(conn, user_id)
            
            if not catatan_list:
                st.info("📝 Belum ada catatan yang disimpan.")
            else:
                st.markdown(f"### 📚 Catatan Tersimpan ({len(catatan_list)})")
                
                for catatan in catatan_list:
                    with st.expander(f"{catatan['judul']} - {catatan['tanggal']}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                            st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
                            st.markdown(f"**Dibuat:** {catatan['created_at']}")
                        
                        with col2:
                            # Tombol download
                            doc = buat_file_word(catatan)
                            doc_buffer = io.BytesIO()
                            doc.save(doc_buffer)
                            doc_buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Download",
                                data=doc_buffer,
                                file_name=f"catatan_{catatan['id']}_{catatan['judul'].replace(' ', '_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"download_{catatan['id']}"
                            )
    
    elif menu == "🧮 Kalkulasi PSA":
        st.markdown('<h2 class="section-header">🧮 Kalkulasi Particle Size Analysis</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Input Data", "Hasil Kalkulasi"])
        
        with tab1:
            st.markdown("""
            <div class="warning-box">
            <strong>📋 Panduan Input Data:</strong><br>
            1. PDI (Polydispersity Index): 0.0 - 1.0 (semakin kecil semakin baik)<br>
            2. %Vol: Persentase volume partikel (0-100%)<br>
            3. Diameter: Ukuran partikel dalam nanometer (nm)<br>
            4. Minimal 2 data untuk perhitungan
            </div>
            """, unsafe_allow_html=True)
            
            # Input jumlah data
            col1, col2 = st.columns(2)
            with col1:
                jumlah_data = st.number_input(
                    "Jumlah Data:",
                    min_value=2,
                    max_value=20,
                    value=5,
                    step=1
                )
            
            with col2:
                st.markdown("")
                st.markdown("")
                if st.button("🔄 Reset Data", use_container_width=True):
                    st.session_state.current_psa = {}
            
            # Input data dalam bentuk tabel
            st.markdown("### Masukkan Data PSA")
            
            data_input = []
            for i in range(jumlah_data):
                cols = st.columns(4)
                with cols[0]:
                    ulangan = st.text_input(f"Ulangan", value=str(i+1), disabled=True, key=f"ulangan_{i}")
                with cols[1]:
                    pdi = st.number_input(
                        f"PDI",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.15,
                        step=0.01,
                        key=f"pdi_{i}"
                    )
                with cols[2]:
                    vol = st.number_input(
                        f"%Vol",
                        min_value=0.0,
                        max_value=100.0,
                        value=20.0,
                        step=1.0,
                        key=f"vol_{i}"
                    )
                with cols[3]:
                    diameter = st.number_input(
                        f"Diameter (nm)",
                        min_value=0.1,
                        value=50.0,
                        step=1.0,
                        key=f"diameter_{i}"
                    )
                data_input.append([pdi, vol, diameter])
            
            # Tombol hitung
            if st.button("🚀 Kalkulasi Hasil PSA", type="primary", use_container_width=True):
                # Ekstrak data
                pdi_list = [d[0] for d in data_input]
                vol_list = [d[1] for d in data_input]
                diameter_list = [d[2] for d in data_input]
                
                # Kalkulasi hasil
                hasil = kalkulasi_hasil_psa(pdi_list, vol_list, diameter_list)
                
                if hasil:
                    # Simpan ke database
                    psa_id = save_psa_to_db(conn, user_id, hasil, data_input)
                    
                    if psa_id:
                        st.success(f"✅ Hasil PSA berhasil disimpan!")
                        
                        st.session_state.current_psa = {
                            'id': psa_id,
                            'hasil': hasil,
                            'data_input': data_input
                        }
                    else:
                        st.error("❌ Gagal menyimpan hasil PSA")
                        st.session_state.current_psa = {
                            'hasil': hasil,
                            'data_input': data_input
                        }
                    
                    st.success("✅ Perhitungan selesai! Buka tab 'Hasil Kalkulasi'.")
                    st.rerun()
        
        with tab2:
            if 'current_psa' not in st.session_state or not st.session_state.current_psa:
                st.info("ℹ️ Masukkan data di tab 'Input Data' dan klik 'Kalkulasi Hasil PSA'.")
            else:
                hasil = st.session_state.current_psa['hasil']
                data_input = st.session_state.current_psa['data_input']
                
                st.markdown("### 📊 Hasil Kalkulasi")
                
                # Tampilkan hasil utama
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="result-box">
                    <h4>📐 Diameter Rata-rata</h4>
                    <h3>{hasil['diameter_rata']:.2f} nm</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="result-box">
                    <h4>📊 PDI Rata-rata</h4>
                    <h3>{hasil['pdi_rata']:.3f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    warna = hasil['warna_kualitas']
                    st.markdown(f"""
                    <div class="result-box">
                    <h4>🏆 Kualitas</h4>
                    <h3 style='color: {warna};'>{hasil['kualitas']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Tabel data input
                st.markdown("### 📋 Data Input")
                df_input = pd.DataFrame({
                    'No': range(1, len(data_input) + 1),
                    'PDI': [f"{d[0]:.3f}" for d in data_input],
                    '%Vol': [f"{d[1]:.1f}%" for d in data_input],
                    'Diameter (nm)': [f"{d[2]:.1f}" for d in data_input]
                })
                st.dataframe(df_input, use_container_width=True)
                
                # Grafik distribusi
                st.markdown("### 📈 Distribusi Ukuran Partikel")
                fig = buat_grafik_distribusi(hasil['distribusi'])
                st.pyplot(fig)
                
                # Tombol download PDF
                pdf_buffer = buat_file_pdf(hasil, df_input.values.tolist())
                
                st.download_button(
                    label="📄 Download Hasil sebagai PDF",
                    data=pdf_buffer,
                    file_name=f"hasil_PSA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    elif menu == "📊 Data Tersimpan":
        st.markdown('<h2 class="section-header">📊 Data Tersimpan</h2>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Catatan Praktikum", "Hasil PSA"])
        
        with tab1:
            catatan_list = get_user_catatan(conn, user_id)
            
            if not catatan_list:
                st.info("📝 Belum ada catatan yang disimpan.")
            else:
                st.markdown(f"### Total Catatan: {len(catatan_list)}")
                
                for catatan in catatan_list:
                    with st.expander(f"{catatan['judul']} ({catatan['tanggal']})"):
                        st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                        st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
                        st.markdown(f"**Dibuat:** {catatan['created_at']}")
        
        with tab2:
            psa_list = get_user_psa_history(conn, user_id)
            
            if not psa_list:
                st.info("🧮 Belum ada hasil PSA yang disimpan.")
            else:
                st.markdown(f"### Total Hasil PSA: {len(psa_list)}")
                
                for psa in psa_list:
                    with st.expander(f"PSA {psa['id']} - {psa['created_at']}"):
                        st.markdown(f"**Diameter Rata-rata:** {psa['diameter_rata']:.2f} nm")
                        st.markdown(f"**PDI Rata-rata:** {psa['pdi_rata']:.3f}")
                        st.markdown(f"**Kualitas:** {psa['kualitas']}")
    
    else:  # Panduan
        st.markdown('<h2 class="section-header">ℹ️ Panduan Penggunaan</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 📚 Tentang NaNote
        
        NaNote adalah aplikasi web untuk:
        1. **Mencatat hasil praktikum** nanomaterial
        2. **Menganalisis data PSA** (Particle Size Analysis)
        
        ### 🔎 Cara Menggunakan
        
        #### 1. Catatan Praktikum
        - Buka menu **"📝 Catatan Praktikum"**
        - Isi form dengan data lengkap
        - Simpan dan download sebagai Word
        
        #### 2. Kalkulator PSA
        - Buka menu **"🧮 Kalkulator PSA"**
        - Input data PDI, %vol, dan diameter
        - Klik "Kalkulasi Hasil PSA"
        - Download hasil sebagai PDF
        
        ### 📊 Interpretasi Hasil PSA
        
        **Polydispersity Index (PDI):**
        - **< 0.1**: Sangat Baik (Monodispers)
        - **0.1 - 0.2**: Baik
        - **0.2 - 0.3**: Cukup
        - **> 0.3**: Kurang (Polydispers Tinggi)
        
        ### 🔒 Keamanan
        - Data disimpan secara lokal
        - Gunakan password yang aman
        - Logout setelah selesai
        """)
    
    # Footer
    st.markdown("---")
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown("🔬 **NaNote** • Catatan Praktikum & Kalkulasi PSA")
    st.markdown(f"© {datetime.now().year} • User: {username}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Fungsi utama aplikasi"""
    # Inisialisasi database
    conn = init_database()
    
    # Cek apakah pengguna sudah login
    if 'user_id' not in st.session_state:
        # Tampilkan halaman login
        show_login_page(conn)
    else:
        # Tampilkan aplikasi utama
        main_app(conn, st.session_state.user_id, st.session_state.username)
    
    # Tutup koneksi
    conn.close()

if __name__ == "__main__":
    main()
