import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import tempfile
import os
import base64
from io import BytesIO
import json
from utils.word_exporter import create_word_note
from utils.pdf_exporter import create_psa_report

# =================== KONFIGURASI APLIKASI ===================
st.set_page_config(
    page_title="NaNote - Catatan & Kalkulator PSA Nanomaterial",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================== CSS KUSTOM NANOTE ===================
st.markdown("""
<style>
    /* PALET WARNA NANOTE */
    :root {
        --primary: #2E86AB;
        --secondary: #A23B72;
        --accent: #F18F01;
        --success: #2E8B57;
        --light: #F8F9FA;
        --dark: #212529;
    }
    
    /* HEADER UTAMA */
    .nanote-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(46, 134, 171, 0.3);
    }
    
    .nanote-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
    }
    
    .nanote-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* CARD STYLE */
    .nanote-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid var(--primary);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
        transition: transform 0.3s ease;
    }
    
    .nanote-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    /* BUTTON STYLE */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 134, 171, 0.4);
    }
    
    /* METRIC CARD */
    .metric-card {
        background: linear-gradient(135deg, var(--primary) 0%, #3B9AB2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    /* SIDEBAR */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, var(--primary) 0%, var(--dark) 100%);
    }
    
    /* TAB STYLE */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--light);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* SUCCESS MESSAGE */
    .stAlert {
        border-radius: 10px;
    }
    
    /* DATA EDITOR */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# =================== INISIALISASI SESSION STATE ===================
def init_session_state():
    """Inisialisasi semua session state"""
    defaults = {
        'catatan_list': [],
        'psa_results': [],
        'current_page': "beranda",
        'edit_mode': False,
        'edit_index': None,
        'data_input_mode': 'manual',
        'psa_data': None,
        'user_prefs': {'theme': 'light', 'language': 'id'}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =================== FUNGSI UTILITAS ===================
def save_to_json(filename, data):
    """Menyimpan data ke file JSON"""
    try:
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_from_json(filename):
    """Memuat data dari file JSON"""
    try:
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def set_page(page_name):
    """Navigasi antar halaman"""
    st.session_state.current_page = page_name
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

def create_sample_psa_data(num_points=8):
    """Membuat data PSA contoh"""
    np.random.seed(42)
    diameters = np.sort(np.random.normal(50, 15, num_points))
    diameters = np.clip(diameters, 5, 150)
    
    # Distribusi normal untuk volume
    volumes = np.exp(-(diameters - diameters.mean())**2 / (2 * (diameters.std()**2)))
    volumes = volumes / volumes.sum() * 100
    
    # PDI meningkat dengan deviasi diameter
    pdis = 0.05 + (np.abs(diameters - diameters.mean()) / diameters.max()) * 0.25
    
    return pd.DataFrame({
        'Diameter (nm)': np.round(diameters, 2),
        '% Volume': np.round(volumes, 2),
        'PDI': np.round(pdis, 3)
    })

# =================== SIDEBAR ===================
with st.sidebar:
    # Logo NaNote
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: white; font-size: 2rem; margin: 0;">🔬 NaNote</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">Catatan & Kalkulator PSA</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Menu Navigasi
    menu_items = {
        "🏠 Beranda": "beranda",
        "📝 Catatan Baru": "catatan_baru",
        "📚 Catatan Tersimpan": "catatan_simpan",
        "🧮 Kalkulator PSA": "kalkulator_psa",
        "📊 Hasil PSA": "hasil_psa",
        "📁 Ekspor Data": "ekspor_data",
        "⚙️ Panduan": "panduan"
    }
    
    for label, page in menu_items.items():
        if st.button(label, use_container_width=True, 
                    type="primary" if st.session_state.current_page == page else "secondary"):
            set_page(page)
    
    st.divider()
    
    # Statistik Cepat
    st.markdown("### 📊 Statistik")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Catatan", len(st.session_state.catatan_list))
    with col_stat2:
        st.metric("PSA", len(st.session_state.psa_results))
    
    st.divider()
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset Data", use_container_width=True):
        st.session_state.catatan_list = []
        st.session_state.psa_results = []
        st.success("Data berhasil direset!")
        st.rerun()
    
    st.divider()
    
    # Info Versi
    st.caption("**NaNote v1.0**")
    st.caption("© 2024 Lab Nanomaterial")

# =================== HALAMAN BERANDA ===================
if st.session_state.current_page == "beranda":
    # Header
    st.markdown("""
    <div class="nanote-header">
        <h1 class="nanote-title">NaNote</h1>
        <p class="nanote-subtitle">Catatan Praktik & Kalkulator PSA Nanomaterial</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    col_intro1, col_intro2 = st.columns([2, 1])
    
    with col_intro1:
        st.markdown("""
        ### Selamat Datang di NaNote! 🎉
        
        **NaNote** adalah aplikasi web yang dirancang khusus untuk membantu Anda dalam:
        
        🔬 **Pencatatan Praktik Nanomaterial**
        - Mencatat seluruh proses sintesis
        - Menyimpan parameter eksperimen
        - Dokumentasi visual hasil
        
        📊 **Analisis Particle Size (PSA)**
        - Kalkulasi distribusi ukuran partikel
        - Analisis statistik lengkap
        - Visualisasi data interaktif
        
        📁 **Manajemen & Ekspor Data**
        - Simpan catatan dalam format Word
        - Ekspor hasil PSA ke PDF
        - Organisasi data terstruktur
        """)
    
    with col_intro2:
        st.image("https://img.icons8.com/color/300/000000/microscope.png", 
                caption="Platform Nanomaterial Digital")
    
    # Quick Start Cards
    st.markdown("### 🚀 Mulai Cepat")
    
    col_start1, col_start2, col_start3 = st.columns(3)
    
    with col_start1:
        with st.container():
            st.markdown("""
            <div class="nanote-card">
                <h4>📝 Catatan Baru</h4>
                <p>Mulai mencatat praktik nanomaterial Anda dengan form lengkap.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Buat Catatan →", key="btn_catatan", use_container_width=True):
                set_page("catatan_baru")
    
    with col_start2:
        with st.container():
            st.markdown("""
            <div class="nanote-card">
                <h4>🧮 Kalkulator PSA</h4>
                <p>Hitung distribusi ukuran partikel dengan data PDI dan % Volume.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Hitung PSA →", key="btn_psa", use_container_width=True):
                set_page("kalkulator_psa")
    
    with col_start3:
        with st.container():
            st.markdown("""
            <div class="nanote-card">
                <h4>📚 Lihat Data</h4>
                <p>Akses catatan dan hasil PSA yang telah Anda simpan.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Data Tersimpan →", key="btn_data", use_container_width=True):
                set_page("catatan_simpan")
    
    # Fitur Unggulan
    st.markdown("### ✨ Fitur Unggulan NaNote")
    
    col_feat1, col_feat2 = st.columns(2)
    
    with col_feat1:
        st.markdown("""
        #### 📝 **Sistem Pencatatan Cerdas**
        
        • **Form Terstruktur**: Input data praktik dengan kategori lengkap
        • **Parameter Detail**: Suhu, waktu, pH, konsentrasi, dan lainnya
        • **Upload Gambar**: Dokumentasi visual hasil sintesis
        • **Auto-Save**: Data tersimpan otomatis dalam session
        • **Template Profesional**: Ekspor ke Word dengan format standar lab
        """)
    
    with col_feat2:
        st.markdown("""
        #### 📊 **Kalkulator PSA Akurat**
        
        • **Input Fleksibel**: Manual atau upload file Excel/CSV
        • **Analisis Statistik**: Mean, median, PDI, variance, std dev
        • **Visualisasi**: Grafik distribusi interaktif dengan Plotly
        • **Klasifikasi Otomatis**: Grade kualitas berdasarkan PDI
        • **Laporan PDF**: Ekspor hasil dengan grafik dan tabel
        """)
    
    # Recent Activity
    if st.session_state.catatan_list or st.session_state.psa_results:
        st.markdown("### 📈 Aktivitas Terkini")
        
        tab_act1, tab_act2 = st.tabs(["📝 Catatan Terbaru", "📊 Hasil PSA"])
        
        with tab_act1:
            if st.session_state.catatan_list:
                recent_notes = list(reversed(st.session_state.catatan_list))[:3]
                for note in recent_notes:
                    with st.expander(f"**{note.get('judul', 'Catatan')}** - {note.get('tanggal', '')}"):
                        st.write(f"**Praktikan:** {note.get('nama_praktikan', '')}")
                        st.write(f"**Material:** {note.get('jenis_nanomaterial', '')}")
                        st.write(f"**Metode:** {note.get('metode_sintesis', '')}")
            else:
                st.info("Belum ada catatan praktik")
        
        with tab_act2:
            if st.session_state.psa_results:
                recent_psa = list(reversed(st.session_state.psa_results))[:3]
                for psa in recent_psa:
                    with st.expander(f"**PSA** - {psa.get('timestamp', '')}"):
                        st.write(f"**Diameter Rata-rata:** {psa.get('diameter_rerata', 0):.2f} nm")
                        st.write(f"**PDI:** {psa.get('pdi_terhitung', 0):.3f}")
                        st.write(f"**Klasifikasi:** {psa.get('klasifikasi', '')}")
            else:
                st.info("Belum ada hasil PSA")

# =================== HALAMAN CATATAN BARU ===================
elif st.session_state.current_page == "catatan_baru":
    st.markdown("## 📝 Catatan Praktik Baru")
    
    with st.form("form_catatan_praktik", clear_on_submit=True):
        st.markdown("### Informasi Dasar")
        
        col_basic1, col_basic2 = st.columns(2)
        
        with col_basic1:
            judul = st.text_input("Judul Praktik*", placeholder="Sintesis Nanopartikel...")
            nama_praktikan = st.text_input("Nama Praktikan*", placeholder="Nama lengkap")
            tanggal = st.date_input("Tanggal Praktik*", datetime.now())
        
        with col_basic2:
            institusi = st.text_input("Institusi/Laboratorium", placeholder="Universitas/Lab")
            kelompok = st.text_input("Kelompok/Shift", placeholder="Kelompok A/Shift 1")
            supervisor = st.text_input("Supervisor/Pembimbing", placeholder="Nama supervisor")
        
        st.divider()
        st.markdown("### Spesifikasi Nanomaterial")
        
        col_nano1, col_nano2 = st.columns(2)
        
        with col_nano1:
            jenis_nanomaterial = st.selectbox(
                "Jenis Nanomaterial*",
                ["TiO₂ (Titanium Dioxide)", "SiO₂ (Silicon Dioxide)", "ZnO (Zinc Oxide)", 
                 "Ag (Silver Nanoparticles)", "Au (Gold Nanoparticles)", "Fe₃O₄ (Magnetite)",
                 "Al₂O₃ (Alumina)", "Lainnya"]
            )
            if jenis_nanomaterial == "Lainnya":
                jenis_nanomaterial = st.text_input("Sebutkan jenis nanomaterial")
        
        with col_nano2:
            metode_sintesis = st.selectbox(
                "Metode Sintesis*",
                ["Sol-Gel", "Hidrotermal", "Sonokimia", "Mekanokimia", 
                 "Chemical Vapor Deposition", "Co-precipitation", "Lainnya"]
            )
            if metode_sintesis == "Lainnya":
                metode_sintesis = st.text_input("Sebutkan metode sintesis")
        
        st.divider()
        st.markdown("### Parameter Sintesis")
        
        col_param1, col_param2, col_param3 = st.columns(3)
        
        with col_param1:
            suhu = st.number_input("Suhu (°C)*", min_value=-273.0, max_value=2000.0, value=25.0)
            waktu = st.number_input("Waktu (jam)*", min_value=0.0, max_value=500.0, value=1.0)
        
        with col_param2:
            tekanan = st.number_input("Tekanan (atm)", min_value=0.0, max_value=1000.0, value=1.0)
            ph = st.slider("pH Larutan", 0.0, 14.0, 7.0, 0.1)
        
        with col_param3:
            konsentrasi = st.number_input("Konsentrasi (mg/mL)*", min_value=0.0, value=1.0, step=0.01)
            pelarut = st.text_input("Pelarut*", value="Aquades")
        
        st.divider()
        st.markdown("### Prosedur & Hasil")
        
        prosedur = st.text_area(
            "Prosedur Praktik*",
            height=150,
            placeholder="Tuliskan langkah-langkah sintesis secara detail..."
        )
        
        hasil_pengamatan = st.text_area(
            "Hasil Pengamatan*",
            height=150,
            placeholder="Deskripsikan hasil yang diperoleh (warna, tekstur, karakteristik)..."
        )
        
        st.markdown("### Dokumentasi (Opsional)")
        uploaded_image = st.file_uploader(
            "Upload gambar hasil sintesis", 
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=False
        )
        
        st.divider()
        
        submitted = st.form_submit_button("💾 Simpan Catatan", type="primary")
        
        if submitted:
            if judul and nama_praktikan and prosedur and hasil_pengamatan:
                # Simpan gambar jika ada
                image_path = None
                if uploaded_image:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(uploaded_image.getvalue())
                        image_path = tmp.name
                
                catatan = {
                    'id': len(st.session_state.catatan_list) + 1,
                    'judul': judul,
                    'nama_praktikan': nama_praktikan,
                    'tanggal': str(tanggal),
                    'institusi': institusi,
                    'kelompok': kelompok,
                    'supervisor': supervisor,
                    'jenis_nanomaterial': jenis_nanomaterial,
                    'metode_sintesis': metode_sintesis,
                    'suhu': suhu,
                    'waktu': waktu,
                    'tekanan': tekanan,
                    'ph': ph,
                    'konsentrasi': konsentrasi,
                    'pelarut': pelarut,
                    'prosedur': prosedur,
                    'hasil_pengamatan': hasil_pengamatan,
                    'image_path': image_path,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'tipe': 'catatan_praktik'
                }
                
                st.session_state.catatan_list.append(catatan)
                save_to_json('nanote_catatan.json', st.session_state.catatan_list)
                
                st.success("✅ Catatan berhasil disimpan!")
                st.balloons()
                
                # Tampilkan preview
                with st.expander("👁️ Preview Catatan"):
                    col_preview1, col_preview2 = st.columns(2)
                    with col_preview1:
                        st.write(f"**Judul:** {judul}")
                        st.write(f"**Praktikan:** {nama_praktikan}")
                        st.write(f"**Tanggal:** {tanggal}")
                        st.write(f"**Material:** {jenis_nanomaterial}")
                    with col_preview2:
                        st.write(f"**Metode:** {metode_sintesis}")
                        st.write(f"**Suhu:** {suhu}°C")
                        st.write(f"**Waktu:** {waktu} jam")
                        st.write(f"**pH:** {ph}")
                
                if st.button("📥 Ekspor ke Word"):
                    try:
                        doc_path = create_word_note(catatan)
                        with open(doc_path, 'rb') as f:
                            doc_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Dokumen Word",
                            data=doc_data,
                            file_name=f"Catatan_{judul[:20]}_{tanggal}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            else:
                st.error("❌ Harap isi semua field yang wajib (*)!")

# =================== HALAMAN CATATAN TERSIMPAN ===================
elif st.session_state.current_page == "catatan_simpan":
    st.markdown("## 📚 Catatan Praktik Tersimpan")
    
    if not st.session_state.catatan_list:
        st.info("📭 Belum ada catatan yang disimpan. Mulai dengan membuat catatan baru!")
    else:
        # Filter dan Pencarian
        col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
        
        with col_filter1:
            search_term = st.text_input("🔍 Cari catatan...", placeholder="Judul atau nama praktikan")
        
        with col_filter2:
            filter_material = st.multiselect(
                "Filter berdasarkan material",
                options=list(set([c.get('jenis_nanomaterial', '') for c in st.session_state.catatan_list])),
                default=[]
            )
        
        with col_filter3:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Filter data
        filtered_notes = st.session_state.catatan_list
        
        if search_term:
            filtered_notes = [
                n for n in filtered_notes
                if search_term.lower() in n.get('judul', '').lower()
                or search_term.lower() in n.get('nama_praktikan', '').lower()
            ]
        
        if filter_material:
            filtered_notes = [
                n for n in filtered_notes
                if n.get('jenis_nanomaterial', '') in filter_material
            ]
        
        st.markdown(f"**📊 Menampilkan {len(filtered_notes)} dari {len(st.session_state.catatan_list)} catatan**")
        
        # Tampilkan catatan
        for idx, catatan in enumerate(filtered_notes):
            with st.container():
                col_note1, col_note2 = st.columns([3, 1])
                
                with col_note1:
                    with st.expander(f"**{catatan.get('judul', 'Catatan')}** - {catatan.get('tanggal', '')}", expanded=False):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**Praktikan:** {catatan.get('nama_praktikan', '')}")
                            st.write(f"**Institusi:** {catatan.get('institusi', '-')}")
                            st.write(f"**Material:** {catatan.get('jenis_nanomaterial', '')}")
                            st.write(f"**Metode:** {catatan.get('metode_sintesis', '')}")
                        
                        with col_info2:
                            st.write(f"**Suhu:** {catatan.get('suhu', '')}°C")
                            st.write(f"**Waktu:** {catatan.get('waktu', '')} jam")
                            st.write(f"**pH:** {catatan.get('ph', '')}")
                            st.write(f"**Konsentrasi:** {catatan.get('konsentrasi', '')} mg/mL")
                        
                        # Tampilkan gambar jika ada
                        if catatan.get('image_path') and os.path.exists(catatan['image_path']):
                            try:
                                st.image(catatan['image_path'], caption="Gambar Hasil Sintesis", width=300)
                            except:
                                pass
                
                with col_note2:
                    # Tombol aksi
                    original_idx = st.session_state.catatan_list.index(catatan)
                    
                    if st.button("📥 Word", key=f"word_{original_idx}", use_container_width=True):
                        try:
                            doc_path = create_word_note(catatan)
                            with open(doc_path, 'rb') as f:
                                doc_data = f.read()
                            
                            st.download_button(
                                label="Download",
                                data=doc_data,
                                file_name=f"Catatan_{catatan['judul'][:20]}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_{original_idx}"
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    if st.button("🗑️ Hapus", key=f"del_{original_idx}", use_container_width=True):
                        # Hapus file gambar jika ada
                        if catatan.get('image_path') and os.path.exists(catatan['image_path']):
                            try:
                                os.remove(catatan['image_path'])
                            except:
                                pass
                        
                        st.session_state.catatan_list.pop(original_idx)
                        save_to_json('nanote_catatan.json', st.session_state.catatan_list)
                        st.success("Catatan berhasil dihapus!")
                        st.rerun()
        
        # Ekspor semua
        st.divider()
        if st.button("📦 Ekspor Semua Catatan ke Word", use_container_width=True):
            st.info("Fitur ekspor batch sedang dikembangkan...")

# =================== HALAMAN KALKULATOR PSA ===================
elif st.session_state.current_page == "kalkulator_psa":
    st.markdown("## 🧮 Kalkulator PSA Nanomaterial")
    
    # Pilihan mode input
    input_mode = st.radio(
        "Pilih mode input data:",
        ["📝 Input Manual", "📁 Upload File Excel/CSV"],
        horizontal=True
    )
    
    if input_mode == "📁 Upload File Excel/CSV":
        uploaded_file = st.file_uploader(
            "Upload file data PSA",
            type=['xlsx', 'xls', 'csv'],
            help="File harus memiliki kolom: 'Diameter (nm)', '% Volume', 'PDI'"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Validasi kolom
                required = ['Diameter (nm)', '% Volume', 'PDI']
                if all(col in df.columns for col in required):
                    st.session_state.psa_data = df[required].copy()
                    st.success(f"✅ File berhasil diupload! {len(df)} data ditemukan.")
                else:
                    st.error("❌ File harus mengandung kolom: 'Diameter (nm)', '% Volume', 'PDI'")
            except Exception as e:
                st.error(f"❌ Error membaca file: {str(e)}")
    
    # Input manual
    else:
        col_input1, col_input2 = st.columns([2, 1])
        
        with col_input1:
            num_points = st.number_input(
                "Jumlah titik data:",
                min_value=3,
                max_value=50,
                value=8,
                step=1
            )
        
        with col_input2:
            st.write("")
            st.write("")
            if st.button("🔄 Generate Data Contoh"):
                st.session_state.psa_data = create_sample_psa_data(num_points)
                st.success("Data contoh berhasil dibuat!")
    
    # Tampilkan editor data
    if st.session_state.psa_data is not None and not st.session_state.psa_data.empty:
        st.markdown("### 📊 Data PSA")
        
        edited_df = st.data_editor(
            st.session_state.psa_data,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Diameter (nm)": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0.1,
                    max_value=10000.0
                ),
                "% Volume": st.column_config.NumberColumn(
                    format="%.2f",
                    min_value=0.0,
                    max_value=100.0
                ),
                "PDI": st.column_config.NumberColumn(
                    format="%.3f",
                    min_value=0.001,
                    max_value=1.0
                )
            }
        )
        
        # Validasi total volume
        total_volume = edited_df['% Volume'].sum()
        if abs(total_volume - 100) > 0.1:
            st.warning(f"⚠️ Total % Volume = {total_volume:.2f}% (disarankan mendekati 100%)")
        
        # Tombol kalkulasi
        if st.button("🧮 Hitung Hasil PSA", type="primary", use_container_width=True):
            with st.spinner("Menghitung..."):
                try:
                    # Normalisasi volume
                    df_calc = edited_df.copy()
                    df_calc['% Volume Normalized'] = (df_calc['% Volume'] / total_volume * 100)
                    
                    # Hitung statistik
                    diameter_avg = np.average(
                        df_calc['Diameter (nm)'],
                        weights=df_calc['% Volume Normalized']
                    )
                    
                    pdi_avg = np.average(
                        df_calc['PDI'],
                        weights=df_calc['% Volume Normalized']
                    )
                    
                    variance = np.average(
                        (df_calc['Diameter (nm)'] - diameter_avg) ** 2,
                        weights=df_calc['% Volume Normalized']
                    )
                    std_dev = np.sqrt(variance)
                    
                    pdi_calculated = variance / (diameter_avg ** 2)
                    
                    # Mode
                    mode_idx = df_calc['% Volume Normalized'].idxmax()
                    mode_diameter = df_calc.loc[mode_idx, 'Diameter (nm)']
                    mode_percentage = df_calc.loc[mode_idx, '% Volume Normalized']
                    
                    # Klasifikasi
                    if pdi_calculated < 0.05:
                        klasifikasi = "Sangat Monodispersi (Excellent)"
                        warna = "🟢"
                        grade = "A+"
                    elif pdi_calculated < 0.1:
                        klasifikasi = "Monodispersi (Sangat Baik)"
                        warna = "🟢"
                        grade = "A"
                    elif pdi_calculated < 0.2:
                        klasifikasi = "Hampir Monodispersi (Baik)"
                        warna = "🟡"
                        grade = "B"
                    elif pdi_calculated < 0.3:
                        klasifikasi = "Polydispersi Sedang"
                        warna = "🟠"
                        grade = "C"
                    else:
                        klasifikasi = "Polydispersi Tinggi"
                        warna = "🔴"
                        grade = "D"
                    
                    # Simpan hasil
                    hasil_psa = {
                        'dataframe': df_calc.to_dict('records'),
                        'diameter_rerata': float(diameter_avg),
                        'pdi_rerata': float(pdi_avg),
                        'pdi_terhitung': float(pdi_calculated),
                        'std_dev': float(std_dev),
                        'variance': float(variance),
                        'mode_diameter': float(mode_diameter),
                        'mode_percentage': float(mode_percentage),
                        'klasifikasi': klasifikasi,
                        'warna': warna,
                        'grade': grade,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'total_points': len(df_calc)
                    }
                    
                    st.session_state.psa_results.append(hasil_psa)
                    save_to_json('nanote_psa.json', st.session_state.psa_results)
                    
                    st.success("✅ Perhitungan PSA berhasil!")
                    
                    # Tampilkan hasil
                    st.markdown("### 📈 Hasil Analisis PSA")
                    
                    # Metrics
                    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                    
                    with col_metric1:
                        st.metric("Diameter Rata-rata", f"{diameter_avg:.2f} nm", f"± {std_dev:.2f} nm")
                    
                    with col_metric2:
                        st.metric("PDI Terhitung", f"{pdi_calculated:.3f}", grade)
                    
                    with col_metric3:
                        st.metric("Mode", f"{mode_diameter:.1f} nm", f"{mode_percentage:.1f}%")
                    
                    with col_metric4:
                        cv = (std_dev / diameter_avg) * 100
                        st.metric("Coef. Variasi", f"{cv:.1f}%", "CV")
                    
                    # Klasifikasi
                    st.info(f"**{warna} Klasifikasi:** {klasifikasi}")
                    
                    # Visualisasi
                    st.markdown("### 📊 Visualisasi Distribusi")
                    
                    fig = go.Figure()
                    
                    # Bar chart
                    fig.add_trace(go.Bar(
                        x=df_calc['Diameter (nm)'],
                        y=df_calc['% Volume Normalized'],
                        name='% Volume',
                        marker_color='royalblue',
                        opacity=0.8,
                        hovertemplate='Diameter: %{x:.1f} nm<br>% Volume: %{y:.1f}%'
                    ))
                    
                    # Rata-rata line
                    fig.add_vline(
                        x=diameter_avg,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Rata-rata: {diameter_avg:.1f} nm"
                    )
                    
                    fig.update_layout(
                        title='Distribusi Ukuran Partikel',
                        xaxis_title='Diameter (nm)',
                        yaxis_title='% Volume',
                        template='plotly_white',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detail data
                    with st.expander("📋 Detail Data dan Statistik"):
                        col_stat1, col_stat2 = st.columns(2)
                        
                        with col_stat1:
                            st.markdown("**Statistik Deskriptif**")
                            stats_df = pd.DataFrame({
                                'Parameter': ['Minimum', 'Maksimum', 'Mean', 'Median', 'Std Dev', 'Variance'],
                                'Nilai': [
                                    f"{df_calc['Diameter (nm)'].min():.2f} nm",
                                    f"{df_calc['Diameter (nm)'].max():.2f} nm",
                                    f"{df_calc['Diameter (nm)'].mean():.2f} nm",
                                    f"{df_calc['Diameter (nm)'].median():.2f} nm",
                                    f"{std_dev:.2f} nm",
                                    f"{variance:.2f}"
                                ]
                            })
                            st.dataframe(stats_df, use_container_width=True, hide_index=True)
                        
                        with col_stat2:
                            st.markdown("**Parameter Kualitas**")
                            quality_df = pd.DataFrame({
                                'Parameter': ['PDI Terhitung', 'Klasifikasi', 'Grade', 'Coef. Variasi', 'Uniformitas'],
                                'Nilai': [
                                    f"{pdi_calculated:.3f}",
                                    klasifikasi,
                                    grade,
                                    f"{cv:.1f}%",
                                    f"{100 - cv:.1f}%"
                                ]
                            })
                            st.dataframe(quality_df, use_container_width=True, hide_index=True)
                    
                    # Rekomendasi
                    st.markdown("### 💡 Rekomendasi")
                    
                    if grade in ['A+', 'A']:
                        st.success("""
                        **Kualitas Sangat Baik!** Nanomaterial Anda memiliki distribusi ukuran yang sangat seragam.
                        
                        **Rekomendasi:**
                        - Lanjutkan metode sintesis dengan parameter yang sama
                        - Cocok untuk aplikasi biomedis dan elektronik presisi
                        - Pertimbangkan untuk publikasi hasil
                        """)
                    elif grade == 'B':
                        st.info("""
                        **Kualitas Baik.** Distribusi ukuran cukup seragam untuk kebanyakan aplikasi.
                        
                        **Rekomendasi:**
                        - Dapat digunakan untuk aplikasi katalisis dan coating
                        - Optimasi kecil dapat meningkatkan monodispersitas
                        - Evaluasi efek pH dan konsentrasi
                        """)
                    elif grade == 'C':
                        st.warning("""
                        **Perlu Optimasi.** Distribusi ukuran cukup lebar.
                        
                        **Rekomendasi:**
                        - Evaluasi parameter sintesis (suhu, waktu, stirring rate)
                        - Pertimbangkan penggunaan surfaktan atau stabilizer
                        - Cocok untuk aplikasi bulk material
                        """)
                    else:
                        st.error("""
                        **Perlu Optimasi Signifikan.** Distribusi ukuran sangat lebar.
                        
                        **Rekomendasi:**
                        - Evaluasi ulang metode sintesis
                        - Optimasi parameter utama
                        - Pertimbangkan metode purifikasi
                        - Cocok untuk aplikasi konstruksi
                        """)
                    
                    # Tombol ekspor PDF
                    st.divider()
                    if st.button("📥 Ekspor Hasil ke PDF", type="primary", use_container_width=True):
                        try:
                            pdf_path = create_psa_report(hasil_psa, len(st.session_state.psa_results))
                            with open(pdf_path, 'rb') as f:
                                pdf_data = f.read()
                            
                            st.download_button(
                                label="⬇️ Download Laporan PDF",
                                data=pdf_data,
                                file_name=f"Laporan_PSA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error dalam perhitungan: {str(e)}")

# =================== HALAMAN HASIL PSA ===================
elif st.session_state.current_page == "hasil_psa":
    st.markdown("## 📊 Hasil PSA Tersimpan")
    
    if not st.session_state.psa_results:
        st.info("📭 Belum ada hasil PSA. Gunakan kalkulator PSA terlebih dahulu!")
    else:
        # Filter
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            pdi_range = st.slider(
                "Filter berdasarkan PDI",
                0.0, 1.0, (0.0, 1.0), 0.01
            )
        
        with col_filter2:
            grade_filter = st.multiselect(
                "Filter berdasarkan grade",
                options=list(set([r.get('grade', '') for r in st.session_state.psa_results])),
                default=[]
            )
        
        # Filter data
        filtered_results = [
            r for r in st.session_state.psa_results
            if pdi_range[0] <= r.get('pdi_terhitung', 0) <= pdi_range[1]
        ]
        
        if grade_filter:
            filtered_results = [
                r for r in filtered_results
                if r.get('grade', '') in grade_filter
            ]
        
        st.markdown(f"**📈 Menampilkan {len(filtered_results)} dari {len(st.session_state.psa_results)} hasil PSA**")
        
        # Tampilkan hasil
        for idx, hasil in enumerate(filtered_results):
            original_idx = st.session_state.psa_results.index(hasil)
            
            with st.container():
                col_res1, col_res2 = st.columns([3, 1])
                
                with col_res1:
                    with st.expander(f"**PSA #{original_idx + 1}** - {hasil.get('timestamp', '')}", expanded=False):
                        col_data1, col_data2 = st.columns(2)
                        
                        with col_data1:
                            st.write(f"**Diameter Rata-rata:** {hasil.get('diameter_rerata', 0):.2f} nm")
                            st.write(f"**PDI Terhitung:** {hasil.get('pdi_terhitung', 0):.3f}")
                            st.write(f"**Standard Dev:** {hasil.get('std_dev', 0):.2f} nm")
                        
                        with col_data2:
                            st.write(f"**Klasifikasi:** {hasil.get('warna', '')} {hasil.get('klasifikasi', '')}")
                            st.write(f"**Grade:** {hasil.get('grade', '')}")
                            st.write(f"**Jumlah Data:** {hasil.get('total_points', 0)} titik")
                        
                        # Tampilkan data
                        if 'dataframe' in hasil:
                            df_display = pd.DataFrame(hasil['dataframe'])
                            st.dataframe(df_display[['Diameter (nm)', '% Volume', 'PDI']], 
                                       use_container_width=True, height=150)
                
                with col_res2:
                    # Tombol aksi
                    if st.button("📥 PDF", key=f"pdf_{original_idx}", use_container_width=True):
                        try:
                            pdf_path = create_psa_report(hasil, original_idx + 1)
                            with open(pdf_path, 'rb') as f:
                                pdf_data = f.read()
                            
                            st.download_button(
                                label="Download",
                                data=pdf_data,
                                file_name=f"PSA_Report_{original_idx + 1}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{original_idx}"
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    if st.button("🗑️", key=f"del_psa_{original_idx}", use_container_width=True):
                        st.session_state.psa_results.pop(original_idx)
                        save_to_json('nanote_psa.json', st.session_state.psa_results)
                        st.success("Hasil PSA berhasil dihapus!")
                        st.rerun()

# =================== HALAMAN EKSPOR DATA ===================
elif st.session_state.current_page == "ekspor_data":
    st.markdown("## 📁 Ekspor Data")
    
    tab1, tab2 = st.tabs(["📝 Ekspor Catatan", "📊 Ekspor Hasil PSA"])
    
    with tab1:
        st.markdown("### Ekspor Catatan Praktik ke Word")
        
        if st.session_state.catatan_list:
            # Pilih catatan
            catatan_options = [f"{c['id']}: {c['judul'][:40]}..." for c in st.session_state.catatan_list]
            selected_note = st.selectbox("Pilih catatan untuk diekspor", catatan_options)
            
            if selected_note:
                note_id = int(selected_note.split(":")[0]) - 1
                catatan = st.session_state.catatan_list[note_id]
                
                # Preview
                with st.expander("👁️ Preview Catatan"):
                    st.write(f"**Judul:** {catatan['judul']}")
                    st.write(f"**Praktikan:** {catatan['nama_praktikan']}")
                    st.write(f"**Tanggal:** {catatan['tanggal']}")
                    st.write(f"**Material:** {catatan['jenis_nanomaterial']}")
                    st.write(f"**Metode:** {catatan['metode_sintesis']}")
                
                # Tombol ekspor
                if st.button("📥 Ekspor ke Word", type="primary", use_container_width=True):
                    try:
                        doc_path = create_word_note(catatan)
                        with open(doc_path, 'rb') as f:
                            doc_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Dokumen Word",
                            data=doc_data,
                            file_name=f"Catatan_{catatan['judul'][:20]}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("Belum ada catatan untuk diekspor")
    
    with tab2:
        st.markdown("### Ekspor Hasil PSA ke PDF")
        
        if st.session_state.psa_results:
            # Pilih hasil PSA
            psa_options = [
                f"Hasil #{i+1}: D={r['diameter_rerata']:.1f}nm, PDI={r['pdi_terhitung']:.3f}" 
                for i, r in enumerate(st.session_state.psa_results)
            ]
            selected_psa = st.selectbox("Pilih hasil PSA untuk diekspor", psa_options)
            
            if selected_psa:
                psa_idx = int(selected_psa.split("#")[1].split(":")[0]) - 1
                hasil = st.session_state.psa_results[psa_idx]
                
                # Preview
                with st.expander("👁️ Preview Hasil"):
                    st.write(f"**Diameter Rata-rata:** {hasil['diameter_rerata']:.2f} nm")
                    st.write(f"**PDI Terhitung:** {hasil['pdi_terhitung']:.3f}")
                    st.write(f"**Klasifikasi:** {hasil['klasifikasi']}")
                    st.write(f"**Grade:** {hasil['grade']}")
                
                # Tombol ekspor
                if st.button("📥 Ekspor ke PDF", type="primary", use_container_width=True, key="export_pdf"):
                    try:
                        pdf_path = create_psa_report(hasil, psa_idx + 1)
                        with open(pdf_path, 'rb') as f:
                            pdf_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Laporan PDF",
                            data=pdf_data,
                            file_name=f"PSA_Report_{psa_idx + 1}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("Belum ada hasil PSA untuk diekspor")

# =================== HALAMAN PANDUAN ===================
elif st.session_state.current_page == "panduan":
    st.markdown("## ⚙️ Panduan NaNote")
    
    tab_guide, tab_about = st.tabs(["📖 Panduan Penggunaan", "ℹ️ Tentang NaNote"])
    
    with tab_guide:
        st.markdown("""
        ### 🎯 **Panduan Lengkap NaNote**
        
        #### **1. 📝 Modul Catatan Praktik**
        
        **Fungsi:** Mencatat seluruh proses sintesis nanomaterial
        
        **Langkah-langkah:**
        1. Buka halaman **"Catatan Baru"**
        2. Isi semua informasi dasar (judul, praktikan, tanggal)
        3. Tentukan spesifikasi nanomaterial (jenis, metode sintesis)
        4. Input parameter sintesis (suhu, waktu, pH, konsentrasi)
        5. Tulis prosedur dan hasil pengamatan
        6. Upload gambar hasil sintesis (opsional)
        7. Klik **"Simpan Catatan"**
        8. Ekspor ke Word jika diperlukan
        
        #### **2. 🧮 Modul Kalkulator PSA**
        
        **Fungsi:** Menganalisis distribusi ukuran partikel nanomaterial
        
        **Cara penggunaan:**
        - **Mode Manual:** Input data langsung di tabel
        - **Mode Upload:** Upload file Excel/CSV dengan format:
          - Kolom 1: Diameter (nm)
          - Kolom 2: % Volume
          - Kolom 3: PDI
        
        **Parameter Output:**
        - Diameter rata-rata (weighted)
        - PDI (Polydispersity Index)
        - Standard deviation
        - Mode diameter
        - Klasifikasi kualitas (A+ sampai D)
        
        #### **3. 📊 Interpretasi Hasil PSA**
        
        **Skala Kualitas:**
        - **A+ / A:** Monodispersi (sangat baik)
        - **B:** Hampir monodispersi (baik)
        - **C:** Polydispersi sedang (cukup)
        - **D:** Polydispersi tinggi (perlu optimasi)
        
        #### **4. 📁 Sistem Ekspor**
        
        **Format yang didukung:**
        - **Word (.docx):** Untuk catatan praktik
        - **PDF (.pdf):** Untuk hasil PSA
        - **Excel (.xlsx):** Untuk data mentah (coming soon)
        
        #### **5. 💾 Manajemen Data**
        
        **Penyimpanan:**
        - Data disimpan dalam session browser
        - Bertahan selama aplikasi terbuka
        - Ekspor untuk penyimpanan permanen
        """)
    
    with tab_about:
        st.markdown("""
        ### ℹ️ **Tentang NaNote**
        
        **NaNote v1.0** - Aplikasi Catatan & Kalkulator PSA Nanomaterial
        
        **Deskripsi:**
        NaNote adalah aplikasi web yang dirancang khusus untuk membantu peneliti dan praktikan
        nanomaterial dalam mencatat hasil praktik dan menganalisis distribusi ukuran partikel.
        
        **Fitur Utama:**
        - 📝 Sistem pencatatan praktik nanomaterial
        - 🧮 Kalkulator PSA dengan analisis statistik
        - 📊 Visualisasi data interaktif
        - 📁 Ekspor ke Word dan PDF
        - 💻 Interface user-friendly dalam bahasa Indonesia
        
        **Teknologi:**
        - Framework: Streamlit
        - Bahasa: Python 3.8+
        - Visualisasi: Plotly
        - Dokumentasi: python-docx, ReportLab
        
        **Pengembang:**
        Aplikasi ini dikembangkan untuk mendukung penelitian nanomaterial di Indonesia.
        
        **Kontak:**
        - Email: support@nanote.com
        - GitHub: github.com/nanote-app
        
        **Lisensi:** MIT License
        
        © 2024 NaNote Team
        """)

# =================== FOOTER ===================
st.markdown("---")
footer_cols = st.columns([2, 1, 1])
with footer_cols[0]:
    st.caption("🔬 **NaNote** - Aplikasi Catatan & Kalkulator PSA Nanomaterial")
with footer_cols[1]:
    st.caption("📧 support@nanote.com")
with footer_cols[2]:
    st.caption("© 2024 All Rights Reserved")
