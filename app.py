import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

st.set_page_config(page_title="GMP Audit System - Final Fix", layout="wide")

# --- DATABASE SIMULATION ---
if 'audit_db' not in st.session_state:
    st.session_state.audit_db = pd.DataFrame(columns=["Lokasi", "Tanggal", "Skor", "Grade"])

# --- FUNGSI GENERATE KEY UNIK ---
def make_unique_key(cat, area, no, criteria):
    # Membuat string unik lalu di-hash agar tidak ada karakter ilegal bagi Streamlit
    raw_str = f"{cat}{area}{no}{criteria}"
    return hashlib.md5(raw_str.encode()).hexdigest()

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Pilih Menu", ["📝 Audit Baru", "📊 Dashboard & Report"])

if menu == "📝 Audit Baru":
    st.title("🛡️ Input Audit GMP Baru")
    
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        st.header("📝 Info Audit")
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal_audit = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file is not None:
        df_template = pd.read_csv(uploaded_file, sep=';')
        total_deduction = 0
        audit_records = []

        # Form Audit
        for kategori, group_kategori in df_template.groupby('Kategori', sort=False):
            with st.expander(f"📂 {kategori}", expanded=True):
                for _, row in group_kategori.iterrows():
                    # Generate ID yang benar-benar unik dan aman
                    u_id = make_unique_key(kategori, row['Area'], row['No'], row['Kriteria Penilaian'])

                    st.markdown(f"**{row['No']} {row['Kriteria Penilaian']}**")
                    st.caption(f"Area: {row['Area']}")
                    
                    col_s, col_n, col_p = st.columns([2, 3, 2])
                    
                    with col_s:
                        pilihan = st.radio("Status", ["OK", "Minor", "Major", "Kritis"], key=f"s_{u_id}", horizontal=True)
                    
                    with col_n:
                        detail = st.text_area("Detail Temuan", key=f"n_{u_id}", height=70, placeholder="Wajib diisi jika tidak OK...")
                    
                    with col_p:
                        # File uploader untuk foto (mendukung kamera HP)
                        foto = st.file_uploader("Bukti Foto", type=["jpg","png","jpeg"], key=f"i_{u_id}")
                        if foto: st.image(foto, width=150)

                    # Hitung skor
                    score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += score_map[pilihan]
                    
                    if pilihan != "OK":
                        audit_records.append({
                            "Kategori": kategori, "No": row['No'], "Status": pilihan, "Detail": detail
                        })
                st.divider()

        if st.button("Simpan Hasil Audit", use_container_width=True):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            # Simpan ke State
            new_entry = {"Lokasi": lokasi, "Tanggal": str(tanggal_audit), "Skor": skor_akhir, "Grade": grade}
            st.session_state.audit_db = pd.concat([st.session_state.audit_db, pd.DataFrame([new_entry])], ignore_index=True)
            
            st.success(f"Audit Tersimpan! Skor: {skor_akhir} (Grade {grade})")
            if audit_records:
                st.subheader("Ringkasan Temuan")
                st.table(pd.DataFrame(audit_records))
    else:
        st.warning("Silakan unggah template CSV di sidebar.")

else:
    st.title("📊 Dashboard & Report")
    
    if not st.session_state.audit_db.empty:
        # Filter & Grafik
        sel_loc = st.selectbox("Pilih Lokasi", st.session_state.audit_db["Lokasi"].unique())
        df_view = st.session_state.audit_db[st.session_state.audit_db["Lokasi"] == sel_loc].sort_values("Tanggal")
        
        # Grafik Perbandingan
        fig = px.line(df_view, x="Tanggal", y="Skor", markers=True, title=f"Tren Kualitas GMP - {sel_loc}")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Data History")
        st.dataframe(df_view, use_container_width=True)
    else:
        st.info("Belum ada data. Silakan lakukan audit terlebih dahulu.")
