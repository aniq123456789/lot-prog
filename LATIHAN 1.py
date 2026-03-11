import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Survey Lot PUO", layout="wide")

# 2. Gaya Visual (CSS) - Latar Belakang Ruang Angkasa
st.markdown("""
    <style>
        .stApp {
            background: url("https://media.giphy.com/media/3o7TKVUn7iM8FMEU24/giphy.gif");
            background-size: cover;
            background-attachment: fixed;
        }
        .main-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            color: black;
            margin-bottom: 20px;
        }
        [data-testid="stMetricValue"] {
            color: #00FF00 !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Fungsi Utiliti
def format_dms(dd):
    d = int(dd)
    m = int((dd - d) * 60)
    s = round((((dd - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<div class='main-card'><h2>🔐 Log Masuk Sistem</h2></div>", unsafe_allow_html=True)
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type="password")
        if st.button("Masuk"):
            if user_id == "1" and password == "admin123":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan salah")
        return False
    return True

# 4. Aplikasi Utama
if check_password():
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Tetapan")
        map_type = st.radio("Jenis Peta", ["Satellite", "Street View"])
        show_bearing = st.checkbox("Papar Bearing", value=True)
        show_distance = st.checkbox("Papar Jarak", value=True)
        uploaded_file = st.file_uploader("Muat Naik CSV", type=["csv"])

    # Header
    st.markdown(f"""
        <div class="main-card">
            <h1>SISTEM SURVEY LOT PUO</h1>
            <p>Jabatan Kejuruteraan Awam</p>
            <hr>
            <b>PENGENDALI:</b> MUHAMMAD ANIQ IRFAN BIN MOHD ASMAZI
        </div>
    """, unsafe_allow_html=True)

    # Proses Data & Peta
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            # Tukar Koordinat (Cassini ke WGS84)
            tf = Transformer.from_crs("EPSG:4390", "EPSG:4326", always_xy=True)
            df['lon'], df['lat'] = tf.transform(df['E'].values, df['N'].values)
            
            # Kira Luas
            poly = Polygon(list(zip(df['E'], df['N'])))
            area = poly.area

            # Papar Metrik
            c1, c2, c3 = st.columns(3)
            c1.metric("Luas (m²)", f"{area:.2f}")
            c2.metric("Luas (Ekar)", f"{area/4046.856:.4f}")
            c3.metric("Stesen", len(df))

            # Konfigurasi Peta Folium
            tile_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19, tiles=tile_url, attr='Google')

            # Lukis Polygon
            coords = list(zip(df['lat'], df['lon']))
            folium.Polygon(locations=coords, color="yellow", fill=True, fill_opacity=0.4).add_to(m)

            # Tambah Label & Marker
            for i in range(len(df)):
                p1 = df.iloc[i]
                p2 = df.iloc[(i + 1) % len(df)]
                
                # Kira Jarak & Bearing
                dist = np.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                brg = (np.degrees(np.arctan2(p2['E']-p1['E'], p2['N']-p1['N'])) + 360) % 360
                
                # Marker Stesen
                folium.CircleMarker([p1['lat'], p1['lon']], radius=4, color='red').add_to(m)
                
                # Label Tengah Garisan
                mid_lat, mid_lon = (p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2
                txt = ""
                if show_bearing: txt += f"{format_dms(brg)}<br>"
                if show_distance: txt += f"{dist:.2f}m"
                
                folium.Marker([mid_lat, mid_lon], icon=folium.DivIcon(html=f'<div style="font-size:8pt; color:white; text-shadow:1px 1px black;">{txt}</div>')).add_to(m)

            folium_static(m, width=1000)
            st.dataframe(df[['STN', 'E', 'N']], use_container_width=True)

        except Exception as e:
            st.error(f"Ralat: {e}")
    else:
        st.info("Sila muat naik fail CSV di bahagian sidebar.")
