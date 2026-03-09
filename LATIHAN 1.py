import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

# --- 1. FUNGSI PENUKARAN KOORDINAT (CASSINI KE WGS84) ---
# Senarai EPSG Cassini Negeri di Malaysia
CASSINI_SYSTEMS = {
    "Selangor/KL": "EPSG:3160",
    "Johor": "EPSG:3168",
    "Kedah": "EPSG:3167",
    "Kelantan": "EPSG:3166",
    "Melaka/N.Sembilan": "EPSG:3161",
    "Pahang": "EPSG:3164",
    "Perak": "EPSG:3162",
    "Perlis": "EPSG:3169",
    "Pulau Pinang": "EPSG:3163",
    "Terengganu": "EPSG:3165"
}

def convert_to_wgs84(df, system_code):
    # Tukar Cassini (Meter) ke WGS84 (Lat/Lon)
    transformer = Transformer.from_crs(system_code, "EPSG:4321", always_xy=True)
    lon, lat = transformer.transform(df['E'].values, df['N'].values)
    df['lat_wgs84'] = lat
    df['lon_wgs84'] = lon
    return df

# --- 2. FUNGSI LOGIN ---
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

# --- 3. ATURCARA UTAMA ---
if login():
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("Sistem Visualisasi Lot & Satelit Google")

    st.sidebar.header("Muat Naik Data")
    uploaded_file = st.sidebar.file_uploader("Pilih fail CSV anda", type="csv")
    
    # Pilihan Sistem Koordinat
    selected_state = st.sidebar.selectbox("Pilih Sistem Koordinat (Negeri):", list(CASSINI_SYSTEMS.keys()))
    system_epsg = CASSINI_SYSTEMS[selected_state]

    df = None
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            # Tukar koordinat meter ke Lat/Lon
            try:
                df = convert_to_wgs84(df, system_epsg)
                
                # Kira Luas (Guna koordinat asal E, N dalam meter)
                e = df['E'].values
                n = df['N'].values
                area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))

                # Pusat Peta (Guna Lat/Lon yang baru ditukar)
                center_lat = df['lat_wgs84'].mean()
                center_lon = df['lon_wgs84'].mean()

                st.write(f"### 🌍 Pandangan Satelit - {selected_state}")
                
                # Bina Peta
                m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22)
                
                # Google Satellite Layer
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                    attr='Google', name='Google Satellite', max_zoom=22, overlay=False
                ).add_to(m)

                # Plot Poligon (Guna lat_wgs84, lon_wgs84)
                coords_poly = [[row['lat_wgs84'], row['lon_wgs84']] for i, row in df.iterrows()]
                folium.Polygon(
                    locations=coords_poly, color="yellow", weight=3,
                    fill=True, fill_color="yellow", fill_opacity=0.3,
                    popup=f"Luas: {area:.2f} m²"
                ).add_to(m)

                # Plot Marker
                for i, row in df.iterrows():
                    folium.CircleMarker(
                        location=[row['lat_wgs84'], row['lon_wgs84']],
                        radius=4, color="red", fill=True, popup=f"STN: {i+1}"
                    ).add_to(m)

                m.fit_bounds(coords_poly)
                st_folium(m, width=1000, height=500, key="map")

                # Bahagian Data
                st.write("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 📋 Data (WGS84)")
                    st.dataframe(df[['STN', 'lat_wgs84', 'lon_wgs84']])
                    st.metric("Luas (m²)", f"{area:.3f}")
                with col2:
                    st.write("### 📐 Pelan Teknikal")
                    fig, ax = plt.subplots()
                    ax.plot(df['E'].tolist()+[df['E'][0]], df['N'].tolist()+[df['N'][0]], 'b-o')
                    ax.set_aspect('equal')
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"Ralat penukaran: {e}")
        else:
            st.error("Pastikan CSV ada kolum E dan N!")
    else:
        st.info("Sila muat naik CSV dan pilih negeri untuk melihat lot di atas satelit.")
