import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM ---
st.set_page_config(page_title="Smart Audit Hub v4", layout="wide")

# Persistent Storage menggunakan Session State
if 'master_templates' not in st.session_state:
    st.session_state.master_templates = {} 
if 'audit_schedules' not in st.session_state:
    st.session_state.audit_schedules = []
if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []
if 'employee_db' not in st.session_state:
    # Menambahkan data awal agar tidak kosong
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

# --- 4. MODULE: MASTER DATA (DATABASE FORM & EMPLOYEE) ---
if menu == "⚙️ Module Master":
    st.title("⚙️ Module Master: Pusat Database")
    
    tab1, tab2 = st.tabs(["Master Form Audit", "Master Employee"])
    
    with tab1:
        st.subheader("1. Unduh Template Form")
        st.write("Gunakan template ini untuk membuat daftar kriteria audit.")
        form_csv = "Kategori,No,Kriteria\nArea Luar,1.1,Lokasi bebas banjir dan bersih\nFasilitas,1.2,Tersedia tempat cuci tangan\nProduksi,2.1,Lantai tidak retak dan bersih"
        st.download_button("📥 Download Template Form (CSV)", form_csv, "template_form.csv", "text/csv")
        
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
                st.success(f"Form {t_audit} - {l_audit} Berhasil Disimpan!")

    with tab2:
        st.subheader("Daftar Auditor & Auditee")
        new_emp = st.data_editor(st.session_state.employee_db, num_rows="dynamic", use_container_width=True)
        if st.button("Update Database Employee"):
            st.session_state.employee_db = new_emp
            st.success("Data Employee diperbarui.")

# --- 5. MODULE: INITIATION & SCHEDULING ---
elif menu == "📅 Initiation & Scheduling":
    st.title("📅 Inisiasi & Penjadwalan")
    
    st.subheader("1. Unduh Template Jadwal")
    sched_csv = "Audit_Title,Tipe,Lokasi,Auditor,Auditee,Tanggal\nAudit Bulanan Mei,GMP,NICE Hub,Riyan Anjasmoro,Yuka,2026-05-30"
    st.download_button("📥 Download Template Jadwal (CSV)", sched_csv, "template_jadwal.csv", "text/csv")
    
    st.divider()
    st.subheader("2. Import Jadwal Audit")
    uploaded_sched = st.file_uploader("Upload File Jadwal (CSV)", type=["csv"])
    if uploaded_sched and st.button("Proses Import Jadwal"):
        df_sched = pd.read_csv(uploaded_sched, sep=None, engine='python')
        for _, row in df_sched.iterrows():
            row_dict = row.to_dict()
            row_dict['Status'] = "Outstanding"
            st.session_state.audit_schedules.append(row_dict)
        st.success(f"{len(df_sched)} Jadwal berhasil ditambahkan!")

