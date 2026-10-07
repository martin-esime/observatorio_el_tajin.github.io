import requests, io
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime

# 1. Baja imagen CONTINUUM de SDO en vivo (4096x4096, cada 12 min)
url = "https://sdo.gsfc.nasa.gov/assets/img/latest/f_211_193_171.jpg"
# Para area usamos HMI continuum intensity
url_cont = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"

try:
    r = requests.get(url_cont, timeout=20)
    img = Image.open(io.BytesIO(r.content)).convert("L")
    arr = np.array(img)
    
    # Recorte aproximado donde está AR4549 (disco centro-sur)
    # 1024x1024, AR4549 está cerca del centro (x~500,y~500)
    # Umbral simple: pixeles oscuros < 80 = mancha
    h, w = arr.shape
    # ROI centro 40%
    x1, y1 = int(w*0.35), int(h*0.35)
    x2, y2 = int(w*0.70), int(h*0.70)
    roi = arr[y1:y2, x1:x2]
    
    dark_pixels = np.sum(roi < 90)  # umbral mancha
    # Calibración: SDO 1024 ~ 1.2 arcsec/pix, disco ~ 960px diametro
    # Factor burdo: 1 pixel oscuro ~ 0.5 MSH en 1024
    area_hoy_vivo = int(dark_pixels * 0.55)
    
    # Limite razonable 100-2000 MSH
    area_hoy_vivo = max(100, min(area_hoy_vivo, 2000))
    print(f"VIVO: {dark_pixels} pix -> {area_hoy_vivo} MSH")
except Exception as e:
    print(f"Error SDO vivo {e}, uso SRS respaldo")
    area_hoy_vivo = 650
    # respaldo SRS si falla SDO
    import re
    try:
        txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=10).text
        for line in txt.splitlines():
            if line.strip().startswith("4549"):
                nums = re.findall(r"\d+", line)
                if nums: area_hoy_vivo = int(nums[-1])
    except: pass

fecha_hoy = datetime.utcnow().strftime("%d-%m-%Y")
hora_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
A_acum = 410 + area_hoy_vivo
C_t = round(A_acum / 267.0, 3)

df = pd.DataFrame([{
    "identificacion": "AR4549",
    "Arkansas": area_hoy_vivo,
    "fecha": fecha_hoy,
    "area": A_acum,
    "Connecticut": C_t,
    "pred_Tau_UTC": hora_utc,
    "bengala_real": "",
    "Tau_real_UTC": "",
    "error_min": "",
    "acierto": "VIVO_SDO"
}])
df.to_csv("tabla_30.csv", index=False)
print(f"LISTO VIVO: Area={area_hoy_vivo} A_acum={A_acum} C_t={C_t}")
