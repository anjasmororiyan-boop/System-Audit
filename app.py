import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Digital GMP Audit", layout="wide")

st.title("🛡️ Digital GMP Audit System")
st.caption("Customized for Template Checklist ABU-QHS")

# Sidebar untuk Kontrol
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    # File uploader disesuaikan dengan format CSV (delimiter ;)
    uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
    
    st.divider()
    st.header("📝 Info Audit")
    lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub", "Outlet Retail"])
    auditor = st.text_input("Nama Auditor", placeholder="Input nama...")
    auditee = st.text_input("Nama Auditee", placeholder="Input nama...")
    tanggal = st.date_input("Tanggal Audit", datetime.now())

# Logika Pengolahan Data Template
if uploaded_file is not None:
    # Membaca CSV dengan delimiter ; sesuai file template Anda
    df_template = pd.read_csv(uploaded_file, sep=';')
    
    # Inisialisasi variabel skor & temuan
    total_deduction = 0
    audit_results = []

    st.info(f"📋 Memuat {len(df_template)} kriteria audit.")

    # Loop berdasarkan Kategori Utama
    for kategori, group_kategori in df_template.groupby('Kategori', sort=False):
        with st.expander(f"📂 {kategori}", expanded=True):
            
            # Loop berdasarkan Area (Sub-Kategori)
            for area, group_area in group_kategori.groupby('Area', sort=False):
                st.markdown(f"**📍 Area: {area}**")
                
                for _, row in group_area.iterrows():
                    # Membuat layout baris: No & Kriteria | Penilaian | Catatan
                    col_text, col_score, col_note = st.columns([4, 3, 3])
                    
                    with col_text:
                        st.write(f"{row['No']}. {row['Kriteria Penilaian']}")
                    
                    with col_score:
                        key_id = f"{row['Kategori']}_{row['No']}_{row['Area']}"
                        pilihan = st.radio(
                            "Status", ["OK", "Minor", "Major", "Kritis"],
                            key=f"status_{key_id}", horizontal=True, label_visibility="collapsed"
                        )
                    
                    with col_note:
                        keterangan = st.text_input("Catatan", key=f"note_{key_id}", placeholder="Detail temuan...", label_visibility="collapsed")
                        
                    # Kalkulasi Skor (Minor -10, Major -20, Kritis -30)
                    score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += score_map[pilihan]
                    
                    if pilihan != "OK":
                        audit_results.append({
                            "Kategori": kategori,
                            "Area": area,
                            "Kriteria": row['Kriteria Penilaian'],
                            "Temuan": pilihan,
                            "Catatan": keterangan
                        })
                st.divider()

    # Bagian Footer Penilaian
    st.divider()
    skor_akhir = max(0, 1000 + total_deduction)
    
    # Penentuan Grade
    if skor_akhir >= 860: grade, color = "A (Sangat Baik)", "green"
    elif skor_akhir >= 710: grade, color = "B (Baik)", "blue"
    elif skor_akhir >= 610: grade, color = "C (Cukup)", "orange"
    else: grade, color = "D (Kurang)", "red"

    # Dashboard Hasil
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Skor Audit Akhir", f"{skor_akhir} / 1000")
    with col_res2:
        st.subheader(f"Grade: :{color}[{grade}]")

    # Tombol Simpan
    if st.button("Simpan & Download Laporan Audit"):
        if audit_results:
            df_final = pd.DataFrame(audit_results)
            st.warning("⚠️ Temuan Terdeteksi!")
            st.table(df_final)
        else:
            st.success("✅ Sempurna! Tidak ada temuan audit.")

else:
    st.warning("Silakan upload file 'Template Checklist.csv' melalui sidebar untuk memulai audit.")
