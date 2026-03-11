import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import folium
from streamlit_folium import st_folium

# --- 1. FUNGSI LOGIN ---
def login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.markdown("<h2 style='text-align: center;'>Log Masuk Sistem Ukur</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_id = st.text_input("ID Pengguna")
            password = st.text_input("Kata Laluan", type="password")
            submit = st.form_submit_button("Log Masuk")

            if submit:
                if user_id == "1" and password == "admin123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan salah!")
        return False
    return True

# Fungsi Penukaran DMS
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

# --- 2. ATURCARA UTAMA (SELEPAS LOGIN) ---
if login():
    # Butang Log Keluar di Sidebar
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("Sistem Visualisasi Lot & Satelit Google")

    # Bahagian Muat Naik Fail di Sidebar
    st.sidebar.header("Muat Naik Data")
    uploaded_file = st.sidebar.file_uploader("Pilih fail CSV anda", type="csv")

    # Inisialisasi Lokasi Lalai (Kuala Lumpur) jika tiada data
    default_lat, default_lon = 3.1390, 101.6869
    zoom_level = 6  # Pandangan jauh Malaysia pada mulanya

    df = None
    area = 0
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            # Gunakan min purata koordinat sebagai pusat peta
            default_lat = df['N'].mean()
            default_lon = df['E'].mean()
            zoom_level = 19 # Zoom sangat dekat apabila data masuk
            
            # Pengiraan Luas
            e = df['E'].values
            n = df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))

    # --- 3. PAPARAN PETA SATELIT (SENTIASA DIPAPARKAN) ---
    st.write("### 🌍 Pandangan Satelit Google")
    
    # Bina Peta Folium
    # max_zoom=22 membolehkan zoom paling dekat dengan permukaan bumi
    m = folium.Map(location=[default_lat, default_lon], zoom_start=zoom_level, max_zoom=22)

    # Masukkan Layer Google Satellite melalui HTML Tile
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True,
        max_zoom=22
    ).add_to(m)

    # Jika CSV berjaya dimuat naik, cantumkan poligon ke dalam peta satelit
    if df is not None:
        coords_poly = [[df['N'][i], df['E'][i]] for i in range(len(df))]
        # Tambah Poligon Kuning
        folium.Polygon(
            locations=coords_poly,
            color="yellow",
            weight=3,
            fill=True,
            fill_color="yellow",
            fill_opacity=0.3,
            popup=f"Luas Lot: {area:.3f} m²"
        ).add_to(m)
        
        # Tambah Marker untuk setiap stesen
        for i, row in df.iterrows():
            folium.CircleMarker(
                location=[row['N'], row['E']],
                radius=3,
                color="red",
                fill=True,
                popup=f"STN: {row.get('STN', i+1)}"
            ).add_to(m)

    # Paparkan Peta folium dalam Streamlit
    st_folium(m, width=1000, height=600, returned_objects=[])

    # --- 4. PAPARAN DATA TEKNIKAL (HANYA JIKA CSV DIBUKA) ---
    if df is not None:
        st.write("---")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### 📋 Pratinjau Data:")
            st.dataframe(df)
            st.metric("Jumlah Luas", f"{area:.3f} m²")

        with col2:
            st.write("### 📐 Pelan Teknikal (Matplotlib):")
            fig, ax = plt.subplots(figsize=(8, 8))
            e_p = df['E'].tolist() + [df['E'][0]]
            n_p = df['N'].tolist() + [df['N'][0]]
            ax.plot(e_p, n_p, marker='o', color='b', linewidth=2)
            ax.fill(e_p, n_p, alpha=0.2, color='skyblue')
            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig)

        # Butang Export GeoJSON
        poly_coords_json = [[df['E'][i], df['N'][i]] for i in range(len(df))] + [[df['E'][0], df['N'][0]]]
        features = [{
            "type": "Feature",
            "properties": {"Luas_m2": area},
            "geometry": {"type": "Polygon", "coordinates": [poly_coords_json]}
        }]
        geojson_string = json.dumps({"type": "FeatureCollection", "features": features})
        st.sidebar.download_button("📥 Muat Turun GeoJSON", geojson_string, file_name="lot_tanah.geojson")
    else:
        st.info("Sila muat naik fail CSV di bahagian sidebar untuk memaparkan poligon di atas satelit.")
