import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM ---
st.set_page_config(page_title="Smart Audit Hub v5", layout="wide")

# Persistent Storage
if 'master_templates' not in st.session_state:
    st.session_state.master_templates = {} 
if 'audit_schedules' not in st.session_state:
    st.session_state.audit_schedules = []
if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []
if 'employee_db' not in st.session_state:
    st.session_state.employee_db = pd.DataFrame([
        {'Nama': 'Riyan Anjasmoro', 'Role': 'Auditor'},
        {'Nama': 'Yuka', 'Role': 'Auditee'}
    ])

# --- 2. FUNGSI PENDUKUNG ---
def calculate_score(results):
    max_score = 1000
    minor = sum(1 for r in results if r['status'] == 'Minor')
    major = sum(1 for r in results if r['status'] == 'Major')
    kritis = sum(1 for r in results if r['status'] == 'Kritis')
    total_pinalti = (minor * 10) + (major * 20) + (kritis * 30)
    final_score = max(0, max_score - total_pinalti)
    if final_score >= 860: grade = "A (Sangat Baik)"
    elif final_score >= 710: grade = "B (Baik)"
    elif final_score >= 610: grade = "C (Cukup)"
    else: grade = "D (Kurang)"
    return final_score, grade, (minor, major, kritis)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ Smart Audit System")
menu = st.sidebar.radio("Navigasi Module", [
    "📊 Dashboard & Outstanding",
    "⚙️ Module Master",
    "📅 Initiation & Scheduling",
    "📝 Execution (Phase 3)",
    "🛠️ Remediation (Phase 6)",
    "📄 Audit Report (Detail)"
])

# --- 4. MODULE: MASTER DATA ---
if menu == "⚙️ Module Master":
    st.title("⚙️ Module Master: Pusat Database")
    tab1, tab2 = st.tabs(["Master Form Audit", "Master Employee"])
    
    with tab1:
        st.subheader("1. Unduh Template Form")
        form_csv = "Kategori,No,Kriteria\nArea Luar,1.1,Lokasi bebas banjir\nProduksi,2.1,Lantai bersih"
        st.download_button("📥 Download Template Form (CSV)", form_csv, "template_form.csv")
        
        st.divider()
        st.subheader("2. Upload & Simpan Master Form")
        c1, c2 = st.columns(2)
        with c1:
            t_audit = st.selectbox("Tipe Audit", ["GMP", "SQA", "ISO", "K3"])
            l_audit = st.selectbox("Lokasi Mapping", ["NICE Hub", "Satelite Kitchen", "Central Kitchen"])
            uploaded_file = st.file_uploader("Upload Master CSV", type=["csv"])
            if uploaded_file and st.button("Simpan ke Database Form"):
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
                st.session_state.master_templates[f"{t_audit}_{l_audit}"] = df.to_dict('records')
                st.success(f"Form {t_audit} - {l_audit} Tersimpan!")

    with tab2:
        st.subheader("Daftar Auditor & Auditee")
        st.session_state.employee_db = st.data_editor(st.session_state.employee_db, num_rows="dynamic", use_container_width=True)

# --- 5. MODULE: INITIATION ---
elif menu == "📅 Initiation & Scheduling":
    st.title("📅 Inisiasi & Penjadwalan")
    st.subheader("1. Unduh Template Jadwal")
    sched_csv = "Audit_Title,Tipe,Lokasi,Auditor,Auditee,Tanggal\nAudit Mei,GMP,NICE Hub,Riyan Anjasmoro,Yuka,2026-05-30"
    st.download_button("📥 Download Template Jadwal (CSV)", sched_csv, "template_jadwal.csv")
    
    st.divider()
    st.subheader("2. Import Jadwal Audit")
    uploaded_sched = st.file_uploader("Upload File Jadwal", type=["csv"])
    if uploaded_sched and st.button("Proses Jadwal"):
        df_sched = pd.read_csv(uploaded_sched, sep=None, engine='python')
        for _, row in df_sched.iterrows():
            d = row.to_dict()
            d['Status'] = "Outstanding"
            st.session_state.audit_schedules.append(d)
        st.success("Jadwal Berhasil Ditambahkan!")

