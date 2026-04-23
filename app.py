import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="GMP Audit System", layout="wide")

# --- DATABASE SIMULATION ---
if 'audit_db' not in st.session_state:
    st.session_state.audit_db = pd.DataFrame(columns=["Lokasi", "Tanggal", "Skor", "Grade"])

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Pilih Menu", ["📝 Audit Baru", "📊 Dashboard & Report"])

if menu == "📝 Audit Baru":
    st.title("🛡️ Input Audit GMP Baru")
    
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal_audit = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file is not None:
        # Load template dengan delimiter ;
        df_template = pd.read_csv(uploaded_file, sep=';')
        total_deduction = 0
        audit_records = []

        # Form Audit
        for kategori, group_kategori in df_template.groupby('Kategori', sort=False):
            with st.expander(f"📂 {kategori}", expanded=True):
                for _, row in group_kategori.iterrows():
                    # Membuat Key Unik agar tidak Error DuplicateWidgetID
                    # Menghilangkan karakter aneh agar key aman
                    clean_cat = str(kategori)[:10].replace(" ", "")
                    unique_key = f"{clean_cat}_{row['No']}_{row['Area']}".replace(".", "")

                    st.markdown(f"**{row['No']}. {row['Kriteria Penilaian']}** (Area: {row['Area']})")
                    
                    col_s, col_n, col_p = st.columns([2, 3, 2])
                    
                    with col_s:
                        pilihan = st.radio("Hasil", ["OK", "Minor", "Major", "Kritis"], key=f"stat_{unique_key}", horizontal=True)
                    
                    with col_n:
                        # Keterangan detail temuan
                        detail = st.text_area("Detail Temuan", key=f"note_{unique_key}", height=70, placeholder="Catat detail di sini...")
                    
                    with col_p:
                        # Foto kamera (Mobile Friendly)
                        foto = st.file_uploader("Foto Bukti", type=["jpg","png","jpeg"], key=f"img_{unique_key}")
                        if foto: st.image(foto, width=100)

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
            
            new_data = {"Lokasi": lokasi, "Tanggal": str(tanggal_audit), "Skor": skor_akhir, "Grade": grade}
            st.session_state.audit_db = pd.concat([st.session_state.audit_db, pd.DataFrame([new_data])], ignore_index=True)
            
            st.success(f"Audit Berhasil Disimpan! Skor Akhir: {skor_akhir}")
            if audit_records:
                st.table(pd.DataFrame(audit_records))
    else:
        st.warning("Silakan upload template CSV di sidebar.")

# --- DASHBOARD & COMPARISON ---
else:
    st.title("📊 Dashboard Analisis Audit")
    
    if not st.session_state.audit_db.empty:
        # Filter Lokasi
        list_lokasi = st.session_state.audit_db["Lokasi"].unique()
        sel_lokasi = st.selectbox("Pilih Lokasi untuk Perbandingan", list_lokasi)
        
        df_plot = st.session_state.audit_db[st.session_state.audit_db["Lokasi"] == sel_lokasi].sort_values("Tanggal")
        
        # Metrics
        if len(df_plot) >= 1:
            latest = df_plot.iloc[-1]
            prev = df_plot.iloc[-2] if len(df_plot) > 1 else latest
            
            m1, m2 = st.columns(2)
            m1.metric("Skor Terakhir", latest['Skor'], delta=int(latest['Skor'] - prev['Skor']))
            m2.metric("Grade", latest['Grade'])

            # Chart Comparison
            st.subheader(f"Tren Skor Audit: {sel_lokasi}")
            fig = px.line(df_plot, x="Tanggal", y="Skor", markers=True, text="Skor")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("History Report")
            st.dataframe(df_plot, use_container_width=True)
    else:
        st.info("Belum ada data audit yang disimpan.")
