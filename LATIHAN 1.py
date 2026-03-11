import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
import base64
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Survey Lot PUO", layout="wide")

# Fungsi untuk menukar gambar lokal kepada format yang boleh dibaca CSS
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. Pengurusan Gambar Latar Belakang (RUANG.jfif)
bg_img = get_base64("RUANG.jfif")
bg_style = ""
if bg_img:
    bg_style = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("data:image/jfif;base64,{bg_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
else:
    # Backup jika fail RUANG.jfif tiada
    bg_style = """
    <style>
    .stApp { background-color: #0e1117; }
    </style>
    """

# 3. CSS Tambahan untuk Kacakkan Interface
st.markdown(bg_style + """
    <style>
        /* Card Utama */
        .main-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #0083B0;
            color: black !important;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(248, 249, 250, 0.95);
            border-right: 5px solid #0083B0;
        }

        /* Profile Image Frame */
        .profile-frame {
            border: 3px solid #0083B0;
            border-radius: 10px;
            padding: 2px;
            background: white;
            display: inline-block;
        }

        /* Metric Styling */
        [data-testid="stMetricValue"] {
            color: #1b5e20 !important;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# 4. Fungsi Utiliti
def format_dms(dd):
    d = int(dd)
    m = int((dd - d) * 60)
    s = round((((dd - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

def check_password():
    if "password_correct" not in st.session_state:
        _, col_mid, _ = st.columns([1, 1.5, 1])
        with col_mid:
            st.markdown("<div class='main-card'><h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
            user_id = st.text_input("👤 Masukkan ID:")
            password = st.text_input("🔑 Kata Laluan:", type="password")
            if st.button("Masuk"):
                if user_id == "1" and password == "admin123":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah!")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

# 5. Aplikasi Utama
if check_password():
    # SIDEBAR
    with st.sidebar:
        # Papar gambar profil image_b5be5f.jpg
        profile_path = "image_b5be5f.jpg"
        if os.path.exists(profile_path):
            st.image(profile_path, use_container_width=True)
        
        st.markdown(f"""
            <div style="background:#0083B0; color:white; padding:15px; border-radius:12px; text-align:center;">
                <h4 style="margin:0;">MUHAMMAD ANIQ IRFAN</h4>
                <p style="margin:0; font-size:0.8em;">SURVEYOR BERDAFTAR (ID: 1)</p>
            </div><br>
        """, unsafe_allow_html=True)
        
        st.header("⚙️ Tetapan Peta")
        map_type = st.radio("Pilih Mod Peta:", ["Google Satellite", "Google Street View"])
        uploaded_file = st.sidebar.file_uploader("Muat Naik CSV", type=["csv"])

    # HEADER UTAMA
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([3, 1.5, 1])
    with c1:
        st.markdown("""
            <h1 style="margin:0; color: black;">SISTEM SURVEY LOT</h1>
            <p style="color: #444;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
            <div style="background:#e3f2fd; padding:10px; border-left:6px solid #0083B0; border-radius:8px;">
                <b>PENGENDALI:</b> <span style="color: #0083B0;">MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</span>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        # Visualisasi Geografi
        st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXF4ZzRyeXF4ZzRyeXF4ZzRyeXF4ZzRyeXF4ZzRyeXF4ZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxxcaBQIYJa/giphy.gif", caption="Visualisasi Data", use_container_width=True)
    with c3:
        if os.path.exists(profile_path):
            st.markdown('<div class="profile-frame">', unsafe_allow_html=True)
            st.image(profile_path, width=110)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # PEMPROSESAN DATA
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if all(col in df.columns for col in ['STN', 'E', 'N']):
                tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
                df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
                
                # Metrik
                poly_geom = Polygon(list(zip(df['E'], df['N'])))
                area = poly_geom.area
                
                st.markdown('<div class="main-card">', unsafe_allow_html=True)
                m1, m2, m3 = st.columns(3)
                m1.metric("Luas (m²)", f"{area:.2f}")
                m2.metric("Luas (Ekar)", f"{area/4046.856:.4f}")
                m3.metric("Bil. Stesen", len(df))
                
                # Folium Map
                tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Google Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
                m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=tiles, attr='Google')
                
                folium.Polygon(locations=list(zip(df['lat'], df['lon'])), color="yellow", weight=3, fill=True, fill_opacity=0.4).add_to(m)
                
                # Marker Stesen
                for i, row in df.iterrows():
                    folium.CircleMarker([row['lat'], row['lon']], radius=5, color='red', fill=True).add_to(m)
                
                folium_static(m, width=1050, height=550)
                
                st.write("### 📊 Jadual Data Koordinat")
                st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Ralat teknikal: {e}")
    else:
        st.markdown("<div class='main-card'>👋 Sila muat naik fail CSV untuk melihat pelan lot.</div>", unsafe_allow_html=True)
