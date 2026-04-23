import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Digital GMP Audit - Detail & Photo", layout="wide")

st.title("🛡️ Digital GMP Audit System")
st.caption("Mode: Audit Lapangan dengan Detail Temuan & Bukti Foto")

# --- DATABASE SIMULATION ---
if 'audit_db' not in st.session_state:
    st.session_state.audit_db = pd.DataFrame(columns=["Lokasi", "Tanggal", "Skor", "Grade"])

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Pilih Menu", ["📝 Audit Baru", "📊 Dashboard & Report"])

if menu == "📝 Audit Baru":
    # Sidebar Config
    with st.sidebar:
        st.header("⚙️ Konfigurasi")
        uploaded_file = st.file_uploader("Upload Template Checklist (CSV)", type=["csv"])
        st.divider()
        st.header("📝 Info Audit")
        lokasi = st.selectbox("Lokasi Unit", ["Satelite Kitchen NICE PIK2", "Central Kitchen Hub"])
        auditor = st.text_input("Nama Auditor")
        tanggal_audit = st.date_input("Tanggal Audit", datetime.now())

    if uploaded_file is not None:
        df_template = pd.read_csv(uploaded_file, sep=';')
        total_deduction = 0
        audit_records = []

        st.info(f"📋 Form Audit Aktif: {len(df_template)} Kriteria")

        # Form Audit Dinamis
        for kategori, group_kategori in df_template.groupby('Kategori', sort=False):
            with st.expander(f"📂 {kategori}", expanded=True):
                for _, row in group_kategori.iterrows():
                    # Judul Kriteria
                    st.markdown(f"**{row['No']}. {row['Kriteria Penilaian']}** (Area: {row['Area']})")
                    
                    # Layout Kolom: Penilaian | Detail Temuan | Foto
                    col_score, col_note, col_photo = st.columns([2, 3, 2])
                    
                    key_id = f"{row['No']}_{row['Area']}"
                    
                    with col_score:
                        pilihan = st.radio(
                            "Status Penilaian", ["OK", "Minor", "Major", "Kritis"],
                            key=f"status_{key_id}", horizontal=True
                        )
                    
                    with col_note:
                        # KOLOM KETERANGAN (Wajib ada untuk mencatat detail)
                        detail = st.text_area(
                            "Detail Temuan / Catatan", 
                            key=f"note_{key_id}", 
                            placeholder="Tuliskan detail ketidaksesuaian di sini...",
                            height=80
                        )
                    
                    with col_photo:
                        # FITUR FOTO (Membuka kamera di handphone secara otomatis)
                        foto = st.file_uploader(
                            "Ambil/Upload Foto", 
                            type=["jpg", "jpeg", "png"], 
                            key=f"photo_{key_id}"
                        )
                        if foto:
                            st.image(foto, width=150, caption="Preview Foto")

                    # Logika Skor
                    score_map = {"OK": 0, "Minor": -10, "Major": -20, "Kritis": -30}
                    total_deduction += score_map[pilihan]
                    
                    # Simpan Rekaman Sementara
                    if pilihan != "OK":
                        audit_records.append({
                            "No": row['No'],
                            "Kriteria": row['Kriteria Penilaian'],
                            "Status": pilihan,
                            "Detail": detail,
                            "HasPhoto": "Ya" if foto else "Tidak"
                        })
                st.divider()

        # Tombol Submit
        if st.button("Simpan Hasil Audit & Generate Summary", use_container_width=True):
            skor_akhir = max(0, 1000 + total_deduction)
            grade = "A" if skor_akhir >= 860 else "B" if skor_akhir >= 710 else "C" if skor_akhir >= 610 else "D"
            
            # Simpan ke History
            new_audit = {"Lokasi": lokasi, "Tanggal": str(tanggal_audit), "Skor": skor_akhir, "Grade": grade}
            st.session_state.audit_db = pd.concat([st.session_state.audit_db, pd.DataFrame([new_audit])], ignore_index=True)
            
            st.success(f"Audit Selesai! Skor Akhir: {skor_akhir} (Grade {grade})")
            
            if audit_records:
                st.subheader("📋 Ringkasan Detail Temuan")
                st.table(pd.DataFrame(audit_records))

    else:
        st.warning("Silakan upload 'Template Checklist.csv' untuk memunculkan form.")

# --- MENU DASHBOARD TETAP SAMA ---
else:
    st.title("📊 Dashboard & Report History")
    st.dataframe(st.session_state.audit_db, use_container_width=True)
