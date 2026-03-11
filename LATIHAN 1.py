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
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 5px solid #0083B0;
        }
        .header-container {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 2px solid #0083B0;
            margin-bottom: 20px;
        }
        .sidebar-name-card {
            background: linear-gradient(135deg, #00B4DB, #0083B0);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 3px solid #ffffff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            margin-top: -10px;
        }
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

# ================== FUNGSI LOGIN ==================
def check_password():
    if "password_correct" not in st.session_state:
        _, col_mid, _ = st.columns([1, 1.5, 1])
        with col_mid:
            st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
            user_id = st.text_input("👤 Masukkan ID:", key="user_id")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password", key="user_pass")
            if st.button("Log Masuk", use_container_width=True):
                if user_id == "1" and password == "admin123":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("😕 ID atau Kata Laluan salah.")
        return False
    return True

# ================== MAIN APP ==================
if check_password():
    
    # --- SIDEBAR PROFIL ---
    with st.sidebar:
        if os.path.exists("profile_img.jpg"): # Mengikut nama fail yang anda muat naik
            st.image("profile_img.jpg", use_container_width=True)
        
        st.markdown("""<div class="sidebar-name-card">
            <h4 style="color: white; margin: 0; font-size: 0.9em;">MUHAMMAD ANIQ IRFAN</h4>
            <p style="color: #e0f7fa; font-size: 0.75em; margin:0;">SURVEYOR BERDAFTAR (ID: 1)</p>
        </div><br>""", unsafe_allow_html=True)

        st.header("⚙️ Tetapan Peta")
        map_type = st.radio("Pilih Mod Peta:", ["Google Satellite", "Google Street View"])
        
        st.markdown("---")
        st.subheader("👁️ Paparan Data")
        show_bearing = st.checkbox("Papar Bearing", value=True)
        show_distance = st.checkbox("Papar Jarak", value=True)
        show_area_label = st.checkbox("Papar Label Luas", value=True)
        
        st.markdown("---")
        st.subheader("🎨 Estetika")
        poly_color = st.sidebar.color_picker("Warna Kawasan", "#6036AF")
        poly_opacity = st.sidebar.slider("Kelegapan", 0.0, 1.0, 0.4)
        
        uploaded_file = st.sidebar.file_uploader("Muat Naik CSV", type=["csv"])

    # --- HEADER ---
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    col_logo, col_text, col_profile_img = st.columns([1, 3.5, 0.8])
    with col_text:
        st.markdown("""
            <h1 style="margin:0;">SISTEM SURVEY LOT</h1>
            <p style="color: #555;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
            <div style="background:#e3f2fd; padding:10px; border-left:6px solid #0083B0; border-radius:8px;">
                <b>PENGENDALI:</b> MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI
            </div>
        """, unsafe_allow_html=True)
    with col_profile_img:
        if os.path.exists("profile_img.jpg"):
            st.markdown('<div class="profile-frame">', unsafe_allow_html=True)
            st.image("profile_img.jpg", width=90)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- LOGIK PEMETAAN ---
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if all(col in df.columns for col in ['STN', 'E', 'N']):
            transformer = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = transformer.transform(df['E'].values, df['N'].values)
            
            coords = list(zip(df['lat'], df['lon']))
            poly_geom = Polygon(list(zip(df['E'], df['N'])))
            area = poly_geom.area

            # Ringkasan
            c1, c2, c3 = st.columns(3)
            c1.metric("Luas (m²)", f"{area:.2f}")
            c2.metric("Luas (Ekar)", f"{area/4046.856:.4f}")
            c3.metric("Bil. Stesen", len(df))

            # Konfigurasi Folium
            tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Google Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=tiles, attr='Google')

            # Lukis Poligon
            folium.Polygon(
                locations=coords,
                color="yellow",
                fill=True,
                fill_color=poly_color,
                fill_opacity=poly_opacity,
                weight=3
            ).add_to(m)

            # Lukis Bearing, Jarak & Stesen
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                # Kira Bearing & Jarak (Satah)
                dE, dN = p2['E'] - p1['E'], p2['N'] - p1['N']
                dist = np.sqrt(dE**2 + dN**2)
                bearing = (np.degrees(np.arctan2(dE, dN)) + 360) % 360
                
                # Tambah Marker Stesen
                folium.CircleMarker(
                    [p1['lat'], p1['lon']], radius=5, color='red', fill=True,
                    tooltip=f"Stesen: {int(p1['STN'])}<br>E: {p1['E']:.2f}<br>N: {p1['N']:.2f}"
                ).add_to(m)

                # Label di tengah garisan
                mid_lat, mid_lon = (p1['lat'] + p2['lat'])/2, (p1['lon'] + p2['lon'])/2
                label_html = ""
                if show_bearing: label_html += f"<b>{format_dms(bearing)}</b><br>"
                if show_distance: label_html += f"<span style='color:yellow;'>{dist:.2f}m</span>"
                
                if label_html:
                    folium.Marker(
                        [mid_lat, mid_lon],
                        icon=folium.DivIcon(html=f'<div style="font-size: 8pt; color: white; text-shadow: 1px 1px black; width:100px;">{label_html}</div>')
                    ).add_to(m)

            # Label Luas di tengah poligon
            if show_area_label:
                folium.Marker(
                    [df['lat'].mean(), df['lon'].mean()],
                    icon=folium.DivIcon(html=f'<div style="font-size: 14pt; color: #00FF00; font-weight: bold; text-shadow: 2px 2px black; width:200px; text-align:center;">LUAS: {area:.2f} m²</div>')
                ).add_to(m)

            folium_static(m, width=1100, height=600)
            st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
    else:
        st.info("👋 Sila muat naik fail CSV untuk melihat peta.")
