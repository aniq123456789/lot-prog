# ================== KEMASKINI LOGIK PEMETAAN (MAX ZOOM) ==================

# ... kod sedia ada ...

            # Konfigurasi Folium dengan Max Zoom yang lebih tinggi
            tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Google Satellite" else 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            
            # Tambah parameter max_zoom=22 dan control_scale=True
            m = folium.Map(
                location=[df['lat'].mean(), df['lon'].mean()], 
                zoom_start=19, 
                tiles=tiles, 
                attr='Google',
                max_zoom=22,         # Membolehkan zoom lebih dekat
                control_scale=True   # Menambah bar skala untuk rujukan jarak
            )

# ... sambung kod seterusnya ...
