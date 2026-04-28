import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# --- KONFIGURASI ---
st.set_page_config(page_title="GMP Audit & CAPA System", layout="wide")

# --- 1. DATABASE LENGKAP (Session State) ---
if 'master_audit_data' not in st.session_state:
    st.session_state.master_audit_data = []

# --- 2. FUNGSI UNIK ID ---
def generate_id(cat, area, no, crit):
    raw_str = f"{cat}{area}{no}{crit}"
    return hashlib.md5(raw_str.encode()).hexdigest()

# --- 3. NAVIGATION ---
st.sidebar.title("🛡️ GMP Digital Hub")
menu = st.sidebar.radio("Pilih Module", [
    "📝 Audit Baru", 
    "🛠️ Monitoring Perbaikan (CAPA)", 
    "📁 Data Master & Report", 
    "📊 Dashboard Analisis"
])

# --- 4. MODULE: AUDIT BARU ---
if menu == "📝 Audit Baru":
    st.title("Input Audit GMP & Penilaian")
    
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=';')
        temp_audit_entries = []
        
        # Counter untuk Kalkulasi
        counts = {"Minor": 0, "Major": 0, "Kritis": 0}

        for kategori, group in df.groupby('Kategori', sort=False):
            with st.expander(f"📂 {kategori}", expanded=True):
                for _, row in group.iterrows():
                    u_id = generate_id(kategori, row['Area'], row['No'], row['Kriteria Penilaian'])
                    st.markdown(f"**{row['No']} {row['Kriteria Penilaian']}**")
                    
                    c1, c2, c3 = st.columns([2, 3, 2])
                    with c1:
                        res = st.radio("Status", ["OK", "Minor", "Major", "Kritis"], key=f"s_{u_id}", horizontal=True)
                    with c2:
                        note = st.text_area("Catatan Temuan", key=f"n_{u_id}", height=70)
                    with c3:
                        img = st.file_uploader("Foto Temuan", type=['jpg','png','jpeg'], key=f"img_t_{u_id}")
                        if img: st.image(img, width=100)

                    if res != "OK":
                        counts[res] += 1

                    temp_audit_entries.append({
                        "ID_Item": u_id, "Kategori": kategori, "No": row['No'], "Area": row['Area'],
                        "Kriteria": row['Kriteria Penilaian'], "Status": res, "Catatan": note,
                        "Foto_Temuan": img, "Tindakan_Perbaikan": "", "Foto_Perbaikan": None,
                        "Status_Perbaikan": "Open" if res != "OK" else "N/A"
                    })
   
# --- 6. MODULE: DATA MASTER & REPORT ---
elif menu == "📁 Data Master & Report":
    st.title("Data Master Audit")
    if st.session_state.master_audit_data:
        df_master = pd.DataFrame(st.session_state.master_audit_data)
        st.dataframe(df_master.drop(columns=['Detail_Penilaian']), use_container_width=True)
        
        selected_audit = st.selectbox("Lihat Detail & Progress Perbaikan", df_master['Audit_ID'])
        detail_data = next(item for item in st.session_state.master_audit_data if item["Audit_ID"] == selected_audit)
        st.table(pd.DataFrame(detail_data["Detail_Penilaian"]))
    else:
        st.info("Database kosong.")

# --- 7. MODULE: DASHBOARD ANALISIS ---
else:
    st.title("📊 Dashboard Analisis")
    if st.session_state.master_audit_data:
        df_dash = pd.DataFrame(st.session_state.master_audit_data)
        loc = st.selectbox("Lokasi", df_dash['Lokasi'].unique())
        df_loc = df_dash[df_dash['Lokasi'] == loc].sort_values('Tanggal')
        
        st.plotly_chart(px.line(df_loc, x="Tanggal", y="Skor_Akhir", markers=True, title="Tren Skor GMP"))
        
        # Summary Status Perbaikan
        total_temuan = sum([len([i for i in a["Detail_Penilaian"] if i["Status"] != "OK"]) for a in st.session_state.master_audit_data])
        total_closed = sum([len([i for i in a["Detail_Penilaian"] if i["Status_Perbaikan"] == "Closed"]) for a in st.session_state.master_audit_data])
        
        c1, c2 = st.columns(2)
        c1.metric("Total Temuan Seluruh Lokasi", total_temuan)
        c2.metric("Temuan Selesai Diperbaiki", total_closed, delta=f"{total_closed - total_temuan}")
