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

# 2. Fungsi Background (RUANG.jfif)
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

bg_img = get_base64("RUANG.jfif")

# 3. CSS - FOKUS WARNA HITAM DI SIDEBAR
st.markdown(f"""
    <style>
        /* Background Utama */
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/jfif;base64,{bg_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* SIDEBAR: Paksa semua tulisan jadi HITAM */
        [data-testid="stSidebar"] {{
            background-color: rgba(248, 249, 250, 0.95);
            border-right: 5px solid #0083B0;
        }}
        
        /* Menyasarkan semua label, teks, dan radio button dalam sidebar */
        [data-testid="stSidebar"] .stText, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] .stMarkdown p {{
            color: #000000 !important;
            font-weight: 600 !important;
        }}

        /* Header & Data Card */
        .header-container {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            border: 2px solid #0083B0;
            margin-bottom: 20px;
        }}
        .data-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 12px;
            color: black !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. Auth Session
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='data-card' style='text-align:center;'><h3>🔐 Log Masuk</h3>", unsafe_allow_html=True)
        id_user = st.text_input("ID:")
        pw_user = st.text_input("Password:", type="password")
        if st.button("Masuk", use_container_width=True):
            if id_user == "1" and pw_user == "admin123":
                st.session_state.auth = True
                st.rerun()
            else: st.error("ID/Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 5. SIDEBAR (Tulisan kini Hitam)
with st.sidebar:
    if os.path.exists("image_b5be5f.jpg"):
        st.image("image_b5be5f.jpg")
    st.markdown("<h3 style='text-align:center; color:white; background:#0083B0; padding:10px; border-radius:10px;'>MUHAMMAD ANIQ IRFAN</h3>", unsafe_allow_html=True)
    
    st.write("### ⚙️ Tetapan Peta")
    map_type = st.radio("Pilih Mod Peta:", ["Satellite", "Street View"])
    
    st.write("### 📂 Muat Naik Data")
    uploaded_file = st.file_uploader("Pilih fail CSV anda", type=["csv"])

# 6. HEADER UTAMA
st.markdown('<div class="header-container">', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])
with c1:
    st.markdown("""
        <h1 style='color:black; margin:0;'>SISTEM SURVEY LOT</h1>
        <p style='color:black; font-size:1.1em;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        <p style='color:#0083B0; font-weight:bold; font-size:1.2em;'>PENGENDALI: MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</p>
    """, unsafe_allow_html=True)
with c2:
    if os.path.exists("image_b5be5f.jpg"):
        st.image("image_b5be5f.jpg", width=100)
st.markdown('</div>', unsafe_allow_html=True)

# 7. LOGIK PEMETAAN
if uploaded_file:
    try:
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
        folium.Polygon(locations=list(zip(df['lat'], df['lon'])), color="yellow", fill=True, weight=3).add_to(m)
        
        folium_static(m, width=1000)
        st.write("### 📊 Jadual Koordinat")
        st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Ralat: {e}")
else:
    st.markdown("<div class='data-card' style='text-align:center;'>👋 Sila muat naik fail CSV di sidebar untuk memulakan survey.</div>", unsafe_allow_html=True)
