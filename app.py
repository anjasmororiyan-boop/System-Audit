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

        # Render Form Audit
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

        # --- KALKULASI PENILAIAN DI BAWAH TEMUAN ---
        st.divider()
        st.subheader("🧮 Summary Temuan & Kalkulasi")
        
        # Tampilkan Tabel Ringkasan Temuan Non-OK
        df_temuan = pd.DataFrame([i for i in temp_audit_entries if i["Status"] != "OK"])
        if not df_temuan.empty:
            st.warning("Daftar Temuan Ketidaksesuaian:")
            st.table(df_temuan[["No", "Kriteria", "Status", "Catatan"]])
        else:
            st.success("Tidak ada temuan ketidaksesuaian (Semua OK).")

        # Perhitungan Skor
        ded_minor = counts["Minor"] * 10
        ded_major = counts["Major"] * 20
        ded_kritis = counts["Kritis"] * 30
        total_deduction = ded_minor + ded_major + ded_kritis
        skor_akhir = max(0, 1000 - total_deduction)
        
        if skor_akhir >= 860: grade = "A (Sangat Baik)"
        elif skor_akhir >= 710: grade = "B (Baik)"
        elif skor_akhir >= 610: grade = "C (Cukup)"
        else: grade = "D (Kurang)"

        # Tampilan Metrik Skor
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Minor (-10)", f"{counts['Minor']}", f"-{ded_minor}")
        col_b.metric("Major (-20)", f"{counts['Major']}", f"-{ded_major}")
        col_c.metric("Kritis (-30)", f"{counts['Kritis']}", f"-{ded_kritis}")
        col_d.metric("SKOR AKHIR", f"{skor_akhir}", f"Grade: {grade}")

        # --- TOMBOL SIMPAN (Pastikan Muncul) ---
        st.divider()
        if st.button("💾 SIMPAN DATA HASIL AUDIT", use_container_width=True):
            master_record = {
                "Audit_ID": f"AUD-{datetime.now().strftime('%Y%m%d%H%M')}",
                "Lokasi": lokasi, "Tanggal": str(tanggal), "Auditor": auditor,
                "Skor_Akhir": skor_akhir, "Grade": grade,
                "Detail_Penilaian": temp_audit_entries
            }
            st.session_state.master_audit_data.append(master_record)
            st.balloons()
            st.success(f"Audit ID {master_record['Audit_ID']} Berhasil Disimpan!")
    else:
        st.info("Silakan unggah file template CSV di sidebar untuk memulai.")

# --- 5. MODULE: MONITORING PERBAIKAN (CAPA) ---
elif menu == "🛠️ Monitoring Perbaikan (CAPA)":
    st.title("🛠️ Perbaikan & Verifikasi (CAPA)")
    if st.session_state.master_audit_data:
        df_m = pd.DataFrame(st.session_state.master_audit_data)
        sel_id = st.selectbox("Pilih ID Audit untuk Tindak Lanjut", df_m['Audit_ID'])
        
        idx = next(i for i, item in enumerate(st.session_state.master_audit_data) if item["Audit_ID"] == sel_id)
        audit_data = st.session_state.master_audit_data[idx]
        temuan = [i for i in audit_data["Detail_Penilaian"] if i["Status"] != "OK"]
        
        if temuan:
            for i, item in enumerate(temuan):
                with st.container(border=True):
                    c_left, c_right = st.columns(2)
                    with c_left:
                        st.error(f"**Temuan {item['No']} - {item['Status']}**")
                        st.write(f"Kriteria: {item['Kriteria']}")
                        st.write(f"Masalah: {item['Catatan']}")
                        if item['Foto_Temuan']: st.image(item['Foto_Temuan'], width=250, caption="Foto Saat Audit")
                    with c_right:
                        # Bagian Auditee mengisi perbaikan
                        capa_text = st.text_area("Tindakan Perbaikan", value=item['Tindakan_Perbaikan'], key=f"cp_{sel_id}_{i}")
                        capa_img = st.file_uploader("Upload Foto Perbaikan (After)", type=['jpg','png','jpeg'], key=f"cpi_{sel_id}_{i}")
                        if capa_img: st.image(capa_img, width=250, caption="Bukti Perbaikan")
                        
                        capa_stat = st.selectbox("Status Verifikasi", ["Open", "Closed"], index=0 if item['Status_Perbaikan']=="Open" else 1, key=f"cps_{sel_id}_{i}")
                        
                        # Simpan balik ke state
                        item['Tindakan_Perbaikan'] = capa_text
                        item['Foto_Perbaikan'] = capa_img if capa_img else item['Foto_Perbaikan']
                        item['Status_Perbaikan'] = capa_stat
            
            if st.button("Update Progress CAPA"):
                st.success("Data monitoring berhasil diperbarui!")
        else:
            st.success("✅ Tidak ada temuan yang perlu diperbaiki.")
    else:
        st.info("Belum ada data audit di database.")

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
