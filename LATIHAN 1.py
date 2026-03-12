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

# 3. CSS Style (Teks Sidebar Hitam & Estetik)
st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/jfif;base64,{bg_img}");
            background-size: cover; background-position: center; background-attachment: fixed;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: rgba(248, 249, 250, 0.95);
            border-right: 5px solid #0083B0;
        }}
        
        /* Memastikan semua elemen teks di sidebar berwarna hitam */
        [data-testid="stSidebar"] .stMarkdown p, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stRadio div,
        [data-testid="stSidebar"] .stCheckbox div,
        [data-testid="stSidebar"] .stMultiSelect div {{
            color: #000000 !important;
            font-weight: 700 !important;
        }}

        .header-clean {{ text-align: center; padding: 20px; margin-bottom: 30px; }}
        .header-clean h1 {{ color: white !important; font-size: 3em !important; text-shadow: 2px 2px 10px rgba(0,0,0,0.8); }}
        
        .data-card {{
            background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px);
            padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);
            color: white !important; margin-bottom: 20px;
        }}
        
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
            color: white !important;
            font-weight: bold;
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
                # Nama Pengendali Ditetapkan
                st.session_state.user_id = "Muhammad Aniq Irfan Bin Mohd Asmazi"
                st.rerun()
            else: st.error("ID atau Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# 6. SIDEBAR
with st.sidebar:
    if os.path.exists("image_b5be5f.jpg"): st.image("image_b5be5f.jpg")
    st.markdown(f"<div style='text-align:center; color:white; background:black; padding:10px; border-radius:10px; font-size: 0.8em;'>PENGENDALI:<br><b>{st.session_state.user_id}</b></div>", unsafe_allow_html=True)
    
    st.write("### ⚙️ Tetapan Peta")
    map_type = st.radio("Pilih Mod Peta:", ["Satellite", "Street View"])
    
    st.write("### 👁️ Paparan Data")
    show_bearing = st.checkbox("Papar Bearing", value=True)
    show_distance = st.checkbox("Papar Jarak", value=True)
    
    # Placeholder untuk kawalan stesen (akan diisi jika fail dimuat naik)
    st.divider()
    uploaded_file = st.file_uploader("Muat naik fail CSV", type=["csv"])

# 7. HEADER
st.markdown(f"""<div class="header-clean"><h1>SISTEM SURVEY LOT</h1><p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p><p style="color:#00d4ff;">Pengendali: {st.session_state.user_id}</p></div>""", unsafe_allow_html=True)

# 8. LOGIK UTAMA
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
        
        # Tambah Kawalan On/Off Stesen di Sidebar
        with st.sidebar:
            st.write("### 📍 Kawalan Stesen")
            all_stn = df['STN'].astype(str).tolist()
            selected_stn = st.multiselect("Pilih Stesen untuk Dipaparkan:", all_stn, default=all_stn)

        # Pengiraan Geometri
        coords_wgs = list(zip(df['lon'], df['lat']))
        poly_points = list(zip(df['E'], df['N']))
        poly = Polygon(poly_points)
        area, perimeter = poly.area, poly.length

        tab1, tab2 = st.tabs(["🗺️ Paparan Peta", "📋 Analisis & Export QGIS"])

        with tab1:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Luas (m²)", f"{area:.2f}")
            m2.metric("Ekar", f"{area/4046.856:.4f}")
            m3.metric("Perimeter (m)", f"{perimeter:.2f}")
            m4.metric("Jumlah Stesen", len(df))

            t_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, max_zoom=22, tiles=None)
            folium.TileLayer(tiles=t_url, attr='Google', name='Google Maps', max_zoom=22, max_native_zoom=20).add_to(m)
            
            # Lukis Poligon (Sentiasa ada sebagai rujukan lot)
            folium.Polygon(locations=list(zip(df['lat'], df['lon'])), color="yellow", fill=True, fill_opacity=0.3, weight=2).add_to(m)

            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                
                # Papar Marker hanya jika stesen dipilih dalam multiselect
                if str(p1['STN']) in selected_stn:
                    folium.CircleMarker(
                        [p1['lat'], p1['lon']], 
                        radius=6, color='red', fill=True, fill_color='white', fill_opacity=1,
                        popup=f"Stesen: {p1['STN']}"
                    ).add_to(m)
                    
                    # Tooltip label stesen
                    folium.Marker(
                        [p1['lat'], p1['lon']],
                        icon=folium.DivIcon(html=f'<div style="font-size:10pt; color:white; font-weight:bold; background:rgba(0,0,0,0.5); padding:2px; border-radius:3px;">{p1["STN"]}</div>')
                    ).add_to(m)

                # Paparan Bearing/Jarak pada garisan
                dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                brg = (np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) + 360) % 360
                
                if show_bearing or show_distance:
                    mid = [(p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2]
                    label = f"{format_dms(brg) if show_bearing else ''}<br>{f'{dist:.2f}m' if show_distance else ''}"
                    folium.Marker(mid, icon=folium.DivIcon(html=f'<div style="font-size:8pt; color:yellow; font-weight:bold; text-shadow:1px 1px black; width:100px;">{label}</div>')).add_to(m)
            
            folium_static(m, width=1100)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="data-card">', unsafe_allow_html=True)
            st.subheader("📊 Struktur Data QGIS")
            
            features = []
            poly_coords = coords_wgs + [coords_wgs[0]]
            
            # Layer Polygon
            features.append({
                "type": "Feature",
                "properties": {"Layer": "Lot_Polygon", "Nama": f"LOT_{st.session_state.user_id}", "Luas_m2": round(area, 2), "Perimeter": round(perimeter, 2)},
                "geometry": {"type": "Polygon", "coordinates": [poly_coords]}
            })

            # Layer Points
            for _, row in df.iterrows():
                features.append({
                    "type": "Feature",
                    "properties": {"Layer": "Batu_Sempadan", "Station": str(row['STN']), "Easting": row['E'], "Northing": row['N']},
                    "geometry": {"type": "Point", "coordinates": [row['lon'], row['lat']]}
                })

            # Layer Lines
            for i in range(len(df)):
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                d = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                b = (np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) + 360) % 360
                features.append({
                    "type": "Feature",
                    "properties": {"Layer": "Garisan_Lot", "Dari": str(p1['STN']), "Ke": str(p2['STN']), "Bearing": format_dms(b), "Jarak_m": round(d, 2)},
                    "geometry": {"type": "LineString", "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]}
                })

            full_geojson = {"type": "FeatureCollection", "features": features}

            st.write("📍 **Data Koordinat Stesen**")
            st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)

            st.divider()
            st.download_button(
                label="📥 MUAT TURUN FAIL UNTUK QGIS (.geojson)",
                data=json.dumps(full_geojson, indent=4),
                file_name=f"Survey_Lengkap_AniqIrfan.geojson",
                mime="application/json", use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"Ralat: {e}")
else:
    st.markdown("<div class='data-card' style='text-align:center;'>👋 Sila muat naik fail CSV untuk menjana data GIS dan kawalan stesen.</div>", unsafe_allow_html=True)
