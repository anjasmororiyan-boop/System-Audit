import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GMP Digital Audit", layout="wide")

st.title("🛡️ Digital GMP Audit System")
st.subheader("Berdasarkan Form ABU-QHS-FRM-014")

# Fitur Upload Template di Sidebar
with st.sidebar:
    st.header("Konfigurasi & Data")
    uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
    st.divider()
    st.header("Informasi Audit")
    lokasi = st.selectbox("Lokasi", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
    auditor = st.text_input("Nama Auditor")
    tanggal = st.date_input("Tanggal Audit", datetime.now())

# Logika Memuat Data
if uploaded_file is not None:
    df_template = pd.read_csv(uploaded_file)
    # Mengelompokkan kriteria berdasarkan kategori dari file yang diupload
    categories = df_template.groupby('Kategori')['Kriteria'].apply(list).to_dict()
else:
    # Default data jika belum ada file yang diupload
    categories = {
        "Contoh Kategori": ["Upload file CSV di sidebar untuk memuat checklist Anda."]
    }

total_deduction = 0
audit_results = []

st.divider()

# Form Audit Dinamis
with st.form("audit_form"):
    for cat_name, items in categories.items():
        with st.expander(f"📍 {cat_name}", expanded=True):
            for item in items:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(item)
                with col2:
                    pilihan = st.radio(
                        "Status", ["OK", "Minor", "Major", "Kritis"],
                        key=f"status_{item}", horizontal=True, label_visibility="collapsed"
                    )
                with col3:
                    file_foto = st.file_uploader("Foto Temuan", key=f"foto_{item}", label_visibility="collapsed")
                    keterangan = st.text_input("Catatan", key=f"note_{item}", label_visibility="collapsed", placeholder="Catatan...")

                # Hitung Pinalti
                score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                total_deduction += score_map[pilihan]
                
                if pilihan != "OK":
                    audit_results.append({"Kategori": cat_name, "Kriteria": item, "Status": pilihan, "Catatan": keterangan})

    submitted = st.form_submit_button("Submit & Hitung Skor")

# Tampilkan Hasil Setelah Submit
if submitted:
    skor_akhir = max(0, 1000 + total_deduction)
    
    if skor_akhir >= 860: kategori, color = "A (Sangat Baik)", "green"
    elif skor_akhir >= 710: kategori, color = "B (Baik)", "blue"
    elif skor_akhir >= 610: kategori, color = "C (Cukup)", "orange"
    else: kategori, color = "D (Kurang)", "red"

    st.header("Ringkasan Hasil")
    c1, c2 = st.columns(2)
    c1.metric("Skor Akhir", f"{skor_akhir} / 1000")
    c2.markdown(f"### Kategori: :{color}[{kategori}]")

    if audit_results:
        st.write("### Daftar Temuan (CAPA):")
        st.table(pd.DataFrame(audit_results))
