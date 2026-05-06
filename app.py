import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM & DATABASE SIMULASI ---
st.set_page_config(page_title="Smart Audit Hub", layout="wide")

if 'master_templates' not in st.session_state:
    # Library Master Form (Template yang sudah di-upload)
    st.session_state.master_templates = {} 

if 'audit_schedules' not in st.session_state:
    # Jadwal yang di-import (Outstanding Tasks)
    st.session_state.audit_schedules = []

if 'audit_history' not in st.session_state:
    # Hasil Audit yang sudah dieksekusi
    st.session_state.audit_history = []

# --- 2. UTILS: SCORING LOGIC ---
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
menu = st.sidebar.radio("Navigasi Module", [
    "📊 Dashboard & Outstanding",
    "⚙️ Module Master",
    "📅 Initiation & Scheduling",
    "📝 Execution (Phase 3)",
    "🛠️ Remediation (Phase 6)"
])

# --- 4. MODULE: MASTER DATA (UPLOAD & SETTING) ---
if menu == "⚙️ Module Master":
    st.title("⚙️ Module Master: Template & Mapping")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upload Master Form")
        type_audit = st.selectbox("Tipe Audit", ["GMP", "SQA", "ISO", "K3"])
        lokasi_master = st.selectbox("Lokasi Mapping", ["NICE Hub", "Satelite Kitchen", "Central Kitchen"])
        uploaded_template = st.file_uploader("Upload Master CSV", type=["csv"])
        
        if uploaded_template and st.button("Simpan ke Library"):
            df_temp = pd.read_csv(uploaded_template, sep=None, engine='python')
            template_key = f"{type_audit}_{lokasi_master}"
            st.session_state.master_templates[template_key] = df_temp.to_dict('records')
            st.success(f"Master Form '{template_key}' berhasil disimpan!")

    with col2:
        st.subheader("Download System Template")
        # Contoh template standar sistem
        template_csv = "Kategori;No;Area;Kriteria\nUmum;1;Pintu;Pintu harus bersih\nProduksi;2;Lantai;Lantai tidak retak"
        st.download_button("📥 Download Blank Template", template_csv, "system_template.csv", "text/csv")

# --- 5. MODULE: INITIATION & SCHEDULING ---
elif menu == "📅 Initiation & Scheduling":
    st.title("📅 Inisiasi & Import Jadwal")
    
    tab1, tab2 = st.tabs(["Import Jadwal Masal", "Inisiasi Manual"])
    
    with tab1:
        st.subheader("Import Jadwal Audit")
        uploaded_sched = st.file_uploader("Upload File Jadwal (CSV)", type=["csv"])
        if uploaded_sched and st.button("Proses Jadwal"):
            df_sched = pd.read_csv(uploaded_sched, sep=None, engine='python')
            for _, row in df_sched.iterrows():
                row_dict = row.to_dict()
                row_dict['status_audit'] = "Outstanding"
                st.session_state.audit_schedules.append(row_dict)
            st.success(f"{len(df_sched)} Jadwal Audit masuk ke Dashboard!")

    with tab2:
        st.subheader("Inisiasi Audit Baru")
        with st.form("manual_init"):
            c1, c2 = st.columns(2)
            t_audit = c1.selectbox("Tipe", ["GMP", "SQA", "ISO"], key="t_man")
            l_audit = c2.selectbox("Lokasi", ["NICE Hub", "Satelite Kitchen"], key="l_man")
            auditor = c1.text_input("Nama Auditor")
            auditee = c2.text_input("Nama Auditee (PIC Perbaikan)")
            
            if st.form_submit_button("Start Audit"):
                key = f"{t_audit}_{l_audit}"
                if key in st.session_state.master_templates:
                    st.info(f"Menggunakan Master Form: {key}")
                    # Logika lanjut ke eksekusi...
                else:
                    st.error("Master Form tidak ditemukan untuk kriteria ini.")

