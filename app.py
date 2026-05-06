import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM ---
st.set_page_config(page_title="Smart Audit Hub v5", layout="wide")
# --- 1. INISIALISASI DATABASE USER & ROLE ---
if 'users_db' not in st.session_state:
    # Database user sederhana (Username: Password)
    st.session_state.users_db = {
        "riyan": {"password": "123", "role": "Auditor", "nama": "Riyan Anjasmoro"},
        "yuka": {"password": "123", "role": "Auditee", "nama": "Yuka"},
        "erland": {"password": "123", "role": "Auditee", "nama": "Erland"}
    }

if 'current_user' not in st.session_state:
    st.session_state.current_user = None
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

# --- 2. MODUL LOGIN ---
def login_page():
    st.title("🔐 Login Smart Audit System")
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username in st.session_state.users_db and st.session_state.users_db[username]["password"] == password:
                st.session_state.current_user = st.session_state.users_db[username]
                st.session_state.current_user['username'] = username
                st.success(f"Selamat Datang, {st.session_state.current_user['nama']}!")
                st.rerun()
            else:
                st.error("Username atau Password salah")

if st.session_state.current_user is None:
    login_page()
    st.stop() # Berhenti di sini jika belum login

# --- 3. SIDEBAR & ROLE ACCESS CONTROL ---
user = st.session_state.current_user
st.sidebar.title(f"👤 {user['nama']}")
st.sidebar.write(f"Role: **{user['role']}**")

# Filter menu berdasarkan Role
menu_options = ["📊 Dashboard & Outstanding"]

if user['role'] == "Auditor":
    menu_options += ["⚙️ Module Master", "📅 Initiation & Scheduling", "📝 Execution (Phase 3)"]

menu_options += ["🛠️ Remediation (Phase 6)", "📄 Audit Report (Detail)"]

menu = st.sidebar.radio("Navigasi Module", menu_options)

