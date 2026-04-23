import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="GMP Audit Mockup", layout="wide")

# Judul dan Header
st.title("🛡️ Digital GMP Audit System")
st.subheader("Berdasarkan Form ABU-QHS-FRM-014")

# Sidebar untuk Informasi Audit
with st.sidebar:
    st.header("Informasi Audit")
    lokasi = st.selectbox("Lokasi", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub", "Aula Rasa Retail"])
    auditor = st.text_input("Nama Auditor")
    auditee = st.text_input("Nama Auditee")
    tanggal = st.date_input("Tanggal Audit", datetime.now())

# Data Kriteria (Contoh dari file Anda)
categories = {
    "Inspeksi Area Luar": [
        "Lokasi bebas banjir dan pencemaran bau/asap/debu.",
        "Terdapat tempat cuci tangan dan pengering yang cukup.",
        "Lingkungan bebas dari semak belukar/rumput liar."
    ],
    "Fasilitas Sanitasi": [
        "Tersedia air bersih yang cukup untuk produksi.",
        "Toilet dalam keadaan bersih dan berfungsi baik.",
        "Tersedia sabun cuci tangan dan petunjuk cuci tangan."
    ],
    "Higiene Karyawan": [
        "Karyawan menggunakan APD lengkap (masker, hairnet).",
        "Karyawan tidak menggunakan perhiasan di area produksi.",
        "Karyawan dalam kondisi sehat (tidak ada luka terbuka)."
    ]
}

# Inisialisasi Skor
total_deduction = 0
audit_results = []

st.divider()

# Form Audit
for cat_name, items in categories.items():
    with st.expander(f"📍 {cat_name}", expanded=True):
        for item in items:
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.write(item)
            
            with col2:
                # Pilihan penilaian
                pilihan = st.radio(
                    f"Hasil: {item}",
                    ["OK", "Minor", "Major", "Kritis"],
                    horizontal=True,
                    key=item,
                    label_visibility="collapsed"
                )
            
            with col3:
                keterangan = st.text_input("Catatan/Temuan", key=f"note_{item}", placeholder="Opsional")

            # Logika Skor sesuai file Rev 1
            score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
            deduction = score_map[pilihan]
            total_deduction += deduction
            
            if pilihan != "OK":
                audit_results.append({"Kriteria": item, "Status": pilihan, "Temuan": keterangan})

# Kalkulasi Akhir
skor_akhir = 1000 + total_deduction
if skor_akhir < 0: skor_akhir = 0

# Penentuan Kategori (Sesuai File Anda)
if skor_akhir >= 860:
    kategori = "A (Sangat Baik)"
    color = "green"
elif skor_akhir >= 710:
    kategori = "B (Baik)"
    color = "blue"
elif skor_akhir >= 610:
    kategori = "C (Cukup)"
    color = "orange"
else:
    kategori = "D (Kurang)"
    color = "red"

# Ringkasan Hasil
st.divider()
st.header("Hasil Penilaian")
c1, c2 = st.columns(2)
c1.metric("Skor Akhir", f"{skor_akhir} / 1000")
c2.markdown(f"### Kategori: :{color}[{kategori}]")

# Tombol Submit & Export
if st.button("Submit Audit & Generate Report"):
    st.success(f"Audit untuk {lokasi} berhasil disimpan!")
    if audit_results:
        st.write("### Daftar Temuan (CAPA):")
        df_temuan = pd.DataFrame(audit_results)
        st.table(df_temuan)
