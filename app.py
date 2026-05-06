import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM ---
st.set_page_config(page_title="Smart Audit Hub v2", layout="wide")

# Inisialisasi Session State agar data tidak hilang saat pindah menu
if 'master_templates' not in st.session_state:
    st.session_state.master_templates = {} 
if 'audit_schedules' not in st.session_state:
    st.session_state.audit_schedules = []
if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []
if 'employee_db' not in st.session_state:
    st.session_state.employee_db = pd.DataFrame(columns=['ID', 'Nama', 'Role', 'Unit'])

# --- 2. FUNGSI PENDUKUNG (UTILS) ---
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
    
    return final_score, grade

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🛡️ Smart Audit System")
st.sidebar.info("Gunakan Module Master terlebih dahulu untuk mengisi data.")
menu = st.sidebar.radio("Navigasi Module", [
    "📊 Dashboard & Outstanding",
    "⚙️ Module Master (Data & Form)",
    "📅 Initiation & Scheduling",
    "📝 Execution (Phase 3)",
    "🛠️ Remediation (Phase 6)"
])

# --- 4. MODULE: MASTER DATA ---
if menu == "⚙️ Module Master (Data & Form)":
    st.title("⚙️ Module Master: Pusat Pengaturan")
    
    # Fitur Instan untuk Testing
    if st.button("🚀 Inisialisasi Data Dummy (Klik ini untuk mencoba cepat)"):
        # 1. Master Employee
        st.session_state.employee_db = pd.DataFrame([
            {'ID': 'EMP01', 'Nama': 'Riyan Anjasmoro', 'Role': 'Auditor', 'Unit': 'QHSE'},
            {'ID': 'EMP02', 'Nama': 'Yuka', 'Role': 'Auditee', 'Unit': 'NICE Hub'},
            {'ID': 'EMP03', 'Nama': 'Budi', 'Role': 'Auditee', 'Unit': 'Satelite PIK2'}
        ])
        # 2. Master Form GMP
        gmp_form = [
            {'Kategori': 'Kebersihan', 'No': '1.1', 'Kriteria': 'Lantai area produksi bersih dan tidak retak'},
            {'Kategori': 'Personel', 'No': '1.2', 'Kriteria': 'Karyawan menggunakan APD lengkap'},
            {'Kategori': 'Fasilitas', 'No': '1.3', 'Kriteria': 'Tersedia tempat cuci tangan yang memadai'}
        ]
        st.session_state.master_templates["GMP_NICE Hub"] = gmp_form
        st.success("Data Dummy (Employee & Form GMP) berhasil dimuat!")

    tab1, tab2 = st.tabs(["Manajemen Employee", "Master Form Audit"])
    
    with tab1:
        st.subheader("Daftar Auditor & Auditee")
        new_emp = st.data_editor(st.session_state.employee_db, num_rows="dynamic", use_container_width=True)
        if st.button("Simpan Data Employee"):
            st.session_state.employee_db = new_emp
            st.success("Data Employee diperbarui.")

    with tab2:
        st.subheader("Upload & Mapping Master Form")
        c1, c2 = st.columns(2)
        with c1:
            t_audit = st.selectbox("Tipe Audit", ["GMP", "SQA", "ISO"])
            l_audit = st.selectbox("Lokasi Mapping", ["NICE Hub", "Satelite Kitchen", "Central Kitchen"])
            uploaded_file = st.file_uploader("Upload CSV Template", type=["csv"])
            if uploaded_file and st.button("Simpan Form"):
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
                st.session_state.master_templates[f"{t_audit}_{l_audit}"] = df.to_dict('records')
                st.success(f"Form {t_audit} untuk {l_audit} tersimpan!")
        with c2:
            st.write("Format CSV: `Kategori,No,Kriteria`")
            csv_sample = "Kategori,No,Kriteria\nUmum,1,Area bersih\nFasilitas,2,Peralatan lengkap"
            st.download_button("📥 Download Blank CSV", csv_sample, "template.csv")

