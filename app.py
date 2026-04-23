import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GMP Audit & Analytics System", layout="wide")

# --- 1. PERSISTENCE LAYER (Simulasi Database) ---
# Menggunakan session_state agar data tersimpan selama aplikasi berjalan
if 'audit_history' not in st.session_state:
    # Data awal untuk simulasi dashboard
    st.session_state.audit_history = []

# --- 2. FUNGSI UNIK ID (Mencegah Error Duplicate Widget) ---
def generate_id(cat, area, no, crit):
    raw_str = f"{cat}{area}{no}{crit}"
    return hashlib.md5(raw_str.encode()).hexdigest()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ GMP Management")
menu = st.sidebar.radio("Pilih Module", ["📝 Audit Baru", "📊 Dashboard & Comparison", "📁 Database Report Master"])

# --- 4. MODULE: AUDIT BARU ---
if menu == "📝 Audit Baru":
    st.title("Input Audit Keamanan Pangan Baru")
    
    with st.sidebar:
        st.header("Konfigurasi")
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        st.header("Informasi Audit")
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub", "Outlet Retail"])
        auditor = st.text_input("Nama Auditor")
        tanggal_audit = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        # Menggunakan delimiter ; sesuai template Anda
        df = pd.read_csv(uploaded_file, sep=';')
        total_deduction = 0
        findings_summary = []

        for kategori, group in df.groupby('Kategori', sort=False):
            with st.expander(f"📂 Kategori: {kategori}", expanded=True):
                for _, row in group.iterrows():
                    # Generate ID unik untuk menghindari DuplicateWidgetID
                    u_id = generate_id(kategori, row['Area'], row['No'], row['Kriteria Penilaian'])
                    
                    st.markdown(f"**{row['No']} {row['Kriteria Penilaian']}** (Area: {row['Area']})")
                    col1, col2, col3 = st.columns([2, 3, 2])
                    
                    with col1:
                        res = st.radio("Hasil", ["OK", "Minor", "Major", "Kritis"], key=f"s_{u_id}", horizontal=True)
                    with col2:
                        note = st.text_area("Detail Temuan", key=f"n_{u_id}", height=70, placeholder="Wajib dicatat jika ada temuan...")
                    with col3:
                        img = st.file_uploader("Ambil/Upload Foto", type=['jpg','png','jpeg'], key=f"i_{u_id}")
                        if img: st.image(img, width=150)

                    # Logic Scoring sesuai standar Anda
                    points = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += points[res]
                    
                    if res != "OK":
                        findings_summary.append({
                            "Kategori": kategori, "No": row['No'], "Status": res, "Detail": note
                        })

        if st.button("💾 SIMPAN HASIL AUDIT KE DATABASE", use_container_width=True):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            # Record Data untuk Dashboard
            entry_audit = {
                "Lokasi": lokasi,
                "Tanggal": str(tanggal_audit),
                "Auditor": auditor,
                "Skor": skor_akhir,
                "Grade": grade,
                "Total Temuan": len(findings_summary)
            }
            st.session_state.audit_history.append(entry_audit)
            
            st.success(f"Audit Berhasil Disimpan! Skor: {skor_akhir} | Grade: {grade}")
            if findings_summary:
                st.subheader("📋 Ringkasan Temuan Lapangan")
                st.table(pd.DataFrame(findings_summary))
    else:
        st.info("Silakan unggah file 'Template Checklist.csv' di sidebar untuk memulai.")

# --- 5. MODULE: DASHBOARD & COMPARISON ---
elif menu == "📊 Dashboard & Comparison":
    st.title("Dashboard Analisis & Perbandingan")
    
    if st.session_state.audit_history:
        df_hist = pd.DataFrame(st.session_state.audit_history)
        df_hist['Tanggal'] = pd.to_datetime(df_hist['Tanggal'])
        
        target_loc = st.selectbox("Pilih Lokasi untuk Analisis", df_hist['Lokasi'].unique())
        df_loc = df_hist[df_hist['Lokasi'] == target_loc].sort_values('Tanggal')

        if len(df_loc) >= 1:
            # Mengambil Audit Terbaru (New) dan Audit Sebelumnya (Last)
            new_audit = df_loc.iloc[-1]
            
            st.divider()
            st.subheader(f"Statistik Terakhir: {target_loc}")
            c1, c2, c3 = st.columns(3)
            
            if len(df_loc) > 1:
                last_audit = df_loc.iloc[-2]
                diff_skor = int(new_audit['Skor'] - last_audit['Skor'])
                diff_temuan = int(new_audit['Total Temuan'] - last_audit['Total Temuan'])
                
                c1.metric("Skor Audit Terbaru", f"{new_audit['Skor']}", delta=diff_skor)
                c2.metric("Grade", new_audit['Grade'])
                c3.metric("Total Temuan", f"{new_audit['Total Temuan']} Item", delta=diff_temuan, delta_color="inverse")
            else:
                c1.metric("Skor Audit Terbaru", new_audit['Skor'])
                c2.metric("Grade", new_audit['Grade'])
                c3.metric("Total Temuan", f"{new_audit['Total Temuan']} Item")

            # Chart Tren Visual
            st.subheader("Tren Performa Keamanan Pangan (Timeline)")
            fig = px.line(df_loc, x="Tanggal", y="Skor", markers=True, text="Skor", 
                          title=f"Grafik Skor GMP - {target_loc}", template="plotly_white")
            fig.update_traces(textposition="bottom right")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Data database masih kosong. Lakukan audit pertama Anda!")

# --- 6. MODULE: DATABASE REPORT MASTER ---
else:
    st.title("📁 Master Data Report")
    if st.session_state.audit_history:
        full_df = pd.DataFrame(st.session_state.audit_history)
        st.write("Semua data yang tersimpan di sistem:")
        st.dataframe(full_df, use_container_width=True)
        
        # Fitur Export
        csv_data = full_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Master Report (CSV)", data=csv_data, file_name="GMP_Master_Report.csv", mime="text/csv")
    else:
        st.info("Belum ada data di database.")
