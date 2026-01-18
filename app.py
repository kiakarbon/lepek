import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import sqlite3
from pathlib import Path
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import matplotlib.pyplot as plt

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
    .stButton button {
        background-color: #3B82F6;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
    }
    .stDownloadButton button {
        background-color: #10B981;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #6B7280;
        font-size: 0.9rem;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNGSI DATABASE
# ============================================

def init_database():
    """Inisialisasi database SQLite"""
    conn = sqlite3.connect('nanote.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabel untuk riwayat pengguna
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            activity_type TEXT,
            activity_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk catatan praktikum
    c.execute('''
        CREATE TABLE IF NOT EXISTS catatan_praktikum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk hasil PSA
    c.execute('''
        CREATE TABLE IF NOT EXISTS hasil_psa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            data_input TEXT,
            diameter_rata REAL,
            pdi_rata REAL,
            total_vol REAL,
            kualitas TEXT,
            distribusi TEXT,
            jumlah_partikel INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabel untuk statistik penggunaan
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            page_views INTEGER DEFAULT 0,
            catatan_created INTEGER DEFAULT 0,
            psa_calculated INTEGER DEFAULT 0,
            last_active DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def get_user_id():
    """Mendapatkan ID unik pengguna dari session state"""
    if 'user_id' not in st.session_state:
        # Generate user ID berdasarkan waktu dan random number
        import random
        import time
        st.session_state.user_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
    return st.session_state.user_id

def log_activity(conn, activity_type, activity_data):
    """Mencatat aktivitas pengguna ke database"""
    user_id = get_user_id()
    c = conn.cursor()
    
    # Log aktivitas
    c.execute('''
        INSERT INTO user_history (user_id, activity_type, activity_data)
        VALUES (?, ?, ?)
    ''', (user_id, activity_type, json.dumps(activity_data)))
    
    # Update statistik penggunaan
    c.execute('''
        INSERT OR IGNORE INTO usage_stats (user_id, page_views, catatan_created, psa_calculated, last_active)
        VALUES (?, 0, 0, 0, CURRENT_TIMESTAMP)
    ''', (user_id,))
    
    # Update last_active
    c.execute('''
        UPDATE usage_stats 
        SET last_active = CURRENT_TIMESTAMP 
        WHERE user_id = ?
    ''', (user_id,))
    
    # Update statistik berdasarkan jenis aktivitas
    if activity_type == 'catatan_created':
        c.execute('''
            UPDATE usage_stats 
            SET catatan_created = catatan_created + 1 
            WHERE user_id = ?
        ''', (user_id,))
    elif activity_type == 'psa_calculated':
        c.execute('''
            UPDATE usage_stats 
            SET psa_calculated = psa_calculated + 1 
            WHERE user_id = ?
        ''', (user_id,))
    
    conn.commit()

def save_catatan_to_db(conn, catatan_data):
    """Menyimpan catatan ke database"""
    user_id = get_user_id()
    c = conn.cursor()
    
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
    
    # Log aktivitas
    log_activity(conn, 'catatan_created', {
        'catatan_id': catatan_id,
        'judul': catatan_data['judul'],
        'timestamp': datetime.now().isoformat()
    })
    
    return catatan_id

def save_psa_to_db(conn, psa_data, data_input):
    """Menyimpan hasil PSA ke database"""
    user_id = get_user_id()
    c = conn.cursor()
    
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
    
    # Log aktivitas
    log_activity(conn, 'psa_calculated', {
        'psa_id': psa_id,
        'diameter_rata': psa_data['diameter_rata'],
        'pdi_rata': psa_data['pdi_rata'],
        'timestamp': datetime.now().isoformat()
    })
    
    return psa_id

def get_user_catatan(conn):
    """Mendapatkan catatan pengguna dari database"""
    user_id = get_user_id()
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
            'waktu_buat': row[14]
        })
    
    return catatan_list

def get_user_psa_history(conn):
    """Mendapatkan riwayat PSA pengguna dari database"""
    user_id = get_user_id()
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

def get_user_stats(conn):
    """Mendapatkan statistik penggunaan pengguna"""
    user_id = get_user_id()
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM usage_stats WHERE user_id = ?
    ''', (user_id,))
    
    row = c.fetchone()
    
    if row:
        return {
            'page_views': row[2],
            'catatan_created': row[3],
            'psa_calculated': row[4],
            'last_active': row[5],
            'created_at': row[6]
        }
    else:
        return {
            'page_views': 0,
            'catatan_created': 0,
            'psa_calculated': 0,
            'last_active': None,
            'created_at': None
        }

def get_recent_activities(conn, limit=10):
    """Mendapatkan aktivitas terkini pengguna"""
    user_id = get_user_id()
    c = conn.cursor()
    
    c.execute('''
        SELECT activity_type, activity_data, timestamp 
        FROM user_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    rows = c.fetchall()
    activities = []
    
    for row in rows:
        activity_data = json.loads(row[1]) if row[1] else {}
        activities.append({
            'type': row[0],
            'data': activity_data,
            'timestamp': row[2]
        })
    
    return activities

# Inisialisasi database
conn = init_database()

# ============================================
# FUNGSI-FUNGSI UTAMA (TETAP SAMA)
# ============================================

# Fungsi untuk menghitung hasil PSA
def kalkulasi_hasil_psa(pdi, vol, diameter):
    """
    Kalkulasi hasil PSA berdasarkan parameter input
    """
    try:
        # Konversi ke array numpy untuk perhitungan
        pdi_array = np.array(pdi)
        vol_array = np.array(vol)
        diameter_array = np.array(diameter)
        
        # Hitung rata-rata berbobot
        total_vol = np.sum(vol_array)
        if total_vol == 0:
            return None
            
        # Diameter rata-rata berbobot volume
        diameter_rata = np.sum(diameter_array * vol_array) / total_vol
        
        # PDI rata-rata berbobot volume
        pdi_rata = np.sum(pdi_array * vol_array) / total_vol
        
        # Hitung distribusi ukuran
        distribusi = {
            '<10 nm': np.sum(vol_array[diameter_array < 10]),
            '10-50 nm': np.sum(vol_array[(diameter_array >= 10) & (diameter_array < 50)]),
            '50-100 nm': np.sum(vol_array[(diameter_array >= 50) & (diameter_array < 100)]),
            '100-500 nm': np.sum(vol_array[(diameter_array >= 100) & (diameter_array < 500)]),
            '>500 nm': np.sum(vol_array[diameter_array >= 500])
        }
        
        # Tentukan kualitas berdasarkan PDI
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

# Fungsi untuk membuat file Word dari catatan
def buat_file_word(catatan_data):
    doc = Document()
    
    # Judul
    doc.add_heading('Catatan Praktikum NaNote', 0)
    
    # Metadata
    doc.add_paragraph(f"Judul: {catatan_data.get('judul', 'Tanpa Judul')}")
    doc.add_paragraph(f"Tanggal: {catatan_data.get('tanggal', datetime.now().strftime('%Y-%m-%d'))}")
    doc.add_paragraph(f"Praktikan: {catatan_data.get('praktikan', 'Tidak Diketahui')}")
    doc.add_paragraph(f"Mata Praktikum: {catatan_data.get('mata_praktikum', 'Tidak Diketahui')}")
    doc.add_paragraph()
    
    # Isi catatan
    doc.add_heading('Isi Catatan', level=1)
    for bagian, isi in catatan_data.get('isi', {}).items():
        doc.add_heading(bagian, level=2)
        doc.add_paragraph(isi)
    
    # Data PSA jika ada
    if 'data_psa' in catatan_data:
        doc.add_heading('Data PSA', level=1)
        for key, value in catatan_data['data_psa'].items():
            doc.add_paragraph(f"{key}: {value}")
    
    return doc

# Fungsi untuk membuat PDF dari hasil PSA
def buat_file_pdf(hasil_psa, data_input):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Judul
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "LAPORAN HASIL PSA NANOMATERIAL")
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"Tanggal: {datetime.now().strftime('%d %B %Y %H:%M:%S')}")
    
    # Garis pembatas
    c.line(50, 720, 550, 720)
    
    # Hasil Perhitungan
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
    
    # Distribusi Ukuran
    y_position -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "DISTRIBUSI UKURAN PARTIKEL")
    y_position -= 20
    
    c.setFont("Helvetica", 10)
    for ukuran, persentase in hasil_psa['distribusi'].items():
        c.drawString(70, y_position, f"{ukuran}: {persentase:.1f}%")
        y_position -= 15
    
    # Data Input
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "DATA INPUT")
    y_position -= 20
    
    # Buat tabel data input
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
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, f"Dibuat dengan NaNote v1.0 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# Fungsi untuk membuat grafik distribusi
def buat_grafik_distribusi(distribusi):
    fig, ax = plt.subplots(figsize=(8, 5))
    
    labels = list(distribusi.keys())
    values = list(distribusi.values())
    
    bars = ax.bar(labels, values, color=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'])
    
    ax.set_xlabel('Rentang Ukuran', fontsize=12)
    ax.set_ylabel('Persentase Volume (%)', fontsize=12)
    ax.set_title('Distribusi Ukuran Partikel', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Tambahkan nilai di atas bar
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

# ============================================
# INISIALISASI SESSION STATE
# ============================================

if 'catatan_list' not in st.session_state:
    st.session_state.catatan_list = []
if 'psa_data' not in st.session_state:
    st.session_state.psa_data = []
if 'current_note' not in st.session_state:
    st.session_state.current_note = {}
if 'current_psa' not in st.session_state:
    st.session_state.current_psa = {}
if 'show_download' not in st.session_state:
    st.session_state.show_download = False
if 'user_stats' not in st.session_state:
    st.session_state.user_stats = {}
if 'recent_activities' not in st.session_state:
    st.session_state.recent_activities = []

# Sidebar
with st.sidebar:
    st.image("https://i.pinimg.com/1200x/8b/06/a8/8b06a832394c6d214729546d6888d0d0.jpg", width=80)
    st.title("NaNote")
    st.markdown("**Catatan & Kalkulator PSA**")
    
    # Tampilkan statistik pengguna
    user_stats = get_user_stats(conn)
    st.markdown("---")
    st.markdown("### 📊 Statistik Anda")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Catatan", user_stats['catatan_created'])
    with col2:
        st.metric("PSA", user_stats['psa_calculated'])
    
    st.markdown("---")
    
    menu = st.radio(
        "Pilih Menu:",
        ["🏠 Beranda", "📝 Catatan Praktikum", "🧮 Kalkulasi PSA", "📊 Data Tersimpan", "📈 Riwayat & Statistik", "ℹ️ Panduan"]
    )

# ============================================
# LOG PAGE VIEW
# ============================================

# Log aktivitas setiap kali halaman dibuka
log_activity(conn, 'page_view', {
    'page': menu,
    'timestamp': datetime.now().isoformat()
})

# ============================================
# KONTEN UTAMA BERDASARKAN MENU
# ============================================

if menu == "🏠 Beranda":
    st.markdown('<h1 class="main-title">🔬 NaNote</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Aplikasi Catatan Praktikum & Kalkulator PSA untuk Nanomaterial</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="data-box">
            <h3>📝 Catatan Praktikum</h3>
            <p>Buat dan simpan catatan praktikum Anda dalam format Microsoft Word (.docx).</p>
            <ul>
                <li>Editor teks lengkap</li>
                <li>Template otomatis</li>
                <li>Simpan sebagai .docx</li>
                <li>Database terintegrasi</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="data-box">
            <h3>🧮 Kalkulasi PSA</h3>
            <p>Hitung hasil Particle Size Analysis dari data PDI, %vol, dan diameter.</p>
            <ul>
                <li>Input data multiple</li>
                <li>Perhitungan otomatis</li>
                <li>Analisis kualitas</li>
                <li>Riwayat tersimpan</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="data-box">
            <h3>📊 Ekspor Data</h3>
            <p>Ekspor hasil dalam format standar untuk laporan.</p>
            <ul>
                <li>Catatan → Word (.docx)</li>
                <li>Hasil PSA → PDF</li>
                <li>Database backup</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tampilkan statistik pengguna di beranda
    st.markdown("### 📈 Statistik Penggunaan Anda")
    user_stats = get_user_stats(conn)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h4>📝 Catatan</h4>
            <h2>{user_stats['catatan_created']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h4>🧮 PSA</h4>
            <h2>{user_stats['psa_calculated']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h4>📊 Halaman</h4>
            <h2>{user_stats['page_views']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        last_active = user_stats['last_active'] or "Belum aktif"
        st.markdown(f"""
        <div class="stats-card">
            <h4>🕒 Terakhir</h4>
            <h6>{str(last_active)[:19]}</h6>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Fitur Utama")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Untuk Catatan Praktikum:**
        - Input data praktikum lengkap
        - Kategorisasi otomatis
        - Template siap pakai
        - Ekspor ke Microsoft Word
        - Database SQLite terintegrasi
        - Riwayat tersimpan permanen
        """)
    
    with col2:
        st.markdown("""
        **Untuk Kalkulasi PSA:**
        - Input data PDI, %vol, diameter
        - Perhitungan rata-rata berbobot
        - Analisis distribusi ukuran
        - Penilaian kualitas nanomaterial
        - Ekspor ke PDF profesional
        - Riwayat perhitungan tersimpan
        """)
    
    st.markdown("---")
    
    st.markdown("### 📈 Contoh Hasil PSA")
    
    # Contoh data untuk demonstrasi
    contoh_data = pd.DataFrame({
        'Ulangan': [1, 2, 3, 4, 5],
        'PDI': [0.12, 0.15, 0.18, 0.09, 0.11],
        '%Vol': [20, 25, 30, 15, 10],
        'Diameter (nm)': [45, 52, 48, 55, 60]
    })
    
    st.dataframe(contoh_data, use_container_width=True)
    
    st.markdown("""
    **Interpretasi Hasil:**
    - **PDI < 0.1**: Sangat Baik (Monodispers)
    - **PDI 0.1-0.2**: Baik
    - **PDI 0.2-0.3**: Cukup
    - **PDI > 0.3**: Kurang (Polydispers Tinggi)
    """)

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
                    try:
                        catatan_id = save_catatan_to_db(conn, catatan_data)
                        st.success(f"✅ Catatan berhasil disimpan ke database! ID: {catatan_id}")
                        
                        # Update session state
                        catatan_data['id'] = catatan_id
                        catatan_data['waktu_buat'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.current_note = catatan_data
                        st.session_state.show_download = True
                        
                    except Exception as e:
                        st.error(f"❌ Gagal menyimpan ke database: {str(e)}")
                    
                    # Tampilkan preview
                    with st.expander("Preview Catatan", expanded=True):
                        st.markdown(f"**Judul:** {judul}")
                        st.markdown(f"**Praktikan:** {praktikan} | **Tanggal:** {tanggal}")
                        st.markdown("---")
                        st.markdown(f"**Tujuan:**\n{tujuan}")
                        st.markdown(f"**Alat dan Bahan:**\n{alat_bahan}")
                        st.markdown(f"**Prosedur:**\n{prosedur}")
                        st.markdown(f"**Hasil:**\n{hasil}")
        
        # Tombol download
        if st.session_state.show_download and st.session_state.current_note:
            catatan_data = st.session_state.current_note
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
    
    with tab2:
        # Ambil data dari database
        catatan_list = get_user_catatan(conn)
        
        if not catatan_list:
            st.info("📝 Belum ada catatan yang disimpan.")
        else:
            st.markdown(f"### 📚 Catatan Tersimpan ({len(catatan_list)})")
            
            for catatan in catatan_list:
                with st.expander(f"{catatan['judul']} - {catatan['tanggal']} (ID: {catatan['id']})"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                        st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
                        st.markdown(f"**Dibuat:** {catatan['waktu_buat']}")
                        if catatan['kelompok']:
                            st.markdown(f"**Kelompok:** {catatan['kelompok']}")
                    
                    with col2:
                        # Tombol download untuk catatan tersimpan
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
                    
                    with col3:
                        if st.button("🗑️ Hapus", key=f"delete_{catatan['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM catatan_praktikum WHERE id = ?", (catatan['id'],))
                            conn.commit()
                            st.success("✅ Catatan berhasil dihapus!")
                            st.rerun()

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
            if st.button("🔄 Reset Tabel", use_container_width=True):
                st.session_state.psa_data = []
                st.rerun()
        
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
                try:
                    psa_id = save_psa_to_db(conn, hasil, data_input)
                    st.success(f"✅ Hasil PSA berhasil disimpan ke database! ID: {psa_id}")
                    
                    st.session_state.current_psa = {
                        'id': psa_id,
                        'hasil': hasil,
                        'data_input': data_input,
                        'pdi_list': pdi_list,
                        'vol_list': vol_list,
                        'diameter_list': diameter_list
                    }
                    
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan ke database: {str(e)}")
                    st.session_state.current_psa = {
                        'hasil': hasil,
                        'data_input': data_input,
                        'pdi_list': pdi_list,
                        'vol_list': vol_list,
                        'diameter_list': diameter_list
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
            
            # Tampilkan ID jika ada
            if 'id' in st.session_state.current_psa:
                st.caption(f"ID: {st.session_state.current_psa['id']}")
            
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
            
            # Tabel distribusi
            st.markdown("### 📊 Detail Distribusi")
            df_distribusi = pd.DataFrame({
                'Rentang Ukuran': list(hasil['distribusi'].keys()),
                'Persentase Volume': [f"{v:.1f}%" for v in hasil['distribusi'].values()]
            })
            st.dataframe(df_distribusi, use_container_width=True)
            
            # Tombol download PDF
            pdf_buffer = buat_file_pdf(hasil, df_input.values.tolist())
            
            st.download_button(
                label="📄 Download Hasil sebagai PDF",
                data=pdf_buffer,
                file_name=f"hasil_PSA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf"
            )
            
            # Tambahkan ke catatan jika ada
            catatan_list = get_user_catatan(conn)
            if catatan_list:
                st.markdown("---")
                st.markdown("### 💾 Simpan ke Catatan")
                
                catatan_options = {f"{cat['judul']} (ID: {cat['id']})": cat['id'] for cat in catatan_list}
                selected_note = st.selectbox(
                    "Pilih Catatan untuk Menyimpan Hasil PSA:",
                    ["Pilih..."] + list(catatan_options.keys())
                )
                
                if selected_note != "Pilih..." and st.button("💾 Simpan ke Catatan"):
                    # Catatan: Untuk menyimpan hubungan antara catatan dan PSA,
                    # kita bisa membuat tabel relasi atau menyimpan PSA ID di catatan
                    st.info("Fitur ini dalam pengembangan. Hubungan data akan disimpan di versi berikutnya.")
                    st.success(f"✅ Hasil PSA akan dihubungkan dengan catatan terpilih.")

elif menu == "📊 Data Tersimpan":
    st.markdown('<h2 class="section-header">📊 Data Tersimpan</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Catatan Praktikum", "Hasil PSA"])
    
    with tab1:
        catatan_list = get_user_catatan(conn)
        
        if not catatan_list:
            st.info("📝 Belum ada catatan yang disimpan.")
        else:
            st.markdown(f"### Total Catatan: {len(catatan_list)}")
            
            # Statistik catatan
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Catatan Terakhir", catatan_list[0]['judul'][:20] + "..." if len(catatan_list[0]['judul']) > 20 else catatan_list[0]['judul'])
            with col2:
                st.metric("Total Catatan", len(catatan_list))
            with col3:
                # Hitung catatan bulan ini
                current_month = datetime.now().strftime("%Y-%m")
                catatan_bulan_ini = sum(1 for cat in catatan_list if cat['waktu_buat'].startswith(current_month))
                st.metric("Catatan Bulan Ini", catatan_bulan_ini)
            
            for catatan in catatan_list:
                with st.expander(f"{catatan['judul']} ({catatan['tanggal']}) - ID: {catatan['id']}"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                        st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
                        st.markdown(f"**Dibuat:** {catatan['waktu_buat']}")
                        st.markdown(f"**ID Database:** {catatan['id']}")
                    
                    with col2:
                        # Tombol download
                        doc = buat_file_word(catatan)
                        doc_buffer = io.BytesIO()
                        doc.save(doc_buffer)
                        doc_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Word",
                            data=doc_buffer,
                            file_name=f"catatan_{catatan['id']}_{catatan['judul'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"word_download_{catatan['id']}"
                        )
                    
                    with col3:
                        if st.button("🗑️ Hapus", key=f"del_cat_{catatan['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM catatan_praktikum WHERE id = ?", (catatan['id'],))
                            conn.commit()
                            st.success("✅ Catatan berhasil dihapus!")
                            st.rerun()
            
            # Tombol backup semua data
            st.markdown("---")
            st.markdown("### 📤 Backup Data")
            
            if st.button("💾 Backup Semua Catatan", use_container_width=True):
                # Buat file JSON backup
                backup_data = {
                    'catatan': catatan_list,
                    'backup_time': datetime.now().isoformat(),
                    'total_catatan': len(catatan_list)
                }
                
                backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Download Backup JSON",
                    data=backup_json,
                    file_name=f"nanote_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    with tab2:
        psa_list = get_user_psa_history(conn)
        
        if not psa_list:
            st.info("🧮 Belum ada hasil PSA yang disimpan.")
        else:
            st.markdown(f"### Total Hasil PSA: {len(psa_list)}")
            
            # Statistik PSA
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_diameter = np.mean([psa['diameter_rata'] for psa in psa_list])
                st.metric("Rata-rata Diameter", f"{avg_diameter:.2f} nm")
            with col2:
                avg_pdi = np.mean([psa['pdi_rata'] for psa in psa_list])
                st.metric("Rata-rata PDI", f"{avg_pdi:.3f}")
            with col3:
                total_partikel = sum([psa['jumlah_partikel'] for psa in psa_list])
                st.metric("Total Partikel", total_partikel)
            
            for psa in psa_list:
                with st.expander(f"PSA {psa['id']} - {psa['created_at']}"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Waktu:** {psa['created_at']}")
                        st.markdown(f"**Diameter Rata-rata:** {psa['diameter_rata']:.2f} nm")
                        st.markdown(f"**PDI Rata-rata:** {psa['pdi_rata']:.3f}")
                        st.markdown(f"**Kualitas:** {psa['kualitas']}")
                        st.markdown(f"**Jumlah Partikel:** {psa['jumlah_partikel']}")
                        st.markdown(f"**ID Database:** {psa['id']}")
                    
                    with col2:
                        # Tombol lihat detail
                        if st.button("👁️ Detail", key=f"view_psa_{psa['id']}"):
                            st.session_state.current_psa = {
                                'id': psa['id'],
                                'hasil': psa,
                                'data_input': psa['data_input']
                            }
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Hapus", key=f"del_psa_{psa['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM hasil_psa WHERE id = ?", (psa['id'],))
                            conn.commit()
                            st.success("✅ Data PSA berhasil dihapus!")
                            st.rerun()

elif menu == "📈 Riwayat & Statistik":
    st.markdown('<h2 class="section-header">📈 Riwayat & Statistik Penggunaan</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Statistik", "Riwayat Aktivitas", "Manajemen Data"])
    
    with tab1:
        st.markdown("### 📊 Statistik Penggunaan Anda")
        
        user_stats = get_user_stats(conn)
        recent_activities = get_recent_activities(conn, 5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Aktivitas Utama")
            st.metric("Total Catatan Dibuat", user_stats['catatan_created'])
            st.metric("Total PSA Dihitung", user_stats['psa_calculated'])
            st.metric("Total Halaman Dilihat", user_stats['page_views'])
        
        with col2:
            st.markdown("#### Informasi Akun")
            st.markdown(f"**User ID:** `{get_user_id()}`")
            st.markdown(f"**Akun Dibuat:** `{user_stats['created_at'] or 'Tidak diketahui'}`")
            st.markdown(f"**Terakhir Aktif:** `{user_stats['last_active'] or 'Belum aktif'}`")
        
        st.markdown("---")
        
        # Visualisasi statistik
        st.markdown("#### 📈 Grafik Aktivitas")
        
        # Ambil lebih banyak data untuk grafik
        all_activities = get_recent_activities(conn, 50)
        
        if all_activities:
            # Hitung aktivitas per hari
            from collections import defaultdict
            import datetime as dt
            
            daily_activity = defaultdict(int)
            for activity in all_activities:
                date = activity['timestamp'][:10]  # Ambil hanya tanggal
                daily_activity[date] += 1
            
            # Buat DataFrame untuk plotting
            dates = list(daily_activity.keys())[-10:]  # 10 hari terakhir
            counts = [daily_activity[date] for date in dates]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(dates, counts, color='#3B82F6')
            ax.set_xlabel('Tanggal')
            ax.set_ylabel('Jumlah Aktivitas')
            ax.set_title('Aktivitas 10 Hari Terakhir')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        
        # Ringkasan aktivitas terkini
        st.markdown("#### 🕒 Aktivitas Terkini")
        if recent_activities:
            for activity in recent_activities:
                timestamp = activity['timestamp']
                activity_type = activity['type']
                
                if activity_type == 'catatan_created':
                    emoji = "📝"
                    desc = f"Membuat catatan: {activity['data'].get('judul', 'Tanpa judul')}"
                elif activity_type == 'psa_calculated':
                    emoji = "🧮"
                    desc = f"Menghitung PSA: Diameter {activity['data'].get('diameter_rata', 0):.2f} nm"
                elif activity_type == 'page_view':
                    emoji = "👁️"
                    desc = f"Melihat halaman: {activity['data'].get('page', 'Unknown')}"
                else:
                    emoji = "📌"
                    desc = activity_type
                
                st.markdown(f"{emoji} **{timestamp}** - {desc}")
        else:
            st.info("Belum ada aktivitas yang tercatat.")
    
    with tab2:
        st.markdown("### 📋 Riwayat Aktivitas Lengkap")
        
        # Filter aktivitas
        col1, col2 = st.columns(2)
        with col1:
            limit = st.slider("Jumlah aktivitas yang ditampilkan:", 5, 100, 20)
        
        with col2:
            filter_type = st.selectbox(
                "Filter jenis aktivitas:",
                ["Semua", "catatan_created", "psa_calculated", "page_view"]
            )
        
        # Ambil data dengan filter
        all_activities = get_recent_activities(conn, 1000)  # Ambil banyak data
        
        if filter_type != "Semua":
            all_activities = [a for a in all_activities if a['type'] == filter_type]
        
        # Tampilkan tabel
        if all_activities:
            activities_display = []
            for activity in all_activities[:limit]:
                activities_display.append({
                    'Waktu': activity['timestamp'],
                    'Jenis': activity['type'],
                    'Data': str(activity['data'])[:100] + "..." if len(str(activity['data'])) > 100 else str(activity['data'])
                })
            
            df_activities = pd.DataFrame(activities_display)
            st.dataframe(df_activities, use_container_width=True)
            
            # Tombol ekspor riwayat
            csv = df_activities.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Riwayat (CSV)",
                data=csv,
                file_name=f"riwayat_aktivitas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Tidak ada aktivitas yang sesuai dengan filter.")
    
    with tab3:
        st.markdown("### 🗄️ Manajemen Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ekspor Database")
            st.markdown("""
            Ekspor seluruh data Anda dalam format JSON.
            File ini berisi:
            - Semua catatan praktikum
            - Semua hasil PSA
            - Riwayat aktivitas
            - Statistik penggunaan
            """)
            
            if st.button("📤 Ekspor Semua Data", use_container_width=True):
                # Kumpulkan semua data
                all_data = {
                    'user_id': get_user_id(),
                    'catatan': get_user_catatan(conn),
                    'psa_history': get_user_psa_history(conn),
                    'user_stats': get_user_stats(conn),
                    'recent_activities': get_recent_activities(conn, 1000),
                    'export_time': datetime.now().isoformat(),
                    'app_version': 'NaNote v1.0'
                }
                
                json_data = json.dumps(all_data, indent=2, ensure_ascii=False, default=str)
                
                st.download_button(
                    label="💾 Download Backup Lengkap",
                    data=json_data,
                    file_name=f"nanote_full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("#### Reset Data")
            st.markdown("""
            ⚠️ **PERHATIAN:** Tindakan ini akan menghapus semua data Anda!
            
            Yang akan dihapus:
            - Semua catatan praktikum
            - Semua hasil PSA
            - Riwayat aktivitas
            - Statistik penggunaan
            
            Tindakan ini tidak dapat dibatalkan!
            """)
            
            if st.checkbox("Saya mengerti dan ingin menghapus semua data"):
                if st.button("🗑️ HAPUS SEMUA DATA", type="secondary", use_container_width=True):
                    c = conn.cursor()
                    c.execute("DELETE FROM catatan_praktikum WHERE user_id = ?", (get_user_id(),))
                    c.execute("DELETE FROM hasil_psa WHERE user_id = ?", (get_user_id(),))
                    c.execute("DELETE FROM user_history WHERE user_id = ?", (get_user_id(),))
                    c.execute("DELETE FROM usage_stats WHERE user_id = ?", (get_user_id(),))
                    conn.commit()
                    
                    st.success("✅ Semua data berhasil dihapus!")
                    st.info("Halaman akan direfresh...")
                    st.rerun()

else:  # Panduan
    st.markdown('<h2 class="section-header">ℹ️ Panduan Penggunaan</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📚 Tentang NaNote
    
    NaNote adalah aplikasi web yang dirancang khusus untuk membantu praktikan dalam:
    1. **Mencatat hasil praktikum** nanomaterial secara digital
    2. **Menganalisis data PSA** (Particle Size Analysis)
    3. **Menyimpan dan mengekspor** hasil dalam format standar
    4. **Menyimpan riwayat** menggunakan database SQLite
    
    ### 🗄️ Sistem Database
    
    Aplikasi ini menggunakan **SQLite** untuk menyimpan data secara lokal. Database menyimpan:
    - **Catatan praktikum** lengkap dengan metadata
    - **Hasil perhitungan PSA** beserta data input
    - **Riwayat aktivitas** pengguna
    - **Statistik penggunaan** aplikasi
    
    ### 🔎 Cara Menggunakan
    
    #### 1. Catatan Praktikum
    - Buka menu **"📝 Catatan Praktikum"**
    - Isi form dengan data lengkap praktikum
    - Data otomatis tersimpan di database
    - Download sebagai file Word (.docx)
    
    #### 2. Kalkulator PSA
    - Buka menu **"🧮 Kalkulator PSA"**
    - Input data PDI, %vol, dan diameter untuk setiap partikel
    - Klik "Hitung Hasil PSA"
    - Hasil otomatis tersimpan di database
    - Download hasil sebagai PDF
    
    #### 3. Data Tersimpan
    - Buka menu **"📊 Data Tersimpan"**
    - Lihat semua catatan dan hasil perhitungan dari database
    - Hapus data yang tidak diperlukan
    - Backup data ke file JSON
    
    #### 4. Riwayat & Statistik
    - Buka menu **"📈 Riwayat & Statistik"**
    - Lihat statistik penggunaan aplikasi
    - Pantau riwayat aktivitas
    - Ekspor atau reset data
    
    ### 📊 Interpretasi Hasil PSA
    
    **Polydispersity Index (PDI):**
    - **< 0.1**: Sangat Baik (Monodispers)
    - **0.1 - 0.2**: Baik
    - **0.2 - 0.3**: Cukup
    - **> 0.3**: Kurang (Polydispers Tinggi)
    
    **Diameter:**
    - < 10 nm: Ultra kecil
    - 10-50 nm: Kecil
    - 50-100 nm: Sedang
    - 100-500 nm: Besar
    - > 500 nm: Sangat besar
    
    ### 💡 Tips Penggunaan Database
    1. **Backup reguler**: Ekspor data Anda secara berkala
    2. **ID Database**: Setiap data memiliki ID unik untuk referensi
    3. **Statistik**: Pantau penggunaan Anda di menu Riwayat
    4. **Pembersihan**: Hapus data lama yang tidak diperlukan
    
    ### 🛠️ Teknologi
    - **Framework**: Streamlit (Python)
    - **Database**: SQLite
    - **Format Ekspor**: .docx, .pdf, .json, .csv
    - **Deployment**: Streamlit Cloud
    - **Bahasa**: Indonesia
    
    ### 🔒 Keamanan Data
    - Data disimpan lokal dalam file `nanote.db`
    - Setiap pengguna memiliki ID unik
    - Backup data dalam format JSON aman
    - Opsi reset data tersedia
    
    ### 🤝 Kontribusi
    Aplikasi ini bersifat open source. Untuk saran dan masukan, silakan buat issue di repository GitHub.
    """)

# Footer
st.markdown("---")
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("🔬 **NaNote** • Aplikasi Catatan Praktikum & Kalkulasi PSA • Dibuat oleh Kelompok 3 Logika dan Pemrograman Komputer")
st.markdown(f"© {datetime.now().year}")
st.markdown('</div>', unsafe_allow_html=True)

# Tutup koneksi database saat aplikasi selesai
conn.close()