# --- 5. MODULE: INITIATION & SCHEDULING ---
elif menu == "📅 Initiation & Scheduling":
    st.title("📅 Inisiasi & Penjadwalan Audit")
    
    if st.session_state.employee_db.empty:
        st.warning("⚠️ Data Employee kosong. Isi di Module Master!")
    else:
        with st.form("form_init"):
            title = st.text_input("Judul Audit (Contoh: Audit Bulanan GMP)")
            c1, c2 = st.columns(2)
            t_audit = c1.selectbox("Tipe Audit", ["GMP", "SQA", "ISO"])
            l_audit = c2.selectbox("Lokasi", ["NICE Hub", "Satelite Kitchen"])
            
            auditor_list = st.session_state.employee_db[st.session_state.employee_db['Role'] == 'Auditor']['Nama'].tolist()
            auditee_list = st.session_state.employee_db[st.session_state.employee_db['Role'] == 'Auditee']['Nama'].tolist()
            
            auditor = c1.selectbox("Pilih Auditor", auditor_list if auditor_list else ["Isi Master Auditor!"])
            auditee = c2.selectbox("Pilih Auditee (PIC)", auditee_list if auditee_list else ["Isi Master Auditee!"])
            date_plan = st.date_input("Tanggal Pelaksanaan")
            
            if st.form_submit_button("Buat Jadwal (Outstanding)"):
                new_sched = {
                    "Audit_Title": title, "Tipe": t_audit, "Lokasi": l_audit,
                    "Auditor": auditor, "Auditee": auditee, "Tanggal": str(date_plan),
                    "Status": "Outstanding"
                }
                st.session_state.audit_schedules.append(new_sched)
                st.success("Jadwal audit telah ditambahkan ke Dashboard!")

# --- 6. MODULE: DASHBOARD ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Outstanding Audit Tasks")
    
    outstanding = [s for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    
    if not outstanding:
        st.info("Tidak ada jadwal audit outstanding. Silakan buat di Module Initiation.")
    else:
        st.subheader("📌 Tugas Audit yang Harus Diselesaikan")
        df_out = pd.DataFrame(outstanding)
        st.table(df_out[["Audit_Title", "Lokasi", "Auditor", "Auditee", "Tanggal"]])

# --- 7. MODULE: EXECUTION ---
elif menu == "📝 Execution (Phase 3)":
    st.title("📝 Eksekusi Audit")
    
    outstanding_titles = [s['Audit_Title'] for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    
    if outstanding_titles:
        sel_task = st.selectbox("Pilih Jadwal Audit", outstanding_titles)
        task = next(item for item in st.session_state.audit_schedules if item["Audit_Title"] == sel_task)
        
        key = f"{task['Tipe']}_{task['Lokasi']}"
        
        if key in st.session_state.master_templates:
            checklist = st.session_state.master_templates[key]
            results = []
            for i, item in enumerate(checklist):
                with st.expander(f"{item['No']} - {item['Kriteria']}"):
                    res = st.radio("Hasil", ["OK", "Minor", "Major", "Kritis"], key=f"r_{i}")
                    note = st.text_area("Catatan", key=f"n_{i}")
                    results.append({"kriteria": item['Kriteria'], "status": res, "note": note})
            
            if st.button("Finalisasi Audit"):
                skor, grade = calculate_score(results)
                data_final = {
                    **task, "Skor": skor, "Grade": grade, "Detail": results, "Tgl_Selesai": str(datetime.now())
                }
                st.session_state.audit_history.append(data_final)
                task['Status'] = "Completed"
                st.balloons()
                st.success(f"Audit Berhasil! Skor: {skor} ({grade})")
        else:
            st.error(f"Form Master '{key}' tidak ditemukan. Silakan mapping di Module Master.")
    else:
        st.info("Semua jadwal audit telah selesai atau belum ada jadwal.")

# --- 8. MODULE: REMEDIATION ---
elif menu == "🛠️ Remediation (Phase 6)":
    st.title("🛠️ Perbaikan Temuan")
    if not st.session_state.audit_history:
        st.info("Belum ada temuan audit.")
    else:
        sel_hist = st.selectbox("Pilih Audit", [a['Audit_Title'] for a in st.session_state.audit_history])
        audit_data = next(a for a in st.session_state.audit_history if a['Audit_Title'] == sel_hist)
        
        findings = [d for d in audit_data['Detail'] if d['status'] != 'OK']
        for i, f in enumerate(findings):
            st.error(f"Temuan: {f['kriteria']} ({f['status']})")
            st.text_area("Tindakan Korektif", key=f"capa_{i}")
            st.file_uploader("Upload Bukti", key=f"up_{i}")
        st.button("Update CAPA")
