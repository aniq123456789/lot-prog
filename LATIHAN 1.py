import streamlit as st
import pd as pd
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

# 2. Fungsi Background
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

bg_img = get_base64("RUANG.jfif")

# 3. CSS
st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/jfif;base64,{bg_img}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(248, 249, 250, 0.95);
            border-right: 5px solid #0083B0;
        }}
        .header-clean {{
            text-align: center;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .header-clean h1 {{
            color: white !important;
            font-size: 3em !important;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.8);
        }}
        .pengendali {{
            color: #00d4ff !important;
            font-weight: bold;
            font-size: 1.3em;
        }}
        .data-card {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.2);
            color: white !important;
        }}
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
            color: white !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 4. Fungsi Format DMS
def format_dms(dd):
    d = int(dd)
    m = int((dd - d) * 60)
    s = round((((dd - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

# 5. Auth Session
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='data-card' style='text-align:center;'><h3>🔐 Log Masuk</h3>", unsafe_allow_html=True)
        id_user = st.text_input("ID:")
        pw_user = st.text_input("Password:", type="password")
        allowed_users = ["1", "2", "3"]
        if st.button("Masuk", use_container_width=True):
            if id_user in allowed_users and pw_user == "admin123":
                st.session_state.auth = True
                st.session_state.user_id = id_user
                st.rerun()
            else:
                st.error("ID atau Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 6. SIDEBAR
with st.sidebar:
    if os.path.exists("image_b5be5f.jpg"):
        st.image("image_b5be5f.jpg")
    st.markdown(f"<h3 style='text-align:center; color:white !important; background:#0083B0; padding:10px; border-radius:10px;'>USER {st.session_state.user_id}</h3>", unsafe_allow_html=True)
    st.write("### ⚙️ Tetapan Peta")
    map_type = st.radio("Pilih Mod Peta:", ["Satellite", "Street View"])
    st.write("### 👁️ Paparan Data")
    show_bearing = st.checkbox("Papar Bearing", value=True)
    show_distance = st.checkbox("Papar Jarak", value=True)
    show_area_label = st.checkbox("Papar Label Luas", value=True)
    uploaded_file = st.file_uploader("Pilih fail CSV anda", type=["csv"])

# 7. HEADER
st.markdown(f"""
    <div class="header-clean">
        <h1>SISTEM SURVEY LOT</h1>
        <p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        <p class="pengendali">PENGENDALI: MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI</p>
    </div>
""", unsafe_allow_html=True)

# 8. LOGIK PEMETAAN (DENGAN FUNGSI HOVER/TOOLTIP)
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
        
        poly = Polygon(list(zip(df['E'], df['N'])))
        area, perimeter = poly.area, poly.length
        
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Luas (m²)", f"{area:.2f}")
        m2.metric("Ekar", f"{area/4046.856:.4f}")
        m3.metric("Perimeter (m)", f"{perimeter:.2f}")
        m4.metric("Stesen", len(df))

        t_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=t_url, attr='Google')
        
        # Plot Polygon Utama
        folium.Polygon(locations=list(zip(df['lat'], df['lon'])), color="yellow", fill=True, fill_opacity=0.2).add_to(m)
        
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            
            # Kira Bearing & Jarak
            dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
            dist = np.sqrt(dE**2 + dN**2)
            brg = (np.degrees(np.arctan2(dE, dN)) + 360) % 360
            
            # --- FUNGSI TOOLTIP (HOVER) ---
            info_hover = f"""
                <div style="font-family: Arial; font-size: 12px; line-height: 1.5;">
                    <b>Stesen:</b> {p1['STN']}<br>
                    <b>E:</b> {p1['E']:.3f}<br>
                    <b>N:</b> {p1['N']:.3f}<br>
                    <hr style='margin:5px 0;'>
                    <b>Ke Stesen:</b> {p2['STN']}<br>
                    <b>Bearing:</b> {format_dms(brg)}<br>
                    <b>Jarak:</b> {dist:.2f}m
                </div>
            """
            
            # Tambah Marker Stesen dengan Tooltip
            folium.CircleMarker(
                location=[p1['lat'], p1['lon']],
                radius=6,
                color='red',
                fill=True,
                fill_color='yellow',
                fill_opacity=1,
                tooltip=folium.Tooltip(info_hover, sticky=True) # Sticky=True supaya info ikut mouse
            ).add_to(m)
            
            # Label Statik (Jika diaktifkan di sidebar)
            mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
            label_text = ""
            if show_bearing: label_text += f"B: {format_dms(brg)}<br>"
            if show_distance: label_text += f"D: {dist:.2f}m"
            if label_text:
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: white; font-weight: bold; text-shadow: 1px 1px black; width: 100px;">{label_text}</div>')).add_to(m)

        if show_area_label:
            folium.Marker([df['lat'].mean(), df['lon'].mean()], icon=folium.DivIcon(html=f'<div style="font-size: 12pt; color: #00FF00; font-weight: bold; text-shadow: 2px 2px black; width: 200px; text-align: center;">LUAS: {area:.2f} m²</div>')).add_to(m)
        
        folium_static(m, width=1000)
        st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Ralat: {e}")
else:
    st.markdown("<div class='data-card' style='text-align:center;'>👋 Sila muat naik fail CSV di sidebar untuk memulakan survey.</div>", unsafe_allow_html=True)
