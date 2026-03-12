import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
import base64
import json
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon, LineString, Point

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

# 3. CSS Style (DIKEMASKINI)
st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/jfif;base64,{bg_img}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: rgba(248, 249, 250, 0.95);
            border-right: 5px solid #0083B0;
        }}
        
        /* Paksa Teks Sidebar Jadi Hitam */
        [data-testid="stSidebar"] .stMarkdown p, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stRadio div,
        [data-testid="stSidebar"] .stCheckbox div {{
            color: #000000 !important;
            font-weight: 700 !important;
        }}

        /* KHUSUS UNTUK MULTISELECT */
        span[data-baseweb="tag"] {{
            background-color: #0083B0 !important;
            color: white !important;
        }}
        div[data-baseweb="select"] {{
            color: black !important;
        }}

        .header-clean {{ text-align: center; padding: 20px; margin-bottom: 30px; }}
        .header-clean h1 {{ color: white !important; font-size: 3em !important; text-shadow: 2px 2px 10px rgba(0,0,0,0.8); }}
        
        .data-card {{
            background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px);
            padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);
            color: white !important; margin-bottom: 20px;
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
    st.session_state.user_id = ""

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='data-card' style='text-align:center;'><h3>🔐 Log Masuk</h3>", unsafe_allow_html=True)
        id_user = st.text_input("ID:")
        pw_user = st.text_input("Password:", type="password")
        if st.button("Masuk", use_container_width=True):
            if id_user in ["1", "2", "3"] and pw_user == "admin123":
                st.session_state.auth = True
                st.session_state.user_id = "Muhammad Aniq Irfan Bin Mohd Asmazi"
                st.rerun()
            else: st.error("ID atau Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 6. SIDEBAR
with st.sidebar:
    st.markdown(f"<div style='text-align:center; color:white; background:black; padding:10px; border-radius:10px; font-size: 0.8em;'>PENGENDALI:<br><b>{st.session_state.user_id}</b></div>", unsafe_allow_html=True)
    
    st.write("### ⚙️ Tetapan Peta")
    map_type = st.radio("Pilih Mod Peta:", ["Satellite", "Street View"])
    
    st.write("### 👁️ Paparan Data")
    show_bearing = st.checkbox("Papar Bearing", value=True)
    show_distance = st.checkbox("Papar Jarak", value=True)
    st.divider()
    uploaded_file = st.file_uploader("Muat naik fail CSV", type=["csv"])

# 7. HEADER
st.markdown(f"""<div class="header-clean"><h1>SISTEM SURVEY LOT</h1><p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p></div>""", unsafe_allow_html=True)

# 8. LOGIK UTAMA
if uploaded_file:
    try:
        # Load Data
        df = pd.read_csv(uploaded_file)
        tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
        
        # --- KAWALAN ON/OFF (DIPERBAIKI) ---
        with st.sidebar:
            st.write("### 📍 Kawalan Stesen")
            stn_list = df['STN'].astype(str).tolist()
            # Gunakan session_state untuk simpan pilihan supaya tidak hilang
            selected_stn = st.multiselect(
                "Pilih Stesen untuk ON:", 
                options=stn_list, 
                default=stn_list,
                key="stn_filter"
            )

        # Pengiraan Geometri
        poly_points = list(zip(df['E'], df['N']))
        poly = Polygon(poly_points)
        area, perimeter = poly.area, poly.length

        tab1, tab2 = st.tabs(["🗺️ Paparan Peta", "📋 Analisis & Data"])

        with tab1:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            
            # Setup Map
            t_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, max_zoom=22)
            folium.TileLayer(tiles=t_url, attr='Google', name='Google Maps', max_zoom=22, overlay=False, control=True).add_to(m)
            
            # Lukis Poligon Lot (Sentiasa ada)
            folium.Polygon(
                locations=list(zip(df['lat'], df['lon'])), 
                color="yellow", fill=True, fill_opacity=0.1, weight=2
            ).add_to(m)

            # Lukis Batu Sempadan & Label (Hanya yang dipilih)
            for _, row in df.iterrows():
                stn_id = str(row['STN'])
                
                if stn_id in selected_stn:
                    # Titik Merah (Batu Sempadan)
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=5, color='red', fill=True, fill_color='white', fill_opacity=1,
                        z_index=1000
                    ).add_to(m)
                    
                    # Label Nombor (Contoh: 1, 2, 3)
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        icon=folium.DivIcon(
                            icon_size=(150,36),
                            icon_anchor=(7,20),
                            html=f'<div style="font-size: 10pt; color: white; font-weight: bold; text-shadow: 2px 2px 4px black;">{stn_id}</div>'
                        )
                    ).add_to(m)

            # Lukis Bearing & Jarak
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                if show_bearing or show_distance:
                    mid_lat = (p1['lat'] + p2['lat']) / 2
                    mid_lon = (p1['lon'] + p2['lon']) / 2
                    dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                    brg = (np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) + 360) % 360
                    
                    txt = f"{format_dms(brg) if show_bearing else ''}<br>{f'{dist:.2f}m' if show_distance else ''}"
                    
                    folium.Marker(
                        [mid_lat, mid_lon],
                        icon=folium.DivIcon(html=f'<div style="font-size:8pt; color:yellow; font-weight:bold; text-shadow:1px 1px black; width:100px;">{txt}</div>')
                    ).add_to(m)
            
            folium_static(m, width=1100)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            st.write(f"**Luas:** {area:.2f} m² | **Perimeter:** {perimeter:.2f} m")
            st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sila pastikan fail CSV mengandungi kolum STN, E, N. Ralat: {e}")
else:
    st.info("Sila muat naik fail CSV di sidebar.")
