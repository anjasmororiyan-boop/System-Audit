import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="GMP Audit & CAPA System", layout="wide")

# --- 1. DATABASE (Session State) ---
if 'master_audit_data' not in st.session_state:
    st.session_state.master_audit_data = []

# --- 2. FUNGSI UNIK ID ---
def generate_id(cat, area, no, crit):
    raw_str = f"{cat}{area}{no}{crit}"
    return hashlib.md5(raw_str.encode()).hexdigest()

# --- 3. SIDEBAR NAVIGATION ---
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
        st.header("Konfigurasi")
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep=';')
        temp_audit_entries = []
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

        # --- SUMMARY & KALKULASI DI BAWAH HASIL AUDIT ---
        st.divider()
        st.subheader("📊 Hasil Penilaian & Summary Temuan")
        
        skor_akhir = max(0, 1000 - (counts["Minor"]*10 + counts["Major"]*20 + counts["Kritis"]*30))
        
        if skor_akhir >= 860: grade, color = "A (Sangat Baik)", "green"
        elif skor_akhir >= 710: grade, color = "B (Baik)", "blue"
        elif skor_akhir >= 610: grade, color = "C (Cukup)", "orange"
        else: grade, color = "D (Kurang)", "red"

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Minor", counts["Minor"])
        col_b.metric("Major", counts["Major"])
        col_c.metric("Kritis", counts["Kritis"])
        col_d.metric("SKOR AKHIR", skor_akhir, grade)
        
        st.markdown(f"**Grade Final: :{color}[{grade}]**")

        # Tabel Summary Temuan Non-OK
        df_summary = pd.DataFrame([i for i in temp_audit_entries if i["Status"] != "OK"])
        if not df_summary.empty:
            st.warning("⚠️ Daftar Temuan yang Harus Diperbaiki:")
            st.table(df_summary[["Kategori", "No", "Kriteria", "Status", "Catatan"]])
        else:
            st.success("✅ Sempurna! Tidak ada temuan ketidaksesuaian.")

        # Tombol Simpan
        if st.button("💾 SIMPAN DATA HASIL AUDIT", use_container_width=True):
            master_record = {
                "Audit_ID": f"AUD-{datetime.now().strftime('%Y%m%d%H%M')}",
                "Lokasi": lokasi, "Tanggal": str(tanggal), "Auditor": auditor,
                "Skor_Akhir": skor_akhir, "Grade": grade, 
                "Detail_Penilaian": temp_audit_entries,
                "Summary_Temuan": df_summary.to_dict('records') if not df_summary.empty else []
            }
            st.session_state.master_audit_data.append(master_record)
            st.balloons()
            st.success("Audit Berhasil Disimpan ke Data Master!")
    else:
        st.info("Silakan unggah file template CSV di sidebar.")

# --- 5. MODULE: MONITORING PERBAIKAN (CAPA) ---
elif menu == "🛠️ Monitoring Perbaikan (CAPA)":
    st.title("🛠️ Monitoring CAPA (Before vs After)")
    if st.session_state.master_audit_data:
        df_m = pd.DataFrame(st.session_state.master_audit_data)
        sel_id = st.selectbox("Pilih ID Audit", df_m['Audit_ID'])
        
        idx = next(i for i, item in enumerate(st.session_state.master_audit_data) if item["Audit_ID"] == sel_id)
        audit_data = st.session_state.master_audit_data[idx]
        temuan = [i for i in audit_data["Detail_Penilaian"] if i["Status"] != "OK"]
        
        if temuan:
            for i, item in enumerate(temuan):
                with st.container(border=True):
                    cl, cr = st.columns(2)
                    with cl:
                        st.error(f"**Temuan {item['No']} ({item['Status']})**")
                        st.write(f"Masalah: {item['Catatan']}")
                        if item['Foto_Temuan']: st.image(item['Foto_Temuan'], width=200)
                    with cr:
                        item['Tindakan_Perbaikan'] = st.text_area("Perbaikan", value=item['Tindakan_Perbaikan'], key=f"t_{sel_id}_{i}")
                        f_p = st.file_uploader("Foto Bukti Perbaikan", type=['jpg','png','jpeg'], key=f"f_{sel_id}_{i}")
                        if f_p: item['Foto_Perbaikan'] = f_p
                        item['Status_Perbaikan'] = st.selectbox("Status", ["Open", "Closed"], index=0 if item['Status_Perbaikan']=="Open" else 1, key=f"s_{sel_id}_{i}")
            
            if st.button("Update CAPA"):
                st.success("Progress perbaikan berhasil diperbarui!")
    else:
        st.info("Belum ada data audit.")

# --- 6. MODULE: DATA MASTER & REPORT ---
elif menu == "📁 Data Master & Report":
    st.title("📁 Database & Report Master")
    
    if st.session_state.master_audit_data:
        df_master = pd.DataFrame(st.session_state.master_audit_data)
        
        # Saring kolom untuk tampilan tabel utama agar tidak error
        cols_display = ["Audit_ID", "Lokasi", "Tanggal", "Auditor", "Skor_Akhir", "Grade"]
        st.subheader("History Audit")
        st.dataframe(df_master[cols_display], use_container_width=True)
        
        st.divider()
        sel_id = st.selectbox("Pilih Audit ID untuk Detail Temuan", df_master['Audit_ID'])
        
        # Ambil record data yang dipilih
        record = next(item for item in st.session_state.master_audit_data if item["Audit_ID"] == sel_id)
        
        # Tampilkan Summary Temuan (Non-OK) di layar
        st.subheader(f"Summary Temuan: {record['Lokasi']}")
        summary_data = record.get("Summary_Temuan", [])
        
        if summary_data:
            st.table(pd.DataFrame(summary_data)[["Kategori", "No", "Kriteria", "Status", "Catatan"]])
        else:
            st.success("Tidak ada temuan (Semua OK) untuk audit ini.")
            
        # --- PROSES DOWNLOAD EXCEL (PERBAIKAN) ---
        import io
        
        # 1. Buat buffer memori
        buffer = io.BytesIO()
        
        # 2. Gunakan ExcelWriter untuk menulis ke buffer
        full_df = pd.DataFrame(record["Detail_Penilaian"])
        csv_buffer = io.StringIO()
        full_df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        csv_data = csv_buffer.getvalue()
            
            # Tambahkan sheet ringkasan temuan jika ada
            if summary_data:
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Ringkasan_Temuan', index=False)
            
            # Atur lebar kolom agar rapi
            workbook = writer.book
            for sheet in writer.sheets.values():
                sheet.set_column('A:Z', 25)

        # 3. Tombol Download menggunakan data dari buffer
        st.download_button(
        label="📥 Download Detail Audit (CSV)",
        data=csv_data,
        file_name=f"Detail_Audit_{sel_id}.csv",
        mime="text/csv"
        )
    else:
        st.info("Belum ada data yang disimpan.")
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