if st.sidebar.button("🚪 Logout"):
    st.session_state.current_user = None
    st.rerun()
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

    # --- BAGIAN 1: KPI METRICS (DIPERBAIKI) ---
    st.subheader("📋 Ringkasan Status Audit & CAPA")
    
    # Menghitung Qty Jadwal dari database utama
    total_jadwal = len(st.session_state.audit_schedules)
    total_selesai = len(st.session_state.audit_history)
    qty_outstanding = len([s for s in st.session_state.audit_schedules if s.get('Status') == "Outstanding"])
    
    # Menghitung Qty Perbaikan (CAPA) yang belum selesai
    qty_belum_perbaikan = 0  # Tanggung jawab Auditee
    qty_menunggu_approval = 0 # Tanggung jawab Auditor
    
    if st.session_state.audit_history:
        for audit in st.session_state.audit_history:
            for item in audit.get('Detail', []):
                # Hanya hitung item yang statusnya bukan OK
                if item.get('status') != 'OK':
                    status_capa = item.get('capa_status', 'Open')
                    
                    if status_capa in ['Open', 'Rejected']:
                        qty_belum_perbaikan += 1
                    elif status_capa == 'Pending Approval':
                        qty_menunggu_approval += 1

    # Tampilan 4 Kolom Metric
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jadwal", f"{total_jadwal}")
    m2.metric("Selesai (Completed)", f"{total_selesai}")
    
    # Menampilkan jumlah audit yang masih pending (Outstanding)
    m3.metric("Pending Audit", f"{qty_outstanding} Jadwal", delta_color="inverse")
    
    # Menampilkan total item temuan yang belum di-approve
    total_pending_capa = qty_belum_perbaikan + qty_menunggu_approval
    m4.metric("Pending Perbaikan", f"{total_pending_capa} Item", delta=f"{qty_menunggu_approval} butuh Approval", delta_color="normal")

    st.divider()

    # --- BAGIAN 2: GRAFIK KOMPARASI (MEMASTIKAN TIPE MUNCUL) ---
    if st.session_state.audit_history:
        st.subheader("📈 Komparasi Hasil Audit")
        df_hist = pd.DataFrame(st.session_state.audit_history)
        
        # Pastikan kolom Tipe tersedia
        if 'Tipe' in df_hist.columns:
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                sel_lokasi = st.multiselect("Lokasi", df_hist['Lokasi'].unique(), default=df_hist['Lokasi'].unique())
            with c_f2:
                sel_tipe = st.multiselect("Tipe Audit", df_hist['Tipe'].unique(), default=df_hist['Tipe'].unique())
            with c_f3:
                sel_judul = st.multiselect("Judul Audit", df_hist['Audit_Title'].unique(), default=df_hist['Audit_Title'].unique())
                
            # Filter Data
            df_filtered = df_hist[
                (df_hist['Lokasi'].isin(sel_lokasi)) & 
                (df_hist['Tipe'].isin(sel_tipe)) & 
                (df_hist['Audit_Title'].isin(sel_judul))
            ]
            
            if not df_filtered.empty:
                fig = px.bar(
                    df_filtered, 
                    x="Audit_Title", 
                    y="Skor", 
                    color="Tipe", # Mengelompokkan warna berdasarkan Tipe Audit
                    barmode="group",
                    text="Skor",
                    title="Tren Skor Berdasarkan Tipe Audit"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Pilih minimal satu kriteria pada filter di atas.")
        else:
            st.error("Data 'Tipe' tidak ditemukan dalam histori. Pastikan Tipe diisi saat inisiasi.")
    else:
        st.info("Belum ada riwayat audit untuk ditampilkan pada grafik.")

    st.divider()

    # --- BAGIAN 3: LIST DETAIL PENDING ---
    st.subheader("📌 Detail Tugas Pending (Outstanding)")
    if qty_outstanding > 0:
        for i, task in enumerate(st.session_state.audit_schedules):
            if task['Status'] == "Outstanding":
                with st.expander(f"🕒 {task['Audit_Title']} - {task['Lokasi']}"):
                    st.write(f"**Target Tanggal:** {task.get('Tanggal', 'N/A')}")
                    st.write(f"**Auditee PIC:** {task['Auditee']}")
                    if st.button("🗑️ Batalkan Jadwal", key=f"del_pending_{i}"):
                        st.session_state.audit_schedules.pop(i)
                        st.rerun()
    else:
        st.success("Semua tugas audit telah selesai dikerjakan.")

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
    st.title("🛠️ Perbaikan & Verifikasi (CAPA)")
    
    # Filter laporan
    audit_with_findings = [a['Audit_Title'] for a in st.session_state.audit_history if any(d['status'] != 'OK' for d in a['Detail'])]
    
    if audit_with_findings:
        sel_rep = st.selectbox("Pilih Laporan Audit", audit_with_findings)
        idx_hist = next(i for i, a in enumerate(st.session_state.audit_history) if a['Audit_Title'] == sel_rep)
        audit_data = st.session_state.audit_history[idx_hist]
        
        for i, item in enumerate(audit_data['Detail']):
            if item['status'] != 'OK':
                if 'capa_status' not in item: item['capa_status'] = 'Open'
                
                with st.container(border=True):
                    st.subheader(f"Item: {item['kriteria']}")
                    col_before, col_after, col_status = st.columns([2, 2, 1.5])
                    
                    with col_before:
                        st.markdown("📷 **Foto Temuan (Before)**")
                        if item.get('photo'): st.image(item['photo'], use_container_width=True)
                        st.warning(f"Catatan: {item['note']}")

                    with col_after:
                        st.markdown("📷 **Foto Perbaikan (After)**")
                        if item.get('capa_photo_after'): st.image(item['capa_photo_after'], use_container_width=True)
                        if item.get('capa_action'): st.success(f"Tindakan: {item['capa_action']}")

                    with col_status:
                        st.write(f"Status: `{item['capa_status']}`")
                        
                        # LOGIKA ROLE AUDITEE (Kirim Perbaikan)
                        if user['role'] == "Auditee" and item['capa_status'] in ['Open', 'Rejected']:
                            capa_txt = st.text_area("Deskripsi Perbaikan", key=f"t_{idx_hist}_{i}")
                            capa_img = st.file_uploader("Upload Bukti After", key=f"f_{idx_hist}_{i}")
                            if st.button("Kirim Approval", key=f"s_{idx_hist}_{i}"):
                                item['capa_action'] = capa_txt
                                item['capa_photo_after'] = capa_img
                                item['capa_status'] = 'Pending Approval'
                                st.rerun()

                        # LOGIKA ROLE AUDITOR (Approve/Reject)
                        elif user['role'] == "Auditor" and item['capa_status'] == 'Pending Approval':
                            if st.button("✔️ Approve", key=f"app_{idx_hist}_{i}", type="primary"):
                                item['capa_status'] = 'Closed'
                                st.rerun()
                            if st.button("❌ Reject", key=f"rej_{idx_hist}_{i}"):
                                item['capa_status'] = 'Rejected'
                                st.rerun()
                        
                        elif item['capa_status'] == 'Closed':
                            st.success("✅ Selesai")
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
