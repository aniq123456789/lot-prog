import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
import base64
import json
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon, mapping

# 1. Konfigurasi Halaman (Mesti paling atas)
st.set_page_config(page_title="Sistem Survey Lot PUO", layout="wide")

# 2. Fungsi Background
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

bg_img = get_base64("RUANG.jfif")

# 3. CSS Style
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
    st.session_state.user_id = ""

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
    st.markdown(f"<h3 style='text-align:center; color:white !important; background:#0083B0; padding:10px; border-radius:10px;'>PENGENDALI: {st.session_state.user_id}</h3>", unsafe_allow_html=True)
    
    st.write("### ⚙️ Tetapan Peta")
    map_type = st.radio("Pilih Mod Peta:", ["Satellite", "Street View"])
    
    st.write("### 👁️ Paparan Data")
    show_bearing = st.checkbox("Papar Bearing", value=True)
    show_distance = st.checkbox("Papar Jarak", value=True)
    show_area_label = st.checkbox("Papar Label Luas", value=True)
    
    st.divider()
    uploaded_file = st.file_uploader("Muat naik fail CSV", type=["csv"])

# 7. HEADER UTAMA
st.markdown(f"""
    <div class="header-clean">
        <h1>SISTEM SURVEY LOT</h1>
        <p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        <p style="color:#00d4ff !important; font-weight:bold;">PENGENDALI: MUHAMMAD ANIQ IRFAN</p>
    </div>
""", unsafe_allow_html=True)

# 8. LOGIK UTAMA
if uploaded_file:
    try:
        # Baca Data
        df = pd.read_csv(uploaded_file)
        
        # Transformasi Koordinat (Cassini EPSG:4390 ke WGS84 EPSG:4326)
        tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
        df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
        
        # Kira Luas & Perimeter
        poly_points = list(zip(df['E'], df['N']))
        poly = Polygon(poly_points)
        area = poly.area
        perimeter = poly.length
        
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        
        # Metrik Atas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Luas (m²)", f"{area:.2f}")
        m2.metric("Ekar", f"{area/4046.856:.4f}")
        m3.metric("Perimeter (m)", f"{perimeter:.2f}")
        m4.metric("Stesen", len(df))

        # Peta Folium
        t_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=t_url, attr='Google')
        
        # Lukis Lot
        folium.Polygon(
            locations=list(zip(df['lat'], df['lon'])),
            color="yellow", fill=True, fill_opacity=0.3, weight=3
        ).add_to(m)

        # Tambah Marker & Label
        for i in range(len(df)):
            p1 = df.iloc[i]
            p2 = df.iloc[(i + 1) % len(df)]
            dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
            brg = (np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) + 360) % 360
            
            folium.CircleMarker([p1['lat'], p1['lon']], radius=5, color='red', fill=True).add_to(m)
            
            if show_bearing or show_distance:
                mid_lat, mid_lon = (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2
                label = f"{format_dms(brg) if show_bearing else ''}<br>{f'{dist:.2f}m' if show_distance else ''}"
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f'<div style="font-size:8pt; color:yellow; font-weight:bold; text-shadow:1px 1px black; width:100px;">{label}</div>')).add_to(m)

        folium_static(m, width=1100)

        # 9. EKSPORT GEOJSON (Bahagian ini punca error tadi jika tak kena gaya)
        st.divider()
        st.write("### 📊 Jadual & Export")
        c1, c2 = st.columns([3, 1])
        
        with c1:
            st.dataframe(df[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
            
        with c2:
            # Sediakan fail GeoJSON
            geojson_data = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {
                        "Pengendali": st.session_state.user_id,
                        "Luas_m2": round(area, 2),
                        "Perimeter_m": round(perimeter, 2)
                    },
                    "geometry": mapping(Polygon(list(zip(df['lon'], df['lat']))))
                }]
            }
            geojson_str = json.dumps(geojson_data)
            
            st.download_button(
                label="📥 Download GeoJSON (QGIS)",
                data=geojson_str,
                file_name=f"Survey_Lot_{st.session_state.user_id}.geojson",
                mime="application/json",
                use_container_width=True
            )
            
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Ralat: {e}")

else:
    st.markdown("<div class='data-card' style='text-align:center;'>👋 Sila muat naik fail CSV di sidebar untuk memulakan survey.</div>", unsafe_allow_html=True)
