import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import tempfile
import os
import json
import base64
from io import BytesIO

# =================== KONFIGURASI APLIKASI ===================
st.set_page_config(
    page_title="NaNote - Catatan & Kalkulator PSA Nanomaterial",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================== CSS KUSTOM ===================
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
    .main-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(46, 134, 171, 0.3);
    }
    
    .title-text {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
    }
    
    .subtitle-text {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* CARD STYLE */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid var(--primary);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
        transition: transform 0.3s ease;
    }
    
    .custom-card:hover {
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
    .metric-box {
        background: linear-gradient(135deg, var(--primary) 0%, #3B9AB2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {
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
</style>
""", unsafe_allow_html=True)

# =================== FUNGSI UTILITAS ===================
def init_session_state():
    """Inisialisasi session state"""
    defaults = {
        'catatan_list': [],
        'psa_results': [],
        'current_page': "beranda",
        'edit_mode': False,
        'edit_index': None,
        'psa_data': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def set_page(page_name):
    """Navigasi antar halaman"""
    st.session_state.current_page = page_name
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

def create_word_document(catatan):
    """Membuat dokumen Word sederhana"""
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    import tempfile
    
    doc = Document()
    
    # Judul
    title = doc.add_heading('LAPORAN PRAKTIKUM NANOMATERIAL', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.size = Pt(16)
    
    # Informasi
    doc.add_paragraph(f"Judul: {catatan['judul']}")
    doc.add_paragraph(f"Praktikan: {catatan['nama_praktikan']}")
    doc.add_paragraph(f"Tanggal: {catatan['tanggal']}")
    doc.add_paragraph(f"Nanomaterial: {catatan['jenis_nanomaterial']}")
    doc.add_paragraph(f"Metode: {catatan['metode_sintesis']}")
    doc.add_paragraph(f"Suhu: {catatan['suhu']}°C")
    doc.add_paragraph(f"Waktu: {catatan['waktu']} jam")
    doc.add_paragraph(f"pH: {catatan['ph']}")
    doc.add_paragraph(f"Konsentrasi: {catatan['konsentrasi']} mg/mL")
    
    # Prosedur
    doc.add_heading('PROSEDUR', level=1)
    doc.add_paragraph(catatan['prosedur'])
    
    # Hasil
    doc.add_heading('HASIL PENGAMATAN', level=1)
    doc.add_paragraph(catatan['hasil_pengamatan'])
    
    # Simpan file
    temp_dir = tempfile.gettempdir()
    filename = f"Catatan_{catatan['judul'][:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join(temp_dir, filename)
    doc.save(filepath)
    
    return filepath

def create_pdf_report(hasil_psa, result_id):
    """Membuat laporan PDF sederhana"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    import tempfile
    
    # Setup dokumen
    temp_dir = tempfile.gettempdir()
    filename = f"Laporan_PSA_{result_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(temp_dir, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Header
    story.append(Paragraph("LAPORAN ANALISIS PSA NANOMATERIAL", styles['Heading1']))
    story.append(Paragraph(f"NaNote Report #{result_id}", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Tabel hasil
    data = [
        ["Parameter", "Nilai", "Keterangan"],
        ["Diameter Rata-rata", f"{hasil_psa['diameter_rerata']:.2f} nm", "Weighted average"],
        ["PDI Terhitung", f"{hasil_psa['pdi_terhitung']:.3f}", hasil_psa['klasifikasi']],
        ["Standard Deviation", f"{hasil_psa['std_dev']:.2f} nm", "σ"],
        ["Variance", f"{hasil_psa['variance']:.2f}", "σ²"],
        ["Jumlah Data", str(hasil_psa['total_points']), "Titik distribusi"]
    ]
    
    table = Table(data, colWidths=[5*cm, 4*cm, 7*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    
    story.append(table)
    doc.build(story)
    
    return filepath

def create_sample_psa_data(num_points=8):
    """Membuat data PSA contoh"""
    np.random.seed(42)
    diameters = np.sort(np.random.normal(50, 15, num_points))
    diameters = np.clip(diameters, 5, 150)
    
    volumes = np.exp(-(diameters - diameters.mean())**2 / (2 * (diameters.std()**2)))
    volumes = volumes / volumes.sum() * 100
    
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
        "📖 Panduan": "panduan"
    }
    
    for label, page in menu_items.items():
        if st.button(label, use_container_width=True, 
                    type="primary" if st.session_state.current_page == page else "secondary"):
            set_page(page)
    
    st.divider()
    
    # Statistik Cepat
    st.markdown("### 📊 Statistik")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Catatan", len(st.session_state.catatan_list))
    with col2:
        st.metric("PSA", len(st.session_state.psa_results))
    
    st.divider()
    
    # Info
    st.caption("**NaNote v1.0**")
    st.caption("© 2024 Lab Nanomaterial")

# =================== HALAMAN BERANDA ===================
if st.session_state.current_page == "beranda":
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="title-text">NaNote</h1>
        <p class="subtitle-text">Catatan Praktik & Kalkulator PSA Nanomaterial</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
    
    with col2:
        st.image("https://img.icons8.com/color/300/000000/test-tube.png", 
                caption="Platform Nanomaterial Digital")
    
    # Quick Start
    st.markdown("### 🚀 Mulai Cepat")
    
    col_start1, col_start2, col_start3 = st.columns(3)
    
    with col_start1:
        st.markdown("""
        <div class="custom-card">
            <h4>📝 Catatan Baru</h4>
            <p>Mulai mencatat praktik nanomaterial Anda.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Buat Catatan →", key="btn1", use_container_width=True):
            set_page("catatan_baru")
    
    with col_start2:
        st.markdown("""
        <div class="custom-card">
            <h4>🧮 Kalkulator PSA</h4>
            <p>Hitung distribusi ukuran partikel.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Hitung PSA →", key="btn2", use_container_width=True):
            set_page("kalkulator_psa")
    
    with col_start3:
        st.markdown("""
        <div class="custom-card">
            <h4>📚 Lihat Data</h4>
            <p>Akses catatan dan hasil PSA.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Data Tersimpan →", key="btn3", use_container_width=True):
            set_page("catatan_simpan")

# =================== HALAMAN CATATAN BARU ===================
elif st.session_state.current_page == "catatan_baru":
    st.markdown("## 📝 Catatan Praktik Baru")
    
    with st.form("form_catatan", clear_on_submit=True):
        st.markdown("### Informasi Dasar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            judul = st.text_input("Judul Praktik*", placeholder="Sintesis Nanopartikel...")
            nama_praktikan = st.text_input("Nama Praktikan*", placeholder="Nama lengkap")
            tanggal = st.date_input("Tanggal Praktik*", datetime.now())
        
        with col2:
            jenis_nanomaterial = st.selectbox(
                "Jenis Nanomaterial*",
                ["TiO₂ (Titanium Dioxide)", "SiO₂ (Silicon Dioxide)", "ZnO (Zinc Oxide)", 
                 "Ag (Silver Nanoparticles)", "Au (Gold Nanoparticles)", "Fe₃O₄ (Magnetite)"]
            )
            metode_sintesis = st.selectbox(
                "Metode Sintesis*",
                ["Sol-Gel", "Hidrotermal", "Sonokimia", "Mekanokimia", "Co-precipitation"]
            )
        
        st.markdown("### Parameter Sintesis")
        
        col3, col4 = st.columns(2)
        
        with col3:
            suhu = st.number_input("Suhu (°C)*", value=25.0)
            waktu = st.number_input("Waktu (jam)*", value=1.0)
        
        with col4:
            ph = st.slider("pH Larutan", 0.0, 14.0, 7.0, 0.1)
            konsentrasi = st.number_input("Konsentrasi (mg/mL)*", value=1.0)
        
        st.markdown("### Prosedur & Hasil")
        
        prosedur = st.text_area(
            "Prosedur Praktik*",
            height=120,
            placeholder="Tuliskan langkah-langkah sintesis..."
        )
        
        hasil_pengamatan = st.text_area(
            "Hasil Pengamatan*",
            height=120,
            placeholder="Deskripsikan hasil yang diperoleh..."
        )
        
        submitted = st.form_submit_button("💾 Simpan Catatan", type="primary")
        
        if submitted:
            if judul and nama_praktikan and prosedur and hasil_pengamatan:
                catatan = {
                    'id': len(st.session_state.catatan_list) + 1,
                    'judul': judul,
                    'nama_praktikan': nama_praktikan,
                    'tanggal': str(tanggal),
                    'jenis_nanomaterial': jenis_nanomaterial,
                    'metode_sintesis': metode_sintesis,
                    'suhu': suhu,
                    'waktu': waktu,
                    'ph': ph,
                    'konsentrasi': konsentrasi,
                    'prosedur': prosedur,
                    'hasil_pengamatan': hasil_pengamatan,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.catatan_list.append(catatan)
                st.success("✅ Catatan berhasil disimpan!")
                st.balloons()
                
                # Tampilkan preview
                with st.expander("👁️ Preview Catatan"):
                    col_pre1, col_pre2 = st.columns(2)
                    with col_pre1:
                        st.write(f"**Judul:** {judul}")
                        st.write(f"**Praktikan:** {nama_praktikan}")
                        st.write(f"**Tanggal:** {tanggal}")
                    with col_pre2:
                        st.write(f"**Material:** {jenis_nanomaterial}")
                        st.write(f"**Metode:** {metode_sintesis}")
                        st.write(f"**Suhu:** {suhu}°C")
            
            else:
                st.error("❌ Harap isi semua field yang wajib (*)!")

# =================== HALAMAN CATATAN TERSIMPAN ===================
elif st.session_state.current_page == "catatan_simpan":
    st.markdown("## 📚 Catatan Praktik Tersimpan")
    
    if not st.session_state.catatan_list:
        st.info("📭 Belum ada catatan yang disimpan.")
    else:
        # Tampilkan catatan
        for idx, catatan in enumerate(st.session_state.catatan_list):
            with st.container():
                col_note1, col_note2 = st.columns([3, 1])
                
                with col_note1:
                    with st.expander(f"**{catatan['judul']}** - {catatan['tanggal']}", expanded=False):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**Praktikan:** {catatan['nama_praktikan']}")
                            st.write(f"**Material:** {catatan['jenis_nanomaterial']}")
                            st.write(f"**Metode:** {catatan['metode_sintesis']}")
                        
                        with col_info2:
                            st.write(f"**Suhu:** {catatan['suhu']}°C")
                            st.write(f"**Waktu:** {catatan['waktu']} jam")
                            st.write(f"**pH:** {catatan['ph']}")
                
                with col_note2:
                    # Tombol aksi
                    if st.button("📥 Word", key=f"word_{idx}", use_container_width=True):
                        try:
                            doc_path = create_word_document(catatan)
                            with open(doc_path, 'rb') as f:
                                doc_data = f.read()
                            
                            st.download_button(
                                label="Download",
                                data=doc_data,
                                file_name=f"Catatan_{catatan['judul'][:20]}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"dl_{idx}"
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                        st.session_state.catatan_list.pop(idx)
                        st.success("Catatan berhasil dihapus!")
                        st.rerun()

# =================== HALAMAN KALKULATOR PSA ===================
elif st.session_state.current_page == "kalkulator_psa":
    st.markdown("## 🧮 Kalkulator PSA Nanomaterial")
    
    # Input data
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
        if st.button("🔄 Generate Contoh"):
            st.session_state.psa_data = create_sample_psa_data(num_points)
            st.success("Data contoh berhasil dibuat!")
    
    # Inisialisasi data jika belum ada
    if st.session_state.psa_data is None:
        st.session_state.psa_data = create_sample_psa_data(num_points)
    
    # Editor data
    st.markdown("### 📊 Data PSA")
    
    edited_df = st.data_editor(
        st.session_state.psa_data,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Diameter (nm)": st.column_config.NumberColumn(format="%.2f"),
            "% Volume": st.column_config.NumberColumn(format="%.2f"),
            "PDI": st.column_config.NumberColumn(format="%.3f")
        }
    )
    
    # Tombol kalkulasi
    if st.button("🧮 Hitung Hasil PSA", type="primary", use_container_width=True):
        with st.spinner("Menghitung..."):
            try:
                # Normalisasi volume
                total_volume = edited_df['% Volume'].sum()
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
                if pdi_calculated < 0.1:
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
                
                st.success("✅ Perhitungan PSA berhasil!")
                
                # Tampilkan hasil
                st.markdown("### 📈 Hasil Analisis PSA")
                
                # Metrics
                col_metric1, col_metric2, col_metric3 = st.columns(3)
                
                with col_metric1:
                    st.metric("Diameter Rata-rata", f"{diameter_avg:.2f} nm")
                
                with col_metric2:
                    st.metric("PDI Terhitung", f"{pdi_calculated:.3f}")
                
                with col_metric3:
                    st.metric("Standard Dev", f"{std_dev:.2f} nm")
                
                # Klasifikasi
                st.info(f"**{warna} Klasifikasi:** {klasifikasi} (Grade: {grade})")
                
                # Visualisasi
                st.markdown("### 📊 Grafik Distribusi")
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_calc['Diameter (nm)'],
                    y=df_calc['% Volume Normalized'],
                    name='% Volume',
                    marker_color='royalblue'
                ))
                
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
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Detail data
                with st.expander("📋 Detail Data"):
                    st.dataframe(df_calc, use_container_width=True)
                
                # Tombol ekspor PDF
                if st.button("📥 Ekspor ke PDF", use_container_width=True):
                    try:
                        pdf_path = create_pdf_report(hasil_psa, len(st.session_state.psa_results))
                        with open(pdf_path, 'rb') as f:
                            pdf_data = f.read()
                        
                        st.download_button(
                            label="⬇️ Download Laporan PDF",
                            data=pdf_data,
                            file_name=f"PSA_Report_{len(st.session_state.psa_results)}.pdf",
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
        st.info("📭 Belum ada hasil PSA.")
    else:
        # Tampilkan hasil
        for idx, hasil in enumerate(st.session_state.psa_results):
            with st.container():
                col_res1, col_res2 = st.columns([3, 1])
                
                with col_res1:
                    with st.expander(f"**PSA #{idx + 1}** - {hasil['timestamp']}", expanded=False):
                        col_data1, col_data2 = st.columns(2)
                        
                        with col_data1:
                            st.write(f"**Diameter Rata-rata:** {hasil['diameter_rerata']:.2f} nm")
                            st.write(f"**PDI Terhitung:** {hasil['pdi_terhitung']:.3f}")
                            st.write(f"**Standard Dev:** {hasil['std_dev']:.2f} nm")
                        
                        with col_data2:
                            st.write(f"**Klasifikasi:** {hasil['warna']} {hasil['klasifikasi']}")
                            st.write(f"**Grade:** {hasil['grade']}")
                            st.write(f"**Jumlah Data:** {hasil['total_points']} titik")
                
                with col_res2:
                    # Tombol aksi
                    if st.button("📥 PDF", key=f"pdf_{idx}", use_container_width=True):
                        try:
                            pdf_path = create_pdf_report(hasil, idx + 1)
                            with open(pdf_path, 'rb') as f:
                                pdf_data = f.read()
                            
                            st.download_button(
                                label="Download",
                                data=pdf_data,
                                file_name=f"PSA_Report_{idx + 1}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{idx}"
                            )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    if st.button("🗑️", key=f"del_psa_{idx}", use_container_width=True):
                        st.session_state.psa_results.pop(idx)
                        st.success("Hasil PSA berhasil dihapus!")
                        st.rerun()

# =================== HALAMAN EKSPOR DATA ===================
elif st.session_state.current_page == "ekspor_data":
    st.markdown("## 📁 Ekspor Data")
    
    tab1, tab2 = st.tabs(["📝 Ekspor Catatan", "📊 Ekspor Hasil PSA"])
    
    with tab1:
        st.markdown("### Ekspor Catatan ke Word")
        
        if st.session_state.catatan_list:
            # Pilih catatan
            catatan_options = [f"{c['id']}: {c['judul'][:40]}..." for c in st.session_state.catatan_list]
            selected_note = st.selectbox("Pilih catatan", catatan_options)
            
            if selected_note:
                note_id = int(selected_note.split(":")[0]) - 1
                catatan = st.session_state.catatan_list[note_id]
                
                # Tombol ekspor
                if st.button("📥 Ekspor ke Word", use_container_width=True):
                    try:
                        doc_path = create_word_document(catatan)
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
            selected_psa = st.selectbox("Pilih hasil PSA", psa_options)
            
            if selected_psa:
                psa_idx = int(selected_psa.split("#")[1].split(":")[0]) - 1
                hasil = st.session_state.psa_results[psa_idx]
                
                # Tombol ekspor
                if st.button("📥 Ekspor ke PDF", use_container_width=True, key="export_pdf"):
                    try:
                        pdf_path = create_pdf_report(hasil, psa_idx + 1)
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
    st.markdown("## 📖 Panduan NaNote")
    
    tab1, tab2 = st.tabs(["Panduan Penggunaan", "Tentang NaNote"])
    
    with tab1:
        st.markdown("""
        ### 🎯 **Panduan Lengkap NaNote**
        
        #### **1. 📝 Modul Catatan Praktik**
        
        **Langkah-langkah:**
        1. Buka halaman **"Catatan Baru"**
        2. Isi semua informasi dasar (judul, praktikan, tanggal)
        3. Tentukan spesifikasi nanomaterial
        4. Input parameter sintesis
        5. Tulis prosedur dan hasil pengamatan
        6. Klik **"Simpan Catatan"**
        7. Ekspor ke Word jika diperlukan
        
        #### **2. 🧮 Modul Kalkulator PSA**
        
        **Cara penggunaan:**
        1. Input data Diameter (nm), % Volume, dan PDI
        2. Klik **"Hitung Hasil PSA"**
        3. Lihat hasil dan visualisasi
        4. Ekspor ke PDF untuk laporan
        
        #### **3. 📊 Interpretasi Hasil PSA**
        
        **Klasifikasi:**
        - **🟢 A:** Monodispersi (sangat baik)
        - **🟡 B:** Hampir monodispersi (baik)
        - **🟠 C:** Polydispersi sedang
        - **🔴 D:** Polydispersi tinggi
        """)
    
    with tab2:
        st.markdown("""
        ### ℹ️ **Tentang NaNote**
        
        **NaNote v1.0** - Aplikasi Catatan & Kalkulator PSA Nanomaterial
        
        **Deskripsi:**
        NaNote adalah aplikasi web yang dirancang khusus untuk membantu peneliti dan praktikan
        nanomaterial dalam mencatat hasil praktik dan menganalisis distribusi ukuran partikel.
        
        **Fitur Utama:**
        - 📝 Sistem pencatatan praktik
        - 🧮 Kalkulator PSA dengan analisis statistik
        - 📊 Visualisasi data interaktif
        - 📁 Ekspor ke Word dan PDF
        
        **Teknologi:**
        - Framework: Streamlit
        - Bahasa: Python
        - Visualisasi: Plotly
        
        **Kontak:**
        - Email: support@nanote.com
        
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
