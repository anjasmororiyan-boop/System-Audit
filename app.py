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
    st.title("Input Audit GMP & Temuan")
    
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=';')
        temp_audit_entries = []
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
                        note = st.text_area("Catatan Temuan", key=f"n_{u_id}", height=70, placeholder="Wajib isi jika temuan...")
                    with c3:
                        img = st.file_uploader("Foto Bukti", type=['jpg','png','jpeg'], key=f"i_{u_id}")

                    points = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += points[res]

                    temp_audit_entries.append({
                        "ID_Item": u_id,
                        "Kategori": kategori,
                        "No": row['No'],
                        "Area": row['Area'],
                        "Kriteria": row['Kriteria Penilaian'],
                        "Status": res,
                        "Catatan": note,
                        "Foto_Ada": "Ya" if img else "Tidak",
                        "Tindakan_Perbaikan": "", # Akan diisi di module CAPA
                        "Status_Perbaikan": "Open" if res != "OK" else "N/A"
                    })

        if st.button("💾 SIMPAN KE DATA MASTER", use_container_width=True):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            master_record = {
                "Audit_ID": f"AUD-{datetime.now().strftime('%Y%m%d%H%M')}",
                "Lokasi": lokasi,
                "Tanggal": str(tanggal),
                "Auditor": auditor,
                "Skor_Akhir": skor_akhir,
                "Grade": grade,
                "Detail_Penilaian": temp_audit_entries
            }
            st.session_state.master_audit_data.append(master_record)
            st.success("Data Berhasil Disimpan!")
            
            # Summary Temuan Non-OK
            temuan_list = [item for item in temp_audit_entries if item["Status"] != "OK"]
            if temuan_list:
                st.warning(f"⚠️ Terdeteksi {len(temuan_list)} temuan yang memerlukan perbaikan.")
                st.table(pd.DataFrame(temuan_list)[["No", "Kriteria", "Status", "Catatan"]])

# --- 5. MODULE: MONITORING PERBAIKAN (CAPA) ---
elif menu == "🛠️ Monitoring Perbaikan (CAPA)":
    st.title("🛠️ Corrective & Preventive Action (CAPA)")
    st.write("Auditee mengisi perbaikan, Auditor melakukan monitoring.")

    if st.session_state.master_audit_data:
        df_m = pd.DataFrame(st.session_state.master_audit_data)
        sel_audit_id = st.selectbox("Pilih ID Audit untuk Tindak Lanjut", df_m['Audit_ID'])
        
        # Ambil referensi data audit yang dipilih
        idx = next(i for i, item in enumerate(st.session_state.master_audit_data) if item["Audit_ID"] == sel_audit_id)
        audit_data = st.session_state.master_audit_data[idx]
        
        # Filter hanya yang butuh perbaikan
        temuan_only = [i for i in audit_data["Detail_Penilaian"] if i["Status"] != "OK"]
        
        if temuan_only:
            for i, item in enumerate(temuan_only):
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.error(f"**Temuan {item['No']}**")
                        st.write(f"**Kriteria:** {item['Kriteria']}")
                        st.write(f"**Masalah:** {item['Catatan']}")
                    with c2:
                        # Input perbaikan oleh Auditee
                        perbaikan = st.text_area(f"Rencana Perbaikan (CAPA)", value=item['Tindakan_Perbaikan'], key=f"capa_{sel_audit_id}_{i}")
                        status_p = st.selectbox("Status Perbaikan", ["Open", "Closed"], index=0 if item['Status_Perbaikan']=="Open" else 1, key=f"stat_capa_{sel_audit_id}_{i}")
                        
                        # Update data langsung ke master
                        item['Tindakan_Perbaikan'] = perbaikan
                        item['Status_Perbaikan'] = status_p
            
            if st.button("Update Status Perbaikan"):
                st.success("Monitoring CAPA diperbarui!")
        else:
            st.success("✅ Tidak ada temuan yang memerlukan perbaikan untuk Audit ID ini.")
    else:
        st.info("Belum ada data audit.")

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