# --- 6. MODULE: DASHBOARD & OUTSTANDING ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Dashboard & Monitoring")
    
    st.subheader("📌 Outstanding Task (Jadwal Audit)")
    if not st.session_state.audit_schedules:
        st.info("Tidak ada jadwal audit saat ini.")
    else:
        for i, task in enumerate(st.session_state.audit_schedules):
            if task['Status'] == "Outstanding":
                with st.expander(f"🕒 {task['Audit_Title']} - {task['Lokasi']} ({task['Tipe']})"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**Auditor:** {task['Auditor']}")
                    c2.write(f"**Auditee:** {task['Auditee']}")
                    if c3.button("🗑️ Hapus Jadwal", key=f"del_{i}"):
                        st.session_state.audit_schedules.pop(i)
                        st.rerun()

# --- 7. MODULE: EXECUTION ---
elif menu == "📝 Execution (Phase 3)":
    st.title("📝 Eksekusi Audit")
    outstanding = [s['Audit_Title'] for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    
    if outstanding:
        sel_task = st.selectbox("Pilih Jadwal Audit", outstanding)
        task = next(item for item in st.session_state.audit_schedules if item["Audit_Title"] == sel_task)
        key = f"{task['Tipe']}_{task['Lokasi']}"
        
        if key in st.session_state.master_templates:
            checklist = st.session_state.master_templates[key]
            results = []
            for i, item in enumerate(checklist):
                with st.container(border=True):
                    st.write(f"**{item['No']}. {item['Kriteria']}**")
                    c1, c2, c3 = st.columns([1, 2, 1])
                    status = c1.radio("Status", ["OK", "Minor", "Major", "Kritis"], key=f"s_{i}")
                    note = c2.text_area("Catatan", key=f"n_{i}")
                    photo = c3.file_uploader("Kamera/Upload", type=['png','jpg','jpeg'], key=f"p_{i}")
                    results.append({"kriteria": item['Kriteria'], "status": status, "note": note, "photo": photo})
            
            if st.button("Finalisasi & Tanda Tangan"):
                skor, grade, pinalti = calculate_score(results)
                st.session_state.audit_history.append({**task, "Skor": skor, "Grade": grade, "Detail": results, "Tgl_Audit": str(datetime.now().date()), "Audit_ID": f"AUD-{datetime.now().strftime('%H%M%S')}"})
                task['Status'] = "Completed"
                st.success(f"Audit Selesai! Skor: {skor} ({grade})")
        else:
            st.error(f"Form Master '{key}' belum ada. Silakan upload di Module Master.")
    else:
        st.info("Tidak ada jadwal audit.")

# --- 8. MODULE: REPORT ---
elif menu == "📄 Audit Report (Detail)":
    st.title("📄 Detail Hasil Audit")
    if not st.session_state.audit_history:
        st.info("Belum ada laporan.")
    else:
        report_names = [f"{a['Tgl_Audit']} - {a['Audit_Title']}" for a in st.session_state.audit_history]
        sel_rep = st.selectbox("Pilih Laporan", report_names)
        rep_data = st.session_state.audit_history[report_names.index(sel_rep)]
        
        st.divider()
        st.write(f"**Auditor:** {rep_data['Auditor']} | **Auditee:** {rep_data['Auditee']}")
        st.metric("SKOR AKHIR", rep_data['Skor'], help=f"Grade: {rep_data['Grade']}")
        st.dataframe(pd.DataFrame(rep_data['Detail'])[['kriteria', 'status', 'note']], use_container_width=True)

# --- 9. MODULE: REMEDIATION ---
elif menu == "🛠️ Remediation (Phase 6)":
    st.title("🛠️ Perbaikan Temuan")
    
    if not st.session_state.audit_history:
        st.info("Belum ada laporan audit yang tersimpan.")
    else:
        # Pilihan laporan yang ingin dilihat detailnya
        report_options = [f"{a['Tgl_Audit']} - {a['Audit_Title']} ({a['Lokasi']})" for a in st.session_state.audit_history]
        sel_report = st.selectbox("Pilih Laporan untuk Dilihat", report_options)
        
        # Ambil data spesifik
        idx = report_options.index(sel_report)
        report_data = st.session_state.audit_history[idx]
        
        # Header Laporan
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**ID Audit:** {report_data['Audit_ID']}")
            st.write(f"**Tipe Audit:** {report_data['Tipe']}")
            st.write(f"**Auditor:** {report_data['Auditor']}")
        with c2:
            st.write(f"**Lokasi:** {report_data['Lokasi']}")
            st.write(f"**Auditee:** {report_data['Auditee']}")
            st.write(f"**Tanggal:** {report_data['Tgl_Audit']}")
        
        # Scoring Summary
        st.subheader("Summary Scoring")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("SKOR AKHIR", report_data['Skor'])
        sc2.metric("GRADE", report_data['Grade'])
        
        # Tabel Detail Kriteria
        st.subheader("Detail Temuan per Item")
        df_detail = pd.DataFrame(report_data['Detail'])
        st.dataframe(df_detail[['kriteria', 'status', 'note']], use_container_width=True)
        
        # Tombol Hapus Laporan (Opsional)
        if st.button("🗑️ Hapus Laporan Ini dari History"):
            st.session_state.audit_history.pop(idx)
            st.success("Laporan berhasil dihapus.")
            st.rerun()
