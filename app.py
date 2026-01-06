import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import base64
import tempfile
from docx import Document
from docx.shared import Inches, Pt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import json
import os

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
        background-color: #FF986A;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
    }
    .result-box {
        background-color: #C47BE4;
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
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #2563EB;
        transform: translateY(-2px);
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
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995463.png", width=80)
    st.title("NaNote")
    st.markdown("**Catatan & Kalkulator PSA**")
    
    st.markdown("---")
    
    menu = st.radio(
        "Pilih Menu:",
        ["🏠 Beranda", "📝 Catatan Praktikum", "🧮 Kalkulasi PSA", "📊 Data Tersimpan", "ℹ️ Panduan"]
    )
    
    st.markdown("---")
    
    st.markdown("### Informasi")
    st.info("""
    Versi: 1.0.0
    Untuk: Praktikum Nanomaterial
    Bahasa: Indonesia
    """)

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
                <li>Data mentah → CSV</li>
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
        'No': [1, 2, 3, 4, 5],
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
                tujuan = st.text_area("Tujuan Praktikum*", height=1500, 
                                    placeholder="Tuliskan tujuan praktikum...")
                alat_bahan = st.text_area("Alat dan Bahan*", height=1500,
                                        placeholder="Daftar alat dan bahan...")
            
            with col2:
                prosedur = st.text_area("Prosedur Kerja*", height=1500,
                                      placeholder="Langkah-langkah percobaan...")
                hasil = st.text_area("Hasil Pengamatan*", height=1500,
                                   placeholder="Hasil yang diamati...")
            
            analisis = st.text_area("Analisis Data", height=1200,
                                  placeholder="Analisis dari hasil yang diperoleh...")
            kesimpulan = st.text_area("Kesimpulan", height=1000,
                                    placeholder="Kesimpulan praktikum...")
            
            submitted = st.form_submit_button("💾 Simpan Catatan", use_container_width=True)
            
            if submitted:
                if not all([judul, praktikan, mata_praktikum != "Pilih...", tujuan, 
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
                    
                    # Tombol download
                    doc = buat_file_word(catatan_data)
                    doc_buffer = io.BytesIO()
                    doc.save(doc_buffer)
                    doc_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Download sebagai Word (.docx)",
                        data=doc_buffer,
                        file_name=f"Catatan_{judul.replace(' ', '_')}_{tanggal}.docx",
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
                            file_name=f"Catatan_{catatan['judul'].replace(' ', '_')}_{catatan['tanggal']}.docx",
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
                
                st.success("✅ Perhitungan selesai! Buka tab 'Hasil Perhitungan'.")
                st.rerun()
    
    with tab2:
        if 'current_psa' not in st.session_state or not st.session_state.current_psa:
            st.info("ℹ️ Masukkan data di tab 'Input Data' dan klik 'Hitung Hasil PSA'.")
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
                file_name=f"Hasil_PSA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
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
            
            for catatan in st.session_state.catatan_list:
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
                            file_name=f"Catatan_{catatan['judul'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            
            # Tombol ekspor semua
            if st.button("📤 Ekspor Semua Data", use_container_width=True):
                all_data = {
                    'catatan': st.session_state.catatan_list,
                    'psa_data': st.session_state.psa_data,
                    'export_time': datetime.now().isoformat()
                }
                
                json_str = json.dumps(all_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=f"nanote_backup_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
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
st.markdown("🔬 **NaNote v1.0** • Aplikasi Catatan Praktikum & Kalkulasi PSA • Dibuat oleh Kelompok 3 Logika dan Pemrograman Komputer")
st.markdown(f"© {datetime.now().year}")
st.markdown('</div>', unsafe_allow_html=True)
