import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# Fungsi untuk tukar bearing decimal ke format DMS (Darjah, Minit, Saat)
def to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = int((deg - d - m/60) * 3600)
    return f"{d}°{m}'{s}\""

# Tajuk Aplikasi
st.title("Visualisasi Poligon Data Ukur")

uploaded_file = st.file_uploader("Pilih fail CSV anda", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    st.write("### Pratinjau Data:")
    st.dataframe(df)

    if 'E' in df.columns and 'N' in df.columns:
        # 1. Pengiraan LUAS (Shoelace Formula)
        e = df['E'].values
        n = df['N'].values
        area = 0.5 * np.abs(np.dot(e, np.roll(n, 1)) - np.dot(n, np.roll(e, 1)))

        # Koordinat untuk poligon tertutup (E, N)
        coords_list = []
        for i in range(len(df)):
            coords_list.append([df['E'][i], df['N'][i]])
        
        # Simpan list koordinat untuk poligon (perlu tutup balik ke titik asal)
        poly_coords = coords_list + [coords_list[0]]

        # Plotting
        e_plot = [c[0] for c in poly_coords]
        n_plot = [c[1] for c in poly_coords]

        fig, ax = plt.subplots(figsize=(12, 12))
        ax.plot(e_plot, n_plot, marker='o', linestyle='-', color='b', linewidth=2)
        ax.fill(e_plot, n_plot, alpha=0.1, color='skyblue') 
        
        center_e, center_n = np.mean(df['E']), np.mean(df['N'])

        # 2. Tambah Bearing (DMS) dan Jarak
        for i in range(len(df)):
            x1, y1 = df['E'][i], df['N'][i]
            next_idx = (i + 1) % len(df)
            x2, y2 = df['E'][next_idx], df['N'][next_idx]
            
            dist = np.sqrt((x2 - x1)*2 + (y2 - y1)*2)
            brg_rad = np.arctan2((x2 - x1), (y2 - y1))
            brg_deg = np.degrees(brg_rad) % 360
            dms_label = to_dms(brg_deg)
            
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            angle_rad = np.arctan2((y2 - y1), (x2 - x1))
            angle_deg = np.degrees(angle_rad)
            
            if angle_deg > 90 or angle_deg < -90:
                angle_deg -= 180

            label = f"{dms_label}\n{dist:.3f}m"
            ax.text(mid_x, mid_y, label, fontsize=9, color='darkred', 
                    ha='center', va='bottom', rotation=angle_deg, 
                    rotation_mode='anchor')

        ax.text(center_e, center_n, f"LUAS:\n{area:.3f} m²", 
                fontsize=14, fontweight='bold', ha='center', color='green',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='green'))

        # Label Stesen di LUAR
        if 'STN' in df.columns:
            for i, txt in enumerate(df['STN']):
                dx = df['E'][i] - center_e
                dy = df['N'][i] - center_n
                dist_center = np.sqrt(dx*2 + dy*2)
                if dist_center == 0: dist_center = 1
                offset_e, offset_n = (dx / dist_center) * 0.5, (dy / dist_center) * 0.5
                
                ax.text(df['E'][i] + offset_e, df['N'][i] + offset_n, 
                        f"STN {txt}", fontsize=9, fontweight='bold', 
                        color='blue', ha='center', va='center')

        ax.set_xlabel('Easting (E)')
        ax.set_ylabel('Northing (N)')
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, linestyle=':', alpha=0.5)

        st.write("### Visualisasi Poligon Terperinci:")
        st.pyplot(fig)
        
        col1, col2 = st.columns(2)
        col1.metric("Luas (Meter Persegi)", f"{area:.3f} m²")
        col2.metric("Luas (Ekar)", f"{area * 0.000247105:.4f} ac")

        # --- FUNGSI EXPORT KE QGIS DENGAN BATU SEMPADAN ---
        st.write("---")
        st.write("### 📥 Export Data untuk QGIS")
        
        features = []
        
        # A. Masukkan Poligon (Kawasan Tanah)
        features.append({
            "type": "Feature",
            "properties": {
                "Jenis": "Kawasan Poligon",
                "Luas_m2": round(area, 3),
                "Luas_Ekar": round(area * 0.000247105, 4)
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords]
            }
        })
        
        # B. Masukkan Setiap Stesen (Batu Sempadan)
        for i in range(len(df)):
            stn_name = str(df['STN'][i]) if 'STN' in df.columns else f"{i+1}"
            features.append({
                "type": "Feature",
                "properties": {
                    "Jenis": "Batu Sempadan",
                    "STN": stn_name,
                    "Easting": df['E'][i],
                    "Northing": df['N'][i]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [df['E'][i], df['N'][i]]
                }
            })
        
        # Bina GeoJSON Lengkap
        geojson_data = {
            "type": "FeatureCollection",
            "name": "Data_Ukur_Lengkap",
            "features": features
        }
        
        geojson_string = json.dumps(geojson_data)
        
        st.download_button(
            label="Download GeoJSON (Poligon + Batu Sempadan)",
            data=geojson_string,
            file_name="pelan_ukur_lengkap.geojson",
            mime="application/json",
            help="Muat turun fail ini untuk QGIS. Ia mengandungi bentuk poligon dan titik stesen."
        )

    else:
        st.error("Ralat: Kolum 'E' dan 'N' tidak ditemui.")