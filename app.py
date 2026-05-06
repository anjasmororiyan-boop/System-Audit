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

# --- 6. MODULE: DASHBOARD ---
elif menu == "📊 Dashboard & Outstanding":
    st.title("📊 Dashboard Utama")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Outstanding Task")
        if st.session_state.audit_schedules:
            for i, task in enumerate(st.session_state.audit_schedules):
                if task['Status'] == "Outstanding":
                    with st.expander(f"🕒 {task['Audit_Title']} - {task['Lokasi']}"):
                        st.write(f"Auditee: {task['Auditee']}")
                        if st.button("🗑️ Hapus", key=f"del_{i}"):
                            st.session_state.audit_schedules.pop(i)
                            st.rerun()
        else: st.info("Kosong")
    
    with c2:
        st.subheader("📈 Performance Grade")
        if st.session_state.audit_history:
            df_hist = pd.DataFrame(st.session_state.audit_history)
            fig = px.bar(df_hist, x="Lokasi", y="Skor", color="Grade", barmode="group", title="Hasil Audit per Lokasi")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Belum ada data grafik.")

# --- 7. MODULE: EXECUTION (PHASE 3) ---
elif menu == "📝 Execution (Phase 3)":
    st.title("📝 Eksekusi Audit")
    
    # Inisialisasi state lokal untuk menyimpan hasil hitung sementara
    if 'temp_results' not in st.session_state:
        st.session_state.temp_results = None

    outstanding = [s['Audit_Title'] for s in st.session_state.audit_schedules if s['Status'] == "Outstanding"]
    
    if outstanding:
        sel_task = st.selectbox("Pilih Jadwal Audit", outstanding)
        task = next(item for item in st.session_state.audit_schedules if item["Audit_Title"] == sel_task)
        key = f"{task['Tipe']}_{task['Lokasi']}"
        
        if key in st.session_state.master_templates:
            checklist = st.session_state.master_templates[key]
            current_audit_results = []
            
            # Form Pengisian Audit
            for i, item in enumerate(checklist):
                with st.container(border=True):
                    st.write(f"**{item['No']}. {item['Kriteria']}**")
                    c1, c2, c3 = st.columns([1, 2, 1])
                    status = c1.radio("Status", ["OK", "Minor", "Major", "Kritis"], key=f"ex_s_{i}")
                    note = c2.text_area("Temuan", key=f"ex_n_{i}")
                    photo = c3.file_uploader("Foto", type=['jpg','png'], key=f"ex_p_{i}")
                    current_audit_results.append({"kriteria": item['Kriteria'], "status": status, "note": note, "photo": photo})
            
            # Tombol Hitung
            if st.button("Selesaikan Audit & Hitung Scoring"):
                skor, grade, pinalti = calculate_score(current_audit_results)
                # Simpan ke session state agar tidak hilang saat tombol simpan muncul
                st.session_state.temp_results = {
                    "skor": skor, 
                    "grade": grade, 
                    "pinalti": pinalti, 
                    "results": current_audit_results
                }

            # Tampilkan Summary jika data sudah dihitung
            if st.session_state.temp_results:
                tr = st.session_state.temp_results
                st.divider()
                st.subheader("📋 Summary Hasil Audit")
                
                sum_c1, sum_c2, sum_c3 = st.columns(3)
                sum_c1.metric("SKOR AKHIR", tr['skor'])
                sum_c2.metric("GRADE", tr['grade'])
                sum_c3.write(f"**Detail Pinalti:**")
                sum_c3.write(f"Minor: {tr['pinalti'][0]} | Major: {tr['pinalti'][1]} | Kritis: {tr['pinalti'][2]}")
                
                st.write("---")
                st.write("**PENGESAHAN (Tanda Tangan Digital)**")
                sig1, sig2 = st.columns(2)
                auditor_sign = sig1.text_input("Nama Auditor", value=task['Auditor'])
                auditee_sign = sig2.text_input("Nama Auditee", value=task['Auditee'])
                
                if st.button("Simpan Laporan Final"):
                    # Masukkan ke history
                    final_data = {
                        **task, 
                        "Skor": tr['skor'], 
                        "Grade": tr['grade'], 
                        "Detail": tr['results'], 
                        "Tgl_Audit": str(datetime.now().date()), 
                        "Audit_ID": f"AUD-{datetime.now().strftime('%H%M%S')}"
                    }
                    st.session_state.audit_history.append(final_data)
                    
                    # Update status jadwal
                    task['Status'] = "Completed"
                    
                    # Reset temp_results agar bersih untuk audit berikutnya
                    st.session_state.temp_results = None
                    
                    st.success("Laporan Final Berhasil Disimpan!")
                    st.rerun()
                    
        else: 
            st.error(f"Form Master '{key}' belum ada. Silakan upload di Module Master.")
    else: 
        st.info("Tidak ada jadwal audit outstanding.")

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
