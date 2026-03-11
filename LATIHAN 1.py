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

# 2. Fungsi tukar gambar lokal ke Base64 (Untuk Background)
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# Ambil data gambar RUANG.jfif
bg_img = get_base64("RUANG.jfif")

# 3. CSS untuk Antaramuka
st.markdown(f"""
    <style>
        /* Background Utama */
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/jfif;base64,{bg_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: rgba(248, 249, 250, 0.9);
            border-right: 5px solid #0083B0;
        }}

        /* Header Container */
        .header-container {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            border: 2px solid #0083B0;
            margin-bottom: 20px;
        }}

        /* Kotak Data (Metric & Table) */
        .data-card {{
            background: rgba(255, 255, 255, 0.85);
            padding: 20px;
            border-radius: 12px;
            color: black !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. Fungsi DMS & Login Ringkas
def format_dms(dd):
    d = int(dd); m = int((dd - d) * 60); s = round((((dd - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Log Masuk")
        id_user = st.text_input("ID:")
        pw_user = st.text_input("Password:", type="password")
        if st.button("Masuk"):
            if id_user == "1" and pw_user == "admin123":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Salah!")
    st.stop()

# 5. Aplikasi Utama
with st.sidebar:
    if os.path.exists("image_b5be5f.jpg"):
        st.image("image_b5be5f.jpg")
    st.markdown("<h4 style='text-align:center;'>MUHAMMAD ANIQ IRFAN</h4>", unsafe_allow_html=True)
    map_type = st.radio("Mod Peta:", ["Satellite", "Street View"])
    uploaded_file = st.file_uploader("Muat Naik CSV", type=["csv"])

# --- HEADER (Tiada GIF/Video) ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown("""
        <h1 style='color:black; margin:0;'>SISTEM SURVEY LOT</h1>
        <p style='color:black;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        <p style='color:#0083B0; font-weight:bold;'>PENGENDALI: MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</p>
    """, unsafe_allow_html=True)
with c2:
    if os.path.exists("image_b5be5f.jpg"):
        st.image("image_b5be5f.jpg", width=100)
st.markdown('</div>', unsafe_allow_html=True)

# 6. Logik Pemetaan
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
    df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
    
    st.markdown('<div class="data-card">', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    poly = Polygon(list(zip(df['E'], df['N'])))
    m1.metric("Luas (m²)", f"{poly.area:.2f}")
    m2.metric("Ekar", f"{poly.area/4046.856:.4f}")
    m3.metric("Stesen", len(df))

    t_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=t_url, attr='Google')
    folium.Polygon(locations=list(zip(df['lat'], df['lon'])), color="yellow", fill=True).add_to(m)
    
    folium_static(m, width=1000)
    st.write("### Data Koordinat")
    st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Sila muat naik fail CSV di sidebar.")
