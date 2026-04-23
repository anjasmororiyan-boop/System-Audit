import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="GMP Audit System & Dashboard", layout="wide")

# --- 1. SIMULASI DATABASE (Session State) ---
if 'audit_db' not in st.session_state:
    # Data dummy untuk simulasi perbandingan (Audit Terdahulu)
    st.session_state.audit_db = pd.DataFrame([
        {"Lokasi": "Satelite Kitchen NICE PIK2", "Tanggal": "2026-03-01", "Skor": 850, "Grade": "B"},
        {"Lokasi": "Central Kitchen Hub", "Tanggal": "2026-03-15", "Skor": 910, "Grade": "A"},
        {"Lokasi": "Satelite Kitchen NICE PIK2", "Tanggal": "2026-04-10", "Skor": 780, "Grade": "B"}
    ])

# --- 2. NAVIGATION ---
menu = st.sidebar.selectbox("Pilih Menu", ["📝 Audit Baru", "📊 Dashboard & Report"])

# --- 3. MENU 1: AUDIT BARU ---
if menu == "📝 Audit Baru":
    st.title("🛡️ Input Audit GMP Baru")
    
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal_audit = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        df_template = pd.read_csv(uploaded_file, sep=';')
        total_deduction = 0
        
        # Form Audit (Simplified for Mockup)
        for kategori, group in df_template.groupby('Kategori', sort=False):
            with st.expander(f"📂 {kategori}"):
                for _, row in group.iterrows():
                    col_t, col_s = st.columns([7, 3])
                    col_t.write(f"{row['No']}. {row['Kriteria Penilaian']}")
                    res = col_s.radio("Hasil", ["OK", "Minor", "Major", "Kritis"], key=f"src_{row['No']}_{kategori}", horizontal=True)
                    
                    score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += score_map[res]

        if st.button("Simpan Hasil Audit"):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            # Simpan ke 'Database'
            new_data = {"Lokasi": lokasi, "Tanggal": str(tanggal_audit), "Skor": skor_akhir, "Grade": grade}
            st.session_state.audit_db = pd.concat([st.session_state.audit_db, pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"Audit Berhasil Disimpan! Skor: {skor_akhir}")
    else:
        st.warning("Upload template untuk memulai.")

# --- 4. MENU 2: DASHBOARD & REPORT ---
else:
    st.title("📊 Dashboard Analisis Audit")

    # --- FILTER ---
    st.subheader("🔍 Filter Data")
    c1, c2 = st.columns(2)
    with c1:
        f_lokasi = st.multiselect("Pilih Lokasi", options=st.session_state.audit_db["Lokasi"].unique(), default=st.session_state.audit_db["Lokasi"].unique())
    with c2:
        # Filter data berdasarkan lokasi
        df_filtered = st.session_state.audit_db[st.session_state.audit_db["Lokasi"].isin(f_lokasi)]
        st.write(f"Menampilkan {len(df_filtered)} data audit.")

    # --- KPI METRICS ---
    st.divider()
    if not df_filtered.empty:
        latest_audit = df_filtered.iloc[-1]
        prev_audit = df_filtered.iloc[-2] if len(df_filtered) > 1 else latest_audit
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Skor Audit Terakhir", latest_audit['Skor'], delta=int(latest_audit['Skor'] - prev_audit['Skor']))
        m2.metric("Grade", latest_audit['Grade'])
        m3.metric("Total Inspeksi", len(df_filtered))

        # --- COMPARISON CHART (Last vs New) ---
        st.subheader("📈 Perbandingan Hasil Audit (Timeline)")
        fig = px.line(df_filtered, x="Tanggal", y="Skor", color="Lokasi", markers=True, 
                      title="Tren Skor GMP per Lokasi", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # --- TABEL SUMMARY ---
        st.subheader("📋 History Report")
        st.dataframe(df_filtered.sort_values(by="Tanggal", ascending=False), use_container_width=True)
        
        # Tombol Download
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("Download Report (.CSV)", data=csv, file_name="Report_Audit_GMP.csv", mime="text/csv")
    else:
        st.error("Tidak ada data untuk lokasi yang dipilih.")