# --- 6. MODULE: DASHBOARD & OUTSTANDING ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Audit Executive Dashboard")
    
    # Overview Metrics
    total_outstanding = len([s for s in st.session_state.audit_schedules if s['status_audit'] == "Outstanding"])
    st.metric("Outstanding Audit Tasks", total_outstanding)
    
    if st.session_state.audit_schedules:
        st.subheader("📌 Reminder: Audit yang Harus Diselesaikan")
        df_outstanding = pd.DataFrame(st.session_state.audit_schedules)
        st.dataframe(df_outstanding[df_outstanding['status_audit'] == "Outstanding"], use_container_width=True)
    
    if st.session_state.audit_history:
        st.divider()
        st.subheader("📈 Tren Kualitas")
        df_hist = pd.DataFrame(st.session_state.audit_history)
        fig = px.line(df_hist, x="Tanggal", y="Skor", color="Lokasi", title="History Skor Audit")
        st.plotly_chart(fig, use_container_width=True)

# --- 7. MODULE: EXECUTION (PHASE 3) ---
elif menu == "📝 Execution (Phase 3)":
    st.title("📝 Eksekusi Audit Lapangan")
    
    # Pilih dari jadwal outstanding
    outstanding_list = [s['Audit_Title'] for s in st.session_state.audit_schedules if s['status_audit'] == "Outstanding"]
    
    if outstanding_list:
        selected_task = st.selectbox("Pilih Jadwal Audit", outstanding_list)
        task_data = next(item for item in st.session_state.audit_schedules if item["Audit_Title"] == selected_task)
        
        template_key = f"{task_data['Tipe']}_{task_data['Lokasi']}"
        
        if template_key in st.session_state.master_templates:
            checklist = st.session_state.master_templates[template_key]
            results = []
            
            st.info(f"Auditee: {task_data['Auditee']} | Lokasi: {task_data['Lokasi']}")
            
            for i, item in enumerate(checklist):
                with st.expander(f"{item['No']}. {item['Kriteria']}", expanded=True):
                    c1, c2 = st.columns([1, 2])
                    status = c1.radio("Hasil", ["OK", "Minor", "Major", "Kritis"], key=f"res_{i}")
                    note = c2.text_area("Catatan Temuan", key=f"note_{i}")
                    results.append({'kriteria': item['Kriteria'], 'status': status, 'note': note})
            
            if st.button("Submit & Hitung Skor"):
                skor, grade = calculate_score(results)
                new_audit = {
                    "Audit_ID": f"AUD-{datetime.now().strftime('%Y%m%d')}",
                    "Judul": selected_task,
                    "Auditee": task_data['Auditee'],
                    "Auditor": task_data['Auditor'],
                    "Lokasi": task_data['Lokasi'],
                    "Tanggal": str(datetime.now().date()),
                    "Skor": skor,
                    "Grade": grade,
                    "Detail": results
                }
                st.session_state.audit_history.append(new_audit)
                task_data['status_audit'] = "Completed"
                st.success(f"Audit Selesai! Skor: {skor} ({grade})")
        else:
            st.error(f"Form untuk {template_key} belum di-upload di Module Master.")
    else:
        st.info("Tidak ada jadwal outstanding.")

# --- 8. MODULE: REMEDIATION (PHASE 6) ---
elif menu == "🛠️ Remediation (Phase 6)":
    st.title("🛠️ Perbaikan Temuan oleh Auditee")
    
    if st.session_state.audit_history:
        audit_names = [a['Judul'] for a in st.session_state.audit_history]
        sel_audit = st.selectbox("Pilih Laporan Audit", audit_names)
        data = next(item for item in st.session_state.audit_history if item["Judul"] == sel_audit)
        
        st.markdown(f"**Auditee PIC:** {data['Auditee']}")
        
        temuan = [d for d in data['Detail'] if d['status'] != 'OK']
        
        for i, t in enumerate(temuan):
            with st.container(border=True):
                st.error(f"Masalah: {t['kriteria']} ({t['status']})")
                st.text_area("Tindakan Perbaikan", key=f"fix_{i}")
                st.file_uploader("Upload Bukti Perbaikan (After)", key=f"file_{i}")
        
        if st.button("Kirim Perbaikan"):
            st.success("Data perbaikan telah dikirim ke Auditor untuk verifikasi.")
    else:
        st.info("Belum ada data audit untuk diperbaiki.")
