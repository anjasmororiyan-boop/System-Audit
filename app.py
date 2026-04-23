import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# --- KONFIGURASI ---
st.set_page_config(page_title="GMP Audit Master System", layout="wide")

# --- 1. DATABASE LENGKAP (Session State) ---
if 'master_audit_data' not in st.session_state:
    st.session_state.master_audit_data = [] # Menyimpan list of dictionaries (Lengkap)

# --- 2. FUNGSI UNIK ID ---
def generate_id(cat, area, no, crit):
    raw_str = f"{cat}{area}{no}{crit}"
    return hashlib.md5(raw_str.encode()).hexdigest()

# --- 3. NAVIGATION ---
st.sidebar.title("🛡️ GMP Digital Hub")
menu = st.sidebar.radio("Pilih Module", ["📝 Audit Baru", "📁 Data Master & Report", "📊 Dashboard Analisis"])

# --- 4. MODULE: AUDIT BARU ---
if menu == "📝 Audit Baru":
    st.title("Input Audit GMP Lengkap")
    
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=';')
        temp_audit_entries = [] # Menampung sementara baris per baris
        total_deduction = 0

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
                        img = st.file_uploader("Foto Bukti", type=['jpg','png','jpeg'], key=f"i_{u_id}")

                    # Hitung Skor
                    points = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += points[res]

                    # Masukkan ke list detail
                    temp_audit_entries.append({
                        "Kategori": kategori,
                        "No": row['No'],
                        "Area": row['Area'],
                        "Kriteria": row['Kriteria Penilaian'],
                        "Status": res,
                        "Catatan": note,
                        "Foto_Ada": "Ya" if img else "Tidak"
                    })

        if st.button("💾 SIMPAN KE DATA MASTER", use_container_width=True):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            # Bungkus semua detail ke dalam satu record master
            master_record = {
                "Audit_ID": f"AUD-{datetime.now().strftime('%Y%m%d%H%M')}",
                "Lokasi": lokasi,
                "Tanggal": str(tanggal),
                "Auditor": auditor,
                "Skor_Akhir": skor_akhir,
                "Grade": grade,
                "Detail_Penilaian": temp_audit_entries # Menyimpan list di dalam kolom
            }
            st.session_state.master_audit_data.append(master_record)
            st.success("Data Master Berhasil Disimpan Lengkap dengan Seluruh Penilaian!")

# --- 5. MODULE: DATA MASTER & REPORT ---
elif menu == "📁 Data Master & Report":
    st.title("Data Master Audit GMP")
    
    if st.session_state.master_audit_data:
        # Tampilkan Ringkasan Terlebih Dahulu
        df_master = pd.DataFrame(st.session_state.master_audit_data)
        st.subheader("Semua History Audit")
        st.dataframe(df_master.drop(columns=['Detail_Penilaian']), use_container_width=True)

        st.divider()
        st.subheader("🔍 Lihat Detail Form Per Audit")
        selected_audit = st.selectbox("Pilih ID Audit untuk Melihat Form Lengkap", df_master['Audit_ID'])
        
        # Tampilkan detail penilaian dari audit yang dipilih
        detail_data = next(item for item in st.session_state.master_audit_data if item["Audit_ID"] == selected_audit)
        df_detail = pd.DataFrame(detail_data["Detail_Penilaian"])
        
        st.write(f"**Laporan Detail untuk {detail_data['Lokasi']} (Tanggal: {detail_data['Tanggal']})**")
        st.table(df_detail)
        
        # Download Button
        csv = df_detail.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Form Ini (CSV)", csv, f"Report_{selected_audit}.csv")
    else:
        st.info("Belum ada data di Master.")

# --- 6. MODULE: DASHBOARD ANALISIS ---
else:
    st.title("📊 Dashboard Perbandingan")
    if st.session_state.master_audit_data:
        df_dash = pd.DataFrame(st.session_state.master_audit_data)
        loc = st.selectbox("Pilih Lokasi", df_dash['Lokasi'].unique())
        df_loc = df_dash[df_dash['Lokasi'] == loc].sort_values('Tanggal')

        if len(df_loc) > 0:
            new = df_loc.iloc[-1]
            c1, c2 = st.columns(2)
            
            if len(df_loc) > 1:
                last = df_loc.iloc[-2]
                c1.metric("Skor Audit Baru", new['Skor_Akhir'], delta=int(new['Skor_Akhir'] - last['Skor_Akhir']))
                c2.metric("Perubahan Grade", new['Grade'], help="Dibandingkan dengan audit sebelumnya")
            else:
                c1.metric("Skor Audit Baru", new['Skor_Akhir'])
                c2.metric("Grade", new['Grade'])

            st.plotly_chart(px.line(df_loc, x="Tanggal", y="Skor_Akhir", markers=True, title="Tren Kualitas GMP"))
