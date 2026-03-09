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

if login():
    if st.sidebar.button("Log Keluar"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title("Sistem Visualisasi Lot & Satelit Google")

    st.sidebar.header("Muat Naik Data")
    uploaded_file = st.sidebar.file_uploader("Pilih fail CSV anda", type="csv")

    # Nilai default
    df = None
    area = 0
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            df['E'] = pd.to_numeric(df['E'])
            df['N'] = pd.to_numeric(df['N'])
            
            # --- PENGESAHAN KOORDINAT ---
            # Jika nilai > 500, ia mungkin meter (RSO/Cassini). 
            # Google Folium perlukan Lat/Lon (contoh: 3.123, 101.123)
            is_meter = df['E'].iloc[0] > 500 
            
            # Kira Luas (Formula Shoelace)
            e = df['E'].values
            n = df['N'].values
            area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))

            # Pusat Peta
            center_lat = df['N'].mean()
            center_lon = df['E'].mean()

            st.write("### 🌍 Pandangan Satelit Google")

            # Bina Peta
            m = folium.Map(
                location=[center_lat, center_lon], 
                zoom_start=19, 
                max_zoom=22
            )

            # Tambah Google Satellite Layer
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google Satellite',
                name='Google Satellite',
                max_zoom=22,
                overlay=False
            ).add_to(m)

            # Plot Poligon
            coords_poly = [[row['N'], row['E']] for i, row in df.iterrows()]
            folium.Polygon(
                locations=coords_poly,
                color="yellow",
                weight=4,
                fill=True,
                fill_color="yellow",
                fill_opacity=0.4,
                popup=f"Luas: {area:.2f} m²"
            ).add_to(m)

            # Plot Marker
            for i, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['N'], row['E']],
                    radius=5,
                    color="red",
                    fill=True,
                    fill_color="white",
                    popup=f"STN: {i+1}"
                ).add_to(m)

            # Paparkan Peta
            # fit_bounds memastikan peta zoom automatik ke poligon
            m.fit_bounds(coords_poly)
            st_folium(m, width=1000, height=600, key="map_updated")

            # Paparan Teknikal
            st.write("---")
            col1, col2 = st.columns(2)
            with col1:
                st.write("### 📋 Data")
                st.dataframe(df)
                st.metric("Luas Keseluruhan", f"{area:.3f} m²")
            with col2:
                st.write("### 📐 Pelan")
                fig, ax = plt.subplots()
                e_p = df['E'].tolist() + [df['E'][0]]
                n_p = df['N'].tolist() + [df['N'][0]]
                ax.plot(e_p, n_p, 'y-o', linewidth=2)
                ax.fill(e_p, n_p, color='yellow', alpha=0.3)
                ax.set_aspect('equal')
                st.pyplot(fig)
        else:
            st.error("Fail CSV mesti mempunyai kolum 'E' dan 'N'!")
    else:
        st.info("Sila muat naik fail CSV untuk melihat data di atas satelit.")
