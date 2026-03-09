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

# --- 2. ATURCARA UTAMA ---
if login():
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("Sistem Visualisasi Lot & Satelit Google")

    st.sidebar.header("Muat Naik Data")
    uploaded_file = st.sidebar.file_uploader("Pilih fail CSV anda", type="csv")

    # Lokasi default jika tiada fail
    default_lat, default_lon = 4.2105, 101.9758 # Tengah Malaysia
    zoom_level = 6

    df = None
    area = 0
    bounds = None

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            # Pastikan data adalah float
            df['E'] = df['E'].astype(float)
            df['N'] = df['N'].astype(float)
            
            default_lat = df['N'].mean()
            default_lon = df['E'].mean()
            zoom_level = 19 # Zoom dekat
            
            # Kira Luas (Formula Shoelace)
            e = df['E'].values
            n = df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))
            
            # Dapatkan sempadan untuk Auto-Zoom
            bounds = [[df['N'].min(), df['E'].min()], [df['N'].max(), df['E'].max()]]

    st.write("### 🌍 Pandangan Satelit Google")
    
    # Bina Peta
    m = folium.Map(
        location=[default_lat, default_lon], 
        zoom_start=zoom_level, 
        max_zoom=22,
        control_scale=True
    )

    # Tambah Google Satellite Layer
    google_satellite = folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True,
        max_zoom=22
    ).add_to(m)

    if df is not None:
        # Plot Poligon
        coords_poly = [[row['N'], row['E']] for i, row in df.iterrows()]
        folium.Polygon(
            locations=coords_poly,
            color="yellow",
            weight=3,
            fill=True,
            fill_color="yellow",
            fill_opacity=0.3,
            popup=f"Luas: {area:.2f} m²"
        ).add_to(m)
        
        # Plot Marker Stesen
        for i, row in df.iterrows():
            folium.CircleMarker(
                location=[row['N'], row['E']],
                radius=4,
                color="red",
                fill=True,
                fill_color="white",
                popup=f"STN: {row.get('STN', i+1)}"
            ).add_to(m)
        
        # AUTO ZOOM ke poligon
        if bounds:
            m.fit_bounds(bounds)

    # Paparkan Peta (Gunakan 'key' supaya peta refresh bila file tukar)
    st_folium(m, width=1000, height=500, key="peta_ukur")

    # --- Bahagian Data & Matplotlib ---
    if df is not None:
        st.write("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("### 📋 Data Koordinat")
            st.dataframe(df)
            st.metric("Jumlah Luas", f"{area:.3f} m²")
        with col2:
            st.write("### 📐 Pelan Teknikal")
            fig, ax = plt.subplots()
            e_p = df['E'].tolist() + [df['E'][0]]
            n_p = df['N'].tolist() + [df['N'][0]]
            ax.plot(e_p, n_p, 'b-o')
            ax.fill(e_p, n_p, alpha=0.3)
            ax.set_aspect('equal')
            st.pyplot(fig)
