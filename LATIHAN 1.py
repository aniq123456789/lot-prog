import math
import numpy as np
import ezdxf  # Library untuk eksport AutoCAD

# ==========================
# DATA ASAL (DARI KOD ANDA)
# ==========================
LOT_NO = "11487"
AREA_VAL = "247 m²"
start_northing = 6736.912
start_easting = 115597.566

data = [
    (119 + 8/60, 13.648),
    (197 + 30/60, 12.544),
    (248 + 19/60, 5.777),
    (299 + 8/60, 12.528),
    (29 + 8/60, 16.764),
]

def bearing_to_xy(bearing_deg, distance):
    rad = math.radians(bearing_deg)
    return distance * math.sin(rad), distance * math.cos(rad)

# Bina koordinat relatif
points_rel = [(0, 0)]
x, y = 0, 0
for b, d in data:
    dx, dy = bearing_to_xy(b, d)
    x += dx
    y += dy
    points_rel.append((x, y))

points_rel = np.array(points_rel)

# Penyelarasan Datum
offset_x = start_easting - points_rel[3][0]
offset_y = start_northing - points_rel[3][1]
points = points_rel + [offset_x, offset_y]

# ==========================================
# FUNGSI EKSPORT KE AUTOCAD (DXF)
# ==========================================
def export_to_autocad(filename, coords, lot_no, area, sides_data):
    # 1. Cipta dokumen DXF baru (Versi R2010 untuk kompatibiliti tinggi)
    doc = ezdxf.new('R2010', setup=True)
    msp = doc.modelspace()

    # 2. Cipta Layer (Warna 7 = Putih/Hitam, Warna 1 = Merah, Warna 3 = Hijau)
    doc.layers.new('SEMPADAN', dxfattribs={'color': 7, 'lineweight': 35})
    doc.layers.new('TEKS_LOT', dxfattribs={'color': 2})
    doc.layers.new('TEKS_SISI', dxfattribs={'color': 3})

    # 3. Lukis Sempadan Lot (LWPolyline)
    # Ambil titik kecuali yang terakhir untuk elak pertindihan koordinat mula/tamat
    boundary = coords[:-1]
    msp.add_lwpolyline(boundary, close=True, dxfattribs={'layer': 'SEMPADAN'})

    # 4. Tambah No Lot & Luas di tengah
    cx, cy = boundary.mean(axis=0)
    msp.add_text(f"LOT {lot_no}", 
                 dxfattribs={'layer': 'TEKS_LOT', 'height': 0.8}
                ).set_placement((cx, cy + 0.4), align=ezdxf.constants.MTEXT_CENTER)
    
    msp.add_text(area, 
                 dxfattribs={'layer': 'TEKS_LOT', 'height': 0.6}
                ).set_placement((cx, cy - 0.4), align=ezdxf.constants.MTEXT_CENTER)

    # 5. Tambah Bearing & Jarak pada setiap sisi
    for i in range(len(sides_data)):
        p1, p2 = coords[i], coords[i+1]
        mx, my = (p1[0] + p2[0])/2, (p1[1] + p2[1])/2
        
        # Kira sudut untuk rotasi teks selari dengan garisan
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        
        # Normalisasi sudut supaya teks tidak terbalik
        if angle > 90: angle -= 180
        elif angle < -90: angle += 180

        b_val, d_val = sides_data[i]
        deg = int(b_val)
        minute = int((b_val - deg) * 60)
        label = f"{deg}%%d{minute:02d}'00\"   {d_val:.3f}m" # %%d adalah simbol darjah dalam AutoCAD

        # Tambah teks dengan offset sedikit dari garisan
        msp.add_text(label, 
                     dxfattribs={'layer': 'TEKS_SISI', 'height': 0.4, 'rotation': angle}
                    ).set_placement((mx, my + 0.2), align=ezdxf.constants.MTEXT_CENTER)

    # 6. Simpan fail
    doc.saveas(filename)
    print(f"Sukses! Fail '{filename}' telah dicipta.")

# Jalankan fungsi eksport
export_to_autocad(f"Lot_{LOT_NO}.dxf", points, LOT_NO, AREA_VAL, data)
