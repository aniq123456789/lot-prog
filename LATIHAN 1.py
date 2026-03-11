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

# ================== CSS UNTUK FRAME & GAYA (STYLING) ==================
st.markdown("""
    <style>
        /* Frame untuk Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 5px solid #0083B0;
        }
        
        /* Frame untuk Header Utama */
        .header-container {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 2px solid #0083B0;
            margin-bottom: 20px;
        }

        /* Gaya untuk Kotak Nama Sidebar */
        .sidebar-name-card {
            background: linear-gradient(135deg, #00B4DB, #0083B0);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 3px solid #ffffff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            margin-top: -10px;
        }

        /* Frame Gambar Profil */
        .profile-frame {
            border: 4px solid #0083B0;
            border-radius: 10px;
            padding: 5px;
            background: white;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

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
    with st.sidebar:
        # 1. Gambar Profil dengan Frame
        if os.path.exists("profile.jpg"):
            st.image("profile.jpg", use_container_width=True)
        else:
            st.warning("📸 Sila upload 'profile.jpg'.")

        # 2. Kotak Nama Berbingkai
        st.markdown(
            """
            <div class="sidebar-name-card">
                <h4 style="color: white; margin: 0; font-family: 'Segoe UI', sans-serif; font-size: 0.9em; font-weight: bold;">MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</h4>
                <p style="color: #e0f7fa; font-size: 0.75em; margin-top: 5px; margin-bottom: 0px; letter-spacing: 1px;">SURVEYOR BERDAFTAR (ID: 1)</p>
            </div>
            <br>
            """, unsafe_allow_html=True
        )

    # --- BAHAGIAN HEADER UTAMA DENGAN FRAME ---
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    col_logo, col_text, col_profile_img = st.columns([1, 3.5, 0.8])
    
    with col_logo:
        if os.path.exists("Poli_Logo.png"):
            st.image("Poli_Logo.png", width=130)
        else:
            st.markdown("<h2 style='color:#0083B0;'>PUO</h2>", unsafe_allow_html=True)

    with col_text:
        st.markdown("""
            <div>
                <h1 style="font-family: 'Arial Black', sans-serif; font-size: 40px; font-weight: 900; color: #1E1E1E; margin-bottom: -5px;">SISTEM SURVEY LOT</h1>
                <p style="font-size: 16px; color: #555; margin-bottom: 15px;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
                <div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 6px solid #0083B0;">
                    <span style="color: #333; font-weight: bold; font-size: 0.9em;">PENGENDALI SISTEM:</span><br>
                    <span style="color: #0083B0; font-weight: 800; font-size: 1.2em;">MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_profile_img:
        if os.path.exists("profile.jpg"):
            st.markdown('<div class="profile-frame">', unsafe_allow_html=True)
            st.image("profile.jpg", width=100)
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ================== SIDEBAR SETTINGS ==================
    st.sidebar.header("⚙️ Tetapan Paparan")
    uploaded_file = st.sidebar.file_uploader("Muat Naik Fail CSV Koordinat", type=["csv"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Konfigurasi Peta")
    show_interactive_map = st.sidebar.toggle("Aktifkan Peta Google", value=True)
    map_provider = st.sidebar.radio("Pilih Jenis Peta:", ["Satelit (Hybrid)", "Standard Map"], index=0, disabled=not show_interactive_map)

    # --- PILIHAN WARNA & GAYA ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Estetika Visual")
    poly_color = st.sidebar.color_picker("Warna Kawasan", "#6036AF") 
    line_color = st.sidebar.color_picker("Warna Sempadan", "#FFFF00") 
    poly_opacity = st.sidebar.slider("Tahap Kelegapan", 0.0, 1.0, 0.4)

    # ================== LOGIK DATA ==================
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if all(col in df.columns for col in ['STN', 'E', 'N']):
                # Penukaran Koordinat (Cassini Perak ke WGS84)
                transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
                df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
                
                poly_geom = Polygon(list(zip(df['E'], df['N'])))
                area = poly_geom.area

                # Paparan Ringkasan dalam Kad
                st.markdown("### 📊 Analisis Data Lot")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.info(f"**Luas (m²)**\n\n{area:.2f}")
                with c2: st.info(f"**Luas (Ekar)**\n\n{area/4046.856:.4f}")
                with c3: st.info(f"**Bil. Stesen**\n\n{len(df)}")
                with c4: st.success(f"**Status**\n\nTutup")

                st.markdown("---")
                
                if show_interactive_map:
                    st.subheader("🗺️ Visualisasi Peta Interaktif")
                    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19)
                    folium.Polygon(
                        locations=[[r['lat'], r['lon']] for _, r in df.iterrows()],
                        color=line_color,
                        fill=True,
                        fill_color=poly_color,
                        fill_opacity=poly_opacity,
                        weight=5
                    ).add_to(m)
                    folium_static(m, width=1100, height=600)
                
                st.subheader("📋 Jadual Data Koordinat")
                st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Ralat teknikal dikesan: {e}")
    else:
        st.info("💡 Sila muat naik fail CSV di sidebar untuk memulakan sistem.")
