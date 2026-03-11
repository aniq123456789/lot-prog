import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point, LineString, mapping
import json
import os
import folium 
from streamlit_folium import folium_static 
from pyproj import Transformer

# Set layout halaman
st.set_page_config(page_title="Sistem Survey Lot PUO", layout="wide")

# ================== FUNGSI TUKAR DMS ==================
def format_dms(decimal_degree):
    d = int(decimal_degree)
    m = int((decimal_degree - d) * 60)
    s = round((((decimal_degree - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

# ================== FUNGSI LOGIN & KEMASKINI ==================
@st.dialog("🔑 Kemaskini Kata Laluan")
def reset_password_dialog():
    st.info("Sila sahkan ID untuk menetapkan semula kata laluan.")
    id_sah = st.text_input("Sahkan ID Pengguna:")
    pass_baru = st.text_input("Kata Laluan Baharu:", type="password")
    pass_sah = st.text_input("Sahkan Kata Laluan Baharu:", type="password")
    
    if st.button("Simpan Kata Laluan", use_container_width=True):
        if id_sah == "1" and pass_baru == pass_sah and pass_baru != "":
            st.success("✅ Kata laluan berjaya dikemaskini!")
            st.rerun()
        else:
            st.error("❌ Maklumat tidak sepadan atau kosong.")

def check_password():
    if "password_correct" not in st.session_state:
        _, col_mid, _ = st.columns([1, 1.5, 1])
        with col_mid:
            st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
            user_id = st.text_input("👤 Masukkan ID:", key="user_id")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password", key="user_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Log Masuk", use_container_width=True):
                if user_id == "1" and password == "admin123":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("😕 ID atau Kata Laluan salah.")
            
            if st.button("❓ Lupa Kata Laluan?", use_container_width=True):
                reset_password_dialog()
        return False
    return True

# ================== MAIN APP (SELEPAS LOGIN) ==================
if check_password():
    
    # --- 👤 PROFIL PENGGUNA (SIDEBAR) ---
    # 1. Ruangan Gambar di Atas
    if os.path.exists("profile.jpg"):
        st.sidebar.image("profile.jpg", use_container_width=True)
    else:
        st.sidebar.warning("📸 Fail 'profile.jpg' tidak dijumpai.")

    # 2. Ruangan (Kotak) Nama di Bawah Gambar
    st.sidebar.markdown(
        """
        <div style="background: linear-gradient(135deg, #00B4DB, #0083B0); padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #ffffff;">
            <h4 style="color: white; margin: 0; font-family: sans-serif; font-size: 0.9em;">MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</h4>
            <hr style="margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.3);">
            <p style="color: #f0f0f0; font-size: 0.75em; margin-bottom: 0px;">Surveyor Berdaftar (ID: 1)</p>
        </div>
        <br>
        """, unsafe_allow_html=True
    )

    # --- BAHAGIAN HEADER UTAMA ---
    col_logo, col_text, col_profile_img = st.columns([1, 3.5, 0.8])
    
    with col_logo:
        if os.path.exists("Poli_Logo.png"):
            st.image("Poli_Logo.png", width=140)
        else:
            st.info("🏢 PUO")

    with col_text:
        st.markdown("""
            <style>
                .main-title { font-family: 'Arial Black', sans-serif; font-size: 38px; font-weight: 900; color: #1E1E1E; margin-bottom: -10px; }
                .sub-title { font-size: 16px; color: #555; }
                .name-box { background-color: #f0f2f6; padding: 10px; border-radius: 8px; border-left: 5px solid #0083B0; margin-top: 10px; }
            </style>
            <div>
                <h1 class="main-title">SISTEM SURVEY LOT</h1>
                <p class="sub-title">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
                <div class="name-box">
                    <span style="color: #333; font-weight: bold;">PENGENDALI:</span> 
                    <span style="color: #0083B0; font-weight: 800;">MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_profile_img:
        # Gambar kecil di header (atas kanan)
        if os.path.exists("profile.jpg"):
            st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
            st.image("profile.jpg", width=100)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border: 1px solid #eee; margin-top: 15px;'>", unsafe_allow_html=True)

    # ================== SIDEBAR SETTINGS ==================
    st.sidebar.header("⚙️ Tetapan Paparan")
    uploaded_file = st.sidebar.file_uploader("Upload fail CSV", type=["csv"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Mod Peta Interaktif")
    show_interactive_map = st.sidebar.toggle("Aktifkan Peta Google", value=True)
    map_provider = st.sidebar.radio("Pilih Jenis Peta:", ["Satelit (Hybrid)", "Standard Map"], index=0, disabled=not show_interactive_map)

    # --- PILIHAN WARNA & GAYA ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Estetika Pelan")
    poly_color = st.sidebar.color_picker("Warna Kawasan", "#6036AF") 
    line_color = st.sidebar.color_picker("Warna Sempadan", "#FFFF00") 
    poly_opacity = st.sidebar.slider("Kelegapan", 0.0, 1.0, 0.3)

    # ... (Bahagian kod selebihnya kekal sama seperti sebelum ini) ...
    # Saya ringkaskan bahagian bawah untuk menjimatkan ruang, anda boleh teruskan guna logic data anda
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if all(col in df.columns for col in ['STN', 'E', 'N']):
                transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
                df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
                
                coords_en = list(zip(df['E'], df['N']))
                coords_ll = list(zip(df['lon'], df['lat']))
                poly_geom = Polygon(coords_en)
                poly_ll = Polygon(coords_ll) 
                area = poly_geom.area

                # METRIK
                st.markdown("### 📊 Ringkasan Lot")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Luas (m²)", f"{area:.2f}")
                c2.metric("Luas (Ekar)", f"{area/4046.856:.4f}")
                c3.metric("Stesen", len(df))
                c4.metric("Status", "Tutup")

                st.markdown("---")
                # Kod visualisasi peta anda di sini...
                if show_interactive_map:
                    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19)
                    folium.Polygon(locations=[[r['lat'], r['lon']] for _, r in df.iterrows()], color=line_color, fill=True, fill_color=poly_color, fill_opacity=poly_opacity).add_to(m)
                    folium_static(m, width=1000, height=600)
                
                st.subheader("📋 Jadual Data")
                st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)

        except Exception as e:
            st.error(f"Ralat: {e}")
    else:
        st.info("👋 Sila muat naik fail CSV untuk melihat hasil.")