# --- 6. MODULE: DASHBOARD & OUTSTANDING ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Dashboard Utama & Monitoring")

    # --- BAGIAN 1: KPI METRICS ---
    st.subheader("📋 Ringkasan Status Audit")
    
    total_jadwal = len(st.session_state.audit_schedules)
    total_selesai = len([s for s in st.session_state.audit_schedules if s['Status'] == "Completed"])
    total_outstanding = len([s for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"])
    
    # Menghitung temuan yang belum diperbaiki di Phase 6
    temuan_pending = 0
    if st.session_state.audit_history:
        for audit in st.session_state.audit_history:
            for item in audit['Detail']:
                if item['status'] != 'OK':
                    # Jika tidak ada key 'capa_status' atau statusnya bukan 'Closed'
                    if 'capa_status' not in item or item['capa_status'] != 'Closed':
                        temuan_pending += 1

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jadwal", total_jadwal)
    m2.metric("Selesai (Completed)", total_selesai)
    m3.metric("Outstanding", total_outstanding, delta_color="inverse")
    m4.metric("Temuan Pending CAPA", temuan_pending, delta_color="inverse")

    st.divider()

    # --- BAGIAN 2: KOMPARASI HASIL AUDIT (DIPERBARUI) ---
    st.subheader("📈 Komparasi Hasil Audit")
    
    if st.session_state.audit_history:
        df_hist = pd.DataFrame(st.session_state.audit_history)
        
        # Filter interaktif untuk komparasi
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            list_lokasi = df_hist['Lokasi'].unique().tolist()
            sel_lokasi = st.multiselect("Lokasi", list_lokasi, default=list_lokasi)
        with c_f2:
            list_tipe = df_hist['Tipe'].unique().tolist()
            sel_tipe = st.multiselect("Tipe Audit", list_tipe, default=list_tipe)
        with c_f3:
            # Fitur Utama: Memilih spesifik Judul Audit untuk dibandingkan
            list_judul = df_hist['Audit_Title'].unique().tolist()
            sel_judul = st.multiselect("Bandingkan Judul Audit", list_judul, default=list_judul)
        
        # Filter Data
        df_filtered = df_hist[
            (df_hist['Lokasi'].isin(sel_lokasi)) & 
            (df_hist['Tipe'].isin(sel_tipe)) & 
            (df_hist['Audit_Title'].isin(sel_judul))
        ]
        
        if not df_filtered.empty:
            # Grafik Komparasi Berdasarkan Hasil Audit (Judul & Tanggal)
            fig = px.bar(
                df_filtered, 
                x="Audit_Title", # Sumbu X sekarang berdasarkan Judul Audit
                y="Skor", 
                color="Lokasi", 
                barmode="group",
                text="Skor",
                hover_data=["Tgl_Audit", "Grade", "Auditor"],
                title="Perbandingan Skor antar Hasil Audit"
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabel Perbandingan Singkat
            st.write("**Tabel Perbandingan Skor:**")
            st.dataframe(df_filtered[['Tgl_Audit', 'Audit_Title', 'Lokasi', 'Skor', 'Grade']], use_container_width=True)
        else:
            st.warning("Data tidak ditemukan untuk kombinasi filter tersebut.")
    else:
        st.info("Belum ada riwayat audit untuk dibandingkan.")

    st.divider()

    # --- BAGIAN 3: OUTSTANDING TASKS ---
    st.subheader("📌 Detail Jadwal Outstanding")
    outstanding_data = [s for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    if outstanding_data:
        for i, task in enumerate(st.session_state.audit_schedules):
            if task['Status'] == "Outstanding":
                with st.expander(f"🕒 {task['Audit_Title']} - {task['Lokasi']}"):
                    col_info, col_del = st.columns([4, 1])
                    col_info.write(f"Auditor: {task['Auditor']} | Auditee: {task['Auditee']} | Tipe: {task['Tipe']}")
                    if col_del.button("🗑️ Hapus", key=f"dash_del_{i}"):
                        st.session_state.audit_schedules.pop(i)
                        st.rerun()
    else:
        st.info("Tidak ada jadwal tertunda.")

# --- 7. MODULE: EXECUTION (PHASE 3) ---
elif menu == "📝 Execution (Phase 3)":
    st.title("📝 Eksekusi Audit")
    
    if 'audit_finalized' not in st.session_state:
        st.session_state.audit_finalized = False
    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None

    outstanding_tasks = [s for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    
    if outstanding_tasks:
        task_options = [t['Audit_Title'] for t in outstanding_tasks]
        sel_task_title = st.selectbox("Pilih Jadwal Audit", task_options)
        
        task_index = next(i for i, s in enumerate(st.session_state.audit_schedules) if s['Audit_Title'] == sel_task_title)
        task = st.session_state.audit_schedules[task_index]
        key = f"{task['Tipe']}_{task['Lokasi']}"
        
        if key in st.session_state.master_templates:
            checklist = st.session_state.master_templates[key]
            
            current_results = []
            for i, item in enumerate(checklist):
                with st.container(border=True):
                    st.write(f"**{item['No']}. {item['Kriteria']}**")
                    c1, c2, c3 = st.columns([1, 2, 1])
                    res_status = c1.radio("Status", ["OK", "Minor", "Major", "Kritis"], key=f"ex_s_{i}")
                    res_note = c2.text_area("Temuan/Catatan", key=f"ex_n_{i}")
                    res_photo = c3.file_uploader("Foto Bukti", type=['jpg','png'], key=f"ex_p_{i}")
                    current_results.append({"no": item['No'], "kriteria": item['Kriteria'], "status": res_status, "note": res_note, "photo": res_photo})
            
            st.divider()
            
            if st.button("📊 Selesaikan Audit & Hitung Scoring"):
                skor, grade, pinalti = calculate_score(current_results)
                # Filter item yang terdapat temuan (Bukan OK)
                daftar_temuan = [r for r in current_results if r['status'] != 'OK']
                
                st.session_state.calculation_result = {
                    "skor": skor, 
                    "grade": grade, 
                    "pinalti": pinalti, 
                    "detail": current_results,
                    "temuan_list": daftar_temuan
                }
                st.session_state.audit_finalized = True

            # --- BAGIAN SUMMARY YANG DIPERBAIKI ---
            if st.session_state.audit_finalized and st.session_state.calculation_result:
                calc = st.session_state.calculation_result
                
                with st.container(border=True):
                    st.subheader("📋 Summary Hasil Audit")
                    sc1, sc2, sc3 = st.columns([1, 1, 1])
                    sc1.metric("SKOR AKHIR", calc['skor'])
                    sc2.metric("GRADE", calc['grade'])
                    
                    p = calc['pinalti']
                    sc3.markdown(f"**Total Pinalti:**\n- Minor: {p[0]}\n- Major: {p[1]}\n- Kritis: {p[2]}")
                    
                    # TAMBAHAN: Detail Item Temuan
                    st.write("**Daftar Item Temuan:**")
                    if calc['temuan_list']:
                        df_temuan = pd.DataFrame(calc['temuan_list'])
                        # Hanya menampilkan kolom No, Kriteria, Status, dan Catatan
                        st.table(df_temuan[['no', 'kriteria', 'status', 'note']])
                    else:
                        st.success("Tidak ada temuan (Semua item OK).")
                    
                    st.write("---")
                    st.write("**PENGESAHAN (Tanda Tangan Digital)**")
                    sig1, sig2 = st.columns(2)
                    final_auditor = sig1.text_input("Nama Auditor", value=task['Auditor'])
                    final_auditee = sig2.text_input("Nama Auditee", value=task['Auditee'])
                    
                    if st.button("💾 Simpan Laporan Final"):
                        st.session_state.audit_history.append({
                            **task,
                            "Audit_ID": f"AUD-{datetime.now().strftime('%H%M%S')}",
                            "Skor": calc['skor'],
                            "Grade": calc['grade'],
                            "Detail": calc['detail'],
                            "Tgl_Audit": str(datetime.now().date()),
                            "Auditor": final_auditor,
                            "Auditee": final_auditee
                        })
                        st.session_state.audit_schedules[task_index]['Status'] = "Completed"
                        st.session_state.audit_finalized = False
                        st.session_state.calculation_result = None
                        st.success("✅ Laporan Berhasil Disimpan!")
                        st.rerun()

        else: 
            st.error(f"Form Master '{key}' belum tersedia.")
    else: 
        st.info("Tidak ada jadwal outstanding.")

# --- 8. MODULE: REMEDIATION (PHASE 6) ---
elif menu == "🛠️ Remediation (Phase 6)":
    st.title("🛠️ Perbaikan Temuan (CAPA)")
    if st.session_state.audit_history:
        audit_with_findings = [a['Audit_Title'] for a in st.session_state.audit_history if any(d['status'] != 'OK' for d in a['Detail'])]
        if audit_with_findings:
            sel_rep = st.selectbox("Pilih Laporan untuk Perbaikan", audit_with_findings)
            rep_data = next(a for a in st.session_state.audit_history if a['Audit_Title'] == sel_rep)
            findings = [d for d in rep_data['Detail'] if d['status'] != 'OK']
            for i, f in enumerate(findings):
                with st.container(border=True):
                    st.error(f"TEMUAN: {f['kriteria']} ({f['status']})")
                    st.write(f"Catatan Auditor: {f['note']}")
                    st.text_area("Tindakan Korektif Auditee", key=f"fix_a_{i}")
                    st.file_uploader("Upload Bukti Perbaikan (After)", key=f"fix_p_{i}")
            st.button("Update Laporan Perbaikan")
        else: st.success("Tidak ada temuan yang perlu diperbaiki.")
    else: st.info("Belum ada histori audit.")

# --- 9. MODULE: REPORT ---
elif menu == "📄 Audit Report (Detail)":
    st.title("📄 Detail Laporan Audit")
    if st.session_state.audit_history:
        report_names = [f"{a['Tgl_Audit']} - {a['Audit_Title']}" for a in st.session_state.audit_history]
        sel_rep = st.selectbox("Pilih Laporan", report_names)
        r = st.session_state.audit_history[report_names.index(sel_rep)]
        st.divider()
        st.subheader(f"Laporan: {r['Audit_Title']}")
        st.write(f"Auditor: {r['Auditor']} | Auditee: {r['Auditee']} | Skor: {r['Skor']} ({r['Grade']})")
        st.dataframe(pd.DataFrame(r['Detail'])[['kriteria', 'status', 'note']], use_container_width=True)
    else: st.info("Belum ada laporan.")
