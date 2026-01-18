import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import hashlib
from pathlib import Path

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

# CSS sederhana inline
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1E3A8A;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .login-box {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        background-color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton button {
        width: 100%;
        background-color: #3B82F6;
        color: white;
        border-radius: 5px;
        padding: 10px;
        font-weight: bold;
        border: none;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNGSI LOGIN SEDERHANA
# ============================================

# Data pengguna (simpan di session state)
if 'users' not in st.session_state:
    st.session_state.users = {
        'demo': {'password': 'demo123', 'name': 'Demo User'},
        'admin': {'password': 'admin123', 'name': 'Administrator'},
        'user': {'password': 'user123', 'name': 'Regular User'}
    }

def hash_password(password):
    """Hash password sederhana"""
    return hashlib.sha256(password.encode()).hexdigest()[:10]

def check_login(username, password):
    """Cek login"""
    if username in st.session_state.users:
        if st.session_state.users[username]['password'] == password:
            return True
    return False

def add_user(username, password, name=""):
    """Tambah pengguna baru"""
    st.session_state.users[username] = {
        'password': password,
        'name': name if name else username
    }
    return True

# ============================================
# HALAMAN LOGIN SEDERHANA
# ============================================

def show_login_page():
    """Tampilkan halaman login"""
    
    # Header
    st.markdown('<h1 class="main-title">🔬 NaNote</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #4B5563;">Aplikasi Catatan Praktikum & Kalkulator PSA</p>', unsafe_allow_html=True)
    
    # Container login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="color: #1E3A8A;">Login</h3>', unsafe_allow_html=True)
        
        # Tab pilihan
        tab1, tab2 = st.tabs(["Masuk", "Buat Akun"])
        
        with tab1:
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            # Tombol login
            if st.button("Login"):
                if not username or not password:
                    st.error("Username dan password harus diisi")
                elif check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_info = st.session_state.users[username]
                    st.success(f"Selamat datang, {username}!")
                    st.rerun()
                else:
                    st.error("Username atau password salah")
            
            # Info akun demo
            st.markdown("---")
            st.markdown("**Akun untuk mencoba:**")
            st.code("Username: demo\nPassword: demo123")
            st.markdown("")
            st.code("Username: admin\nPassword: admin123")
        
        with tab2:
            new_user = st.text_input("Username Baru", placeholder="Pilih username")
            new_pass = st.text_input("Password Baru", type="password", placeholder="Pilih password")
            confirm_pass = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
            full_name = st.text_input("Nama Lengkap (opsional)", placeholder="Nama Anda")
            
            if st.button("Daftar"):
                if not new_user or not new_pass:
                    st.error("Username dan password harus diisi")
                elif len(new_user) < 3:
                    st.error("Username minimal 3 karakter")
                elif len(new_pass) < 4:
                    st.error("Password minimal 4 karakter")
                elif new_pass != confirm_pass:
                    st.error("Password tidak cocok")
                elif new_user in st.session_state.users:
                    st.error("Username sudah digunakan")
                else:
                    add_user(new_user, new_pass, full_name)
                    st.success(f"Akun {new_user} berhasil dibuat! Silakan login.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('<p style="text-align: center; color: #6B7280;">🔬 NaNote - Catatan Praktikum & Kalkulasi PSA</p>', unsafe_allow_html=True)

# ============================================
# APLIKASI UTAMA (Sederhana)
# ============================================

def main_app():
    """Aplikasi utama setelah login"""
    
    # Sidebar
    with st.sidebar:
        st.title("🔬 NaNote")
        st.markdown(f"**User:** {st.session_state.username}")
        
        if 'user_info' in st.session_state and 'name' in st.session_state.user_info:
            st.markdown(f"*{st.session_state.user_info['name']}*")
        
        st.markdown("---")
        
        # Menu
        menu = st.radio(
            "Menu:",
            ["🏠 Beranda", "📝 Catatan", "🧮 Kalkulasi", "📊 Data", "ℹ️ Info", "🚪 Logout"]
        )
    
    # Konten utama
    if menu == "🏠 Beranda":
        st.markdown("# 🔬 Selamat Datang di NaNote")
        st.markdown("Aplikasi untuk mencatat praktikum dan menghitung PSA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("**Fitur Utama:**")
            st.markdown("- 📝 Catatan praktikum")
            st.markdown("- 🧮 Kalkulasi PSA")
            st.markdown("- 📊 Analisis data")
            st.markdown("- 💾 Simpan data lokal")
        
        with col2:
            st.info("**Instruksi:**")
            st.markdown("1. Pilih menu di sidebar")
            st.markdown("2. Buat catatan atau hitung PSA")
            st.markdown("3. Simpan hasil kerja Anda")
            st.markdown("4. Logout setelah selesai")
    
    elif menu == "📝 Catatan":
        st.markdown("# 📝 Buat Catatan Praktikum")
        
        with st.form("catatan_form"):
            judul = st.text_input("Judul Catatan")
            tanggal = st.date_input("Tanggal")
            isi = st.text_area("Isi Catatan", height=200)
            
            if st.form_submit_button("Simpan"):
                if judul and isi:
                    # Simpan di session state
                    if 'catatan' not in st.session_state:
                        st.session_state.catatan = []
                    
                    catatan_baru = {
                        'id': len(st.session_state.catatan) + 1,
                        'judul': judul,
                        'tanggal': str(tanggal),
                        'isi': isi,
                        'user': st.session_state.username,
                        'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.session_state.catatan.append(catatan_baru)
                    st.success(f"Catatan '{judul}' berhasil disimpan!")
                else:
                    st.error("Judul dan isi catatan harus diisi")
        
        # Daftar catatan
        if 'catatan' in st.session_state and st.session_state.catatan:
            st.markdown("### 📚 Catatan Tersimpan")
            for cat in st.session_state.catatan:
                if cat['user'] == st.session_state.username:
                    with st.expander(f"{cat['judul']} - {cat['tanggal']}"):
                        st.markdown(f"**Dibuat oleh:** {cat['user']}")
                        st.markdown(f"**Waktu:** {cat['waktu']}")
                        st.markdown(cat['isi'])
    
    elif menu == "🧮 Kalkulasi":
        st.markdown("# 🧮 Kalkulasi PSA")
        
        st.info("Masukkan data untuk kalkulasi PSA (Particle Size Analysis)")
        
        # Input data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pdi = st.number_input("PDI", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
        
        with col2:
            vol = st.number_input("% Volume", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        
        with col3:
            diameter = st.number_input("Diameter (nm)", min_value=0.1, value=50.0, step=1.0)
        
        # Tombol hitung
        if st.button("Hitung Hasil"):
            try:
                # Perhitungan sederhana
                if vol == 0:
                    st.error("Volume tidak boleh 0")
                else:
                    # Simulasi perhitungan
                    hasil = {
                        'diameter_rata': diameter,
                        'pdi_rata': pdi,
                        'kualitas': "Baik" if pdi < 0.2 else "Cukup" if pdi < 0.3 else "Kurang",
                        'warna': "green" if pdi < 0.2 else "orange" if pdi < 0.3 else "red"
                    }
                    
                    # Tampilkan hasil
                    st.markdown("### 📊 Hasil Kalkulasi")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Diameter Rata-rata", f"{hasil['diameter_rata']:.2f} nm")
                    with col2:
                        st.metric("PDI Rata-rata", f"{hasil['pdi_rata']:.3f}")
                    with col3:
                        warna = hasil['warna']
                        st.markdown(f"<h3 style='color:{warna};'>Kualitas: {hasil['kualitas']}</h3>", unsafe_allow_html=True)
                    
                    # Simpan hasil
                    if 'psa_data' not in st.session_state:
                        st.session_state.psa_data = []
                    
                    hasil_data = {
                        'id': len(st.session_state.psa_data) + 1,
                        'user': st.session_state.username,
                        'pdi': pdi,
                        'vol': vol,
                        'diameter': diameter,
                        'hasil': hasil,
                        'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.session_state.psa_data.append(hasil_data)
                    st.success("Hasil berhasil disimpan!")
            
            except Exception as e:
                st.error(f"Error dalam perhitungan: {str(e)}")
    
    elif menu == "📊 Data":
        st.markdown("# 📊 Data Tersimpan")
        
        # Data catatan
        if 'catatan' in st.session_state and st.session_state.catatan:
            st.markdown("### Catatan Praktikum")
            catatan_user = [c for c in st.session_state.catatan if c['user'] == st.session_state.username]
            
            if catatan_user:
                for cat in catatan_user:
                    st.markdown(f"**{cat['judul']}** ({cat['tanggal']})")
                    st.caption(f"Dibuat: {cat['waktu']}")
            else:
                st.info("Belum ada catatan")
        else:
            st.info("Belum ada catatan")
        
        # Data PSA
        if 'psa_data' in st.session_state and st.session_state.psa_data:
            st.markdown("### Hasil PSA")
            psa_user = [p for p in st.session_state.psa_data if p['user'] == st.session_state.username]
            
            if psa_user:
                for psa in psa_user:
                    with st.expander(f"PSA #{psa['id']} - {psa['waktu']}"):
                        st.markdown(f"PDI: {psa['pdi']}")
                        st.markdown(f"%Vol: {psa['vol']}")
                        st.markdown(f"Diameter: {psa['diameter']} nm")
                        st.markdown(f"Kualitas: {psa['hasil']['kualitas']}")
            else:
                st.info("Belum ada data PSA")
        else:
            st.info("Belum ada data PSA")
    
    elif menu == "ℹ️ Info":
        st.markdown("# ℹ️ Informasi Aplikasi")
        
        st.markdown("""
        ## Tentang NaNote
        
        NaNote adalah aplikasi sederhana untuk:
        - Mencatat hasil praktikum nanomaterial
        - Melakukan kalkulasi PSA (Particle Size Analysis)
        - Menyimpan data secara lokal
        
        ## Cara Menggunakan
        
        1. **Buat Catatan**: Menu "📝 Catatan"
           - Isi judul, tanggal, dan isi catatan
           - Klik "Simpan" untuk menyimpan
        
        2. **Kalkulasi PSA**: Menu "🧮 Kalkulasi"
           - Masukkan data PDI, %Volume, dan Diameter
           - Klik "Hitung Hasil" untuk melihat hasil
        
        3. **Lihat Data**: Menu "📊 Data"
           - Lihat semua catatan dan hasil kalkulasi
        
        ## Interpretasi PDI
        
        - **PDI < 0.2**: Baik
        - **PDI 0.2-0.3**: Cukup
        - **PDI > 0.3**: Kurang
        
        ## Keamanan
        
        - Data disimpan di session state browser
        - Data akan hilang jika browser ditutup
        - Untuk penyimpanan permanen, ekspor data secara manual
        
        ## Pengembang
        
        Aplikasi ini dikembangkan untuk keperluan praktikum nanomaterial.
        """)
    
    elif menu == "🚪 Logout":
        st.markdown("# 🚪 Logout")
        
        st.warning("Apakah Anda yakin ingin logout?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Ya, Logout"):
                st.session_state.logged_in = False
                if 'username' in st.session_state:
                    del st.session_state.username
                st.success("Logout berhasil!")
                st.rerun()
        
        with col2:
            if st.button("Tidak, Kembali"):
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(f'<p style="text-align: center; color: #6B7280;">🔬 NaNote • User: {st.session_state.username} • {datetime.now().year}</p>', unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================

def main():
    """Fungsi utama aplikasi"""
    
    # Inisialisasi status login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Tampilkan halaman sesuai status
    if not st.session_state.logged_in:
        show_login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
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
</style>
""", unsafe_allow_html=True)

# Inisialisasi session state
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

# Sidebar
with st.sidebar:
    st.image("https://i.pinimg.com/1200x/8b/06/a8/8b06a832394c6d214729546d6888d0d0.jpg", width=80)
    st.title("NaNote")
    st.markdown("**Catatan & Kalkulator PSA**")
    
    st.markdown("---")
    
    menu = st.radio(
        "Pilih Menu:",
        ["🏠 Beranda", "📝 Catatan Praktikum", "🧮 Kalkulasi PSA", "📊 Data Tersimpan", "ℹ️ Panduan"]
    )
    
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
            <ul>
                <li>Editor teks lengkap</li>
                <li>Template otomatis</li>
                <li>Simpan sebagai .docx</li>
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
            </ul>
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
        - Penyimpanan lokal
        """)
    
    with col2:
        st.markdown("""
        **Untuk Kalkulasi PSA:**
        - Input data PDI, %vol, diameter
        - Perhitungan rata-rata berbobot
        - Analisis distribusi ukuran
        - Penilaian kualitas nanomaterial
        - Ekspor ke PDF profesional
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
                        'id': len(st.session_state.catatan_list) + 1,
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
                        },
                        'waktu_buat': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.session_state.catatan_list.append(catatan_data)
                    st.session_state.current_note = catatan_data
                    st.session_state.show_download = True
                    
                    st.success("✅ Catatan berhasil disimpan!")
                    
                    # Tampilkan preview
                    with st.expander("Preview Catatan", expanded=True):
                        st.markdown(f"**Judul:** {judul}")
                        st.markdown(f"**Praktikan:** {praktikan} | **Tanggal:** {tanggal}")
                        st.markdown("---")
                        st.markdown(f"**Tujuan:**\n{tujuan}")
                        st.markdown(f"**Alat dan Bahan:**\n{alat_bahan}")
                        st.markdown(f"**Prosedur:**\n{prosedur}")
                        st.markdown(f"**Hasil:**\n{hasil}")
        
        # TOMBOL DOWNLOAD DIPINDAHKAN DI SINI (DI LUAR FORM)
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
        if not st.session_state.catatan_list:
            st.info("📝 Belum ada catatan yang disimpan.")
        else:
            st.markdown(f"### 📚 Catatan Tersimpan ({len(st.session_state.catatan_list)})")
            
            for idx, catatan in enumerate(st.session_state.catatan_list):
                with st.expander(f"{catatan['judul']} - {catatan['tanggal']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                        st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
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
                            file_name=f"catatan_{catatan['judul'].replace(' ', '_')}_{catatan['tanggal']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"download_{idx}"
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
                st.session_state.current_psa = {
                    'hasil': hasil,
                    'data_input': data_input,
                    'pdi_list': pdi_list,
                    'vol_list': vol_list,
                    'diameter_list': diameter_list
                }
                
                # Simpan ke history
                st.session_state.psa_data.append({
                    'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'hasil': hasil,
                    'data_count': len(data_input)
                })
                
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
            if st.session_state.catatan_list:
                st.markdown("---")
                st.markdown("### 💾 Simpan ke Catatan")
                
                catatan_options = {cat['judul']: idx for idx, cat in enumerate(st.session_state.catatan_list)}
                selected_note = st.selectbox(
                    "Pilih Catatan untuk Menyimpan Hasil PSA:",
                    ["Pilih..."] + list(catatan_options.keys())
                )
                
                if selected_note != "Pilih..." and st.button("💾 Simpan ke Catatan"):
                    idx = catatan_options[selected_note]
                    st.session_state.catatan_list[idx]['data_psa'] = {
                        'diameter_rata': hasil['diameter_rata'],
                        'pdi_rata': hasil['pdi_rata'],
                        'kualitas': hasil['kualitas'],
                        'total_vol': hasil['total_vol']
                    }
                    st.success(f"✅ Hasil PSA berhasil disimpan ke catatan '{selected_note}'!")

elif menu == "📊 Data Tersimpan":
    st.markdown('<h2 class="section-header">📊 Data Tersimpan</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Catatan Praktikum", "Hasil PSA"])
    
    with tab1:
        if not st.session_state.catatan_list:
            st.info("📝 Belum ada catatan yang disimpan.")
        else:
            st.markdown(f"### Total Catatan: {len(st.session_state.catatan_list)}")
            
            for idx, catatan in enumerate(st.session_state.catatan_list):
                with st.expander(f"{catatan['judul']} ({catatan['tanggal']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Praktikan:** {catatan['praktikan']}")
                        st.markdown(f"**Mata Praktikum:** {catatan['mata_praktikum']}")
                        st.markdown(f"**Dibuat:** {catatan['waktu_buat']}")
                        
                        if 'data_psa' in catatan:
                            st.markdown("---")
                            st.markdown("**Data PSA Terkait:**")
                            for key, value in catatan['data_psa'].items():
                                st.markdown(f"- {key}: {value}")
                    
                    with col2:
                        # Tombol download
                        doc = buat_file_word(catatan)
                        doc_buffer = io.BytesIO()
                        doc.save(doc_buffer)
                        doc_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Word",
                            data=doc_buffer,
                            file_name=f"catatan_{catatan['judul'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"word_download_{idx}"
                        )
            
            # Tombol ekspor semua
            if st.button("📤 Ekspor Semua Data", use_container_width=True):
                all_data = {
                    'catatan': st.session_state.catatan_list,
                    'psa_data': st.session_state.psa_data,
                    'export_time': datetime.now().isoformat()
                }
                
                st.download_button(
                    label="📄 Download Word Backup",
                    data=doc_buffer,
                    file_name=f"nanote_backup_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="word_backup_download"
                )
    
    with tab2:
        if not st.session_state.psa_data:
            st.info("🧮 Belum ada hasil PSA yang disimpan.")
        else:
            st.markdown(f"### Total Hasil PSA: {len(st.session_state.psa_data)}")
            
            for idx, psa in enumerate(st.session_state.psa_data):
                with st.expander(f"Perhitungan {idx+1} - {psa['waktu']}"):
                    st.markdown(f"**Waktu:** {psa['waktu']}")
                    st.markdown(f"**Jumlah Data:** {psa['data_count']}")
                    st.markdown(f"**Diameter Rata-rata:** {psa['hasil']['diameter_rata']:.2f} nm")
                    st.markdown(f"**PDI Rata-rata:** {psa['hasil']['pdi_rata']:.3f}")
                    st.markdown(f"**Kualitas:** {psa['hasil']['kualitas']}")

else:  # Panduan
    st.markdown('<h2 class="section-header">ℹ️ Panduan Penggunaan</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📚 Tentang NaNote
    
    NaNote adalah aplikasi web yang dirancang khusus untuk membantu praktikan dalam:
    1. **Mencatat hasil praktikum** nanomaterial secara digital
    2. **Menganalisis data PSA** (Particle Size Analysis)
    3. **Menyimpan dan mengekspor** hasil dalam format standar
    
    ### 🔎 Cara Menggunakan
    
    #### 1. Catatan Praktikum
    - Buka menu **"📝 Catatan Praktikum"**
    - Isi form dengan data lengkap praktikum
    - Simpan catatan dan download sebagai file Word (.docx)
    
    #### 2. Kalkulator PSA
    - Buka menu **"🧮 Kalkulator PSA"**
    - Input data PDI, %vol, dan diameter untuk setiap partikel
    - Klik "Hitung Hasil PSA"
    - Lihat hasil di tab "Hasil Perhitungan"
    - Download hasil sebagai PDF
    
    #### 3. Data Tersimpan
    - Buka menu **"📊 Data Tersimpan"**
    - Lihat semua catatan dan hasil perhitungan yang telah disimpan
    - Ekspor data backup jika diperlukan
    
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
    
    ### 💡 Tips
    1. Simpan catatan segera setelah praktikum selesai
    2. Periksa konsistensi data sebelum menghitung PSA
    3. Gunakan ekspor PDF untuk laporan formal
    4. Backup data penting secara berkala
    
    ### 🛠️ Teknologi
    - **Framework**: Streamlit (Python)
    - **Format Ekspor**: .docx, .pdf
    - **Deployment**: Streamlit Cloud
    - **Bahasa**: Indonesia
    
    ### 🤝 Kontribusi
    Aplikasi ini bersifat open source. Untuk saran dan masukan, silakan buat issue di repository GitHub.
    """)

# Footer
st.markdown("---")
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("🔬 **NaNote** • Aplikasi Catatan Praktikum & Kalkulasi PSA • Dibuat oleh Kelompok 3 Logika dan Pemrograman Komputer")
st.markdown(f"© {datetime.now().year}")
st.markdown('</div>', unsafe_allow_html=True)
