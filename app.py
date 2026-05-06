import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# --- 1. KONFIGURASI SISTEM ---
st.set_page_config(page_title="Smart Audit Hub v3", layout="wide")

# Persistent Storage menggunakan Session State
if 'master_templates' not in st.session_state:
    st.session_state.master_templates = {} 
if 'audit_schedules' not in st.session_state:
    st.session_state.audit_schedules = []
if 'audit_history' not in st.session_state:
    st.session_state.audit_history = []
if 'employee_db' not in st.session_state:
    st.session_state.employee_db = pd.DataFrame(columns=['Nama', 'Role'])

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
    "🛠️ Remediation (Phase 6)"
])

# --- 4. MODULE: MASTER DATA (DATABASE FORM & EMPLOYEE) ---
if menu == "⚙️ Module Master":
    st.title("⚙️ Module Master: Pusat Database")
    
    tab1, tab2 = st.tabs(["Master Form Audit", "Master Employee"])
    
    with tab1:
        st.subheader("Upload & Simpan Master Form")
        st.info("Template ini akan disimpan secara permanen berdasarkan Tipe & Lokasi.")
        c1, c2 = st.columns(2)
        with c1:
            t_audit = st.selectbox("Tipe Audit", ["GMP", "SQA", "ISO", "K3"])
            l_audit = st.selectbox("Lokasi Mapping", ["NICE Hub", "Satelite Kitchen", "Central Kitchen"])
            uploaded_file = st.file_uploader("Upload Master CSV/Excel", type=["csv", "xlsx"])
            
            if uploaded_file and st.button("Simpan ke Database Form"):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, sep=None, engine='python')
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Simpan permanen ke session state
                st.session_state.master_templates[f"{t_audit}_{l_audit}"] = df.to_dict('records')
                st.success(f"Form {t_audit} untuk {l_audit} berhasil disimpan dalam database.")

    with tab2:
        st.subheader("Daftar Auditor & Auditee")
        new_emp = st.data_editor(st.session_state.employee_db, num_rows="dynamic", use_container_width=True)
        if st.button("Update Database Employee"):
            st.session_state.employee_db = new_emp
            st.success("Data Employee diperbarui.")

# --- 5. MODULE: INITIATION & SCHEDULING ---
elif menu == "📅 Initiation & Scheduling":
    st.title("📅 Inisiasi & Penjadwalan")
    
    st.subheader("Import Jadwal Audit")
    uploaded_sched = st.file_uploader("Upload File Jadwal (CSV)", type=["csv"])
    if uploaded_sched and st.button("Proses Jadwal"):
        df_sched = pd.read_csv(uploaded_sched, sep=None, engine='python')
        for _, row in df_sched.iterrows():
            row_dict = row.to_dict()
            row_dict['Status'] = "Outstanding"
            st.session_state.audit_schedules.append(row_dict)
        st.success(f"{len(df_sched)} Jadwal masuk ke Outstanding Dashboard.")
    
    st.divider()
    st.subheader("Input Manual")
    with st.form("manual_init"):
        title = st.text_input("Judul Audit")
        c1, c2 = st.columns(2)
        ta = c1.selectbox("Tipe", ["GMP", "SQA", "ISO"])
        la = c2.selectbox("Lokasi", ["NICE Hub", "Satelite Kitchen"])
        
        auditor_list = st.session_state.employee_db[st.session_state.employee_db['Role'] == 'Auditor']['Nama'].tolist()
        auditee_list = st.session_state.employee_db[st.session_state.employee_db['Role'] == 'Auditee']['Nama'].tolist()
        
        auditor = c1.selectbox("Auditor", auditor_list if auditor_list else ["Isi Master Employee!"])
        auditee = c2.selectbox("Auditee (PIC)", auditee_list if auditee_list else ["Isi Master Employee!"])
        
        if st.form_submit_button("Simpan Jadwal"):
            st.session_state.audit_schedules.append({
                "Audit_Title": title, "Tipe": ta, "Lokasi": la,
                "Auditor": auditor, "Auditee": auditee, "Status": "Outstanding"
            })
            st.success("Jadwal tersimpan.")

# --- 6. MODULE: EXECUTION (CAMERA & SCORING) ---
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
                    note = c2.text_area("Catatan Temuan", key=f"n_{i}")
                    
                    # Fitur Kamera atau Upload Foto Temuan
                    photo = c3.file_uploader("Foto Bukti", type=['png','jpg','jpeg'], key=f"p_{i}")
                    
                    results.append({"kriteria": item['Kriteria'], "status": status, "note": note, "photo": photo})
            
            if st.button("Selesaikan Audit & Hitung Skor"):
                skor, grade, pinalti = calculate_score(results)
                
                st.divider()
                st.subheader("📑 Ringkasan Temuan & Perhitungan")
                col1, col2, col3 = st.columns(3)
                col1.metric("Skor Akhir", skor)
                col2.metric("Grade", grade)
                col3.write(f"Minor: {pinalti[0]} | Major: {pinalti[1]} | Kritis: {pinalti[2]}")
                
                # Lembar Tanda Tangan
                st.write("---")
                st.write("**PENGESAHAN LAPORAN**")
                ts1, ts2 = st.columns(2)
                ts1.text_input("Tanda Tangan Auditor (Ketik Nama)", value=task['Auditor'])
                ts2.text_input("Tanda Tangan Auditee (Ketik Nama)", value=task['Auditee'])
                
                data_final = {
                    **task, "Skor": skor, "Grade": grade, "Detail": results, "Tgl_Audit": str(datetime.now().date())
                }
                st.session_state.audit_history.append(data_final)
                task['Status'] = "Completed"
                st.success("Laporan telah ditandatangani dan disimpan dalam riwayat.")
        else:
            st.error(f"Form '{key}' tidak ditemukan di Database Master.")
    else:
        st.info("Tidak ada tugas audit.")

# --- 7. MODULE: DASHBOARD ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Dashboard Utama")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Outstanding Task")
        df_out = pd.DataFrame([s for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"])
        st.dataframe(df_out, use_container_width=True) if not df_out.empty else st.info("Kosong")
        
    with c2:
        st.subheader("📈 Performance Grade")
        if st.session_state.audit_history:
            df_hist = pd.DataFrame(st.session_state.audit_history)
            fig = px.bar(df_hist, x="Lokasi", y="Skor", color="Grade", barmode="group")
            st.plotly_chart(fig, use_container_width=True)

# --- 8. MODULE: REMEDIATION ---
elif menu == "🛠️ Remediation (Phase 6)":
    st.title("🛠️ Perbaikan Temuan")
    if st.session_state.audit_history:
        sel_hist = st.selectbox("Pilih Audit", [a['Audit_Title'] for a in st.session_state.audit_history])
        audit_data = next(a for a in st.session_state.audit_history if a['Audit_Title'] == sel_hist)
        
        findings = [d for d in audit_data['Detail'] if d['status'] != 'OK']
        for i, f in enumerate(findings):
            with st.expander(f"TEMUAN: {f['kriteria']} ({f['status']})"):
                st.write(f"Catatan: {f['note']}")
                st.text_area("Tindakan Korektif", key=f"fix_{i}")
                st.file_uploader("Upload Bukti Perbaikan", key=f"fup_{i}")
        st.button("Update Status Perbaikan")
    else:
        st.info("Belum ada data audit.")
