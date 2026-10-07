import requests, io, re, os
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime

# 1. AREA EN VIVO SDO
url_cont = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"
area_hoy_vivo = None

try:
    r = requests.get(url_cont, timeout=20)
    img = Image.open(io.BytesIO(r.content)).convert("L")
    arr = np.array(img)
    h, w = arr.shape
    x1, y1 = int(w*0.35), int(h*0.35)
    x2, y2 = int(w*0.70), int(h*0.70)
    roi = arr[y1:y2, x1:x2]
    dark_pixels = np.sum(roi < 90)
    area_hoy_vivo = int(dark_pixels * 0.55)
    area_hoy_vivo = max(100, min(area_hoy_vivo, 2000))
    print(f"VIVO SDO: {area_hoy_vivo} MSH")
except Exception as e:
    print(f"Fallo SDO {e}, respaldo SRS")
    try:
        txt = requests.get("https://services.swpc.noaa.gov/text/srs.txt", timeout=10).text
        for line in txt.splitlines():
            if line.strip().startswith("4549"):
                nums = re.findall(r"\d+", line)
                if nums: area_hoy_vivo = int(nums[-1])
    except: pass
    if area_hoy_vivo is None: area_hoy_vivo = 650

# 2. CALCULA TUS PARAMETROS
fecha_hoy = datetime.utcnow().strftime("%d-%m-%Y")
hora_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
A_acum = 410 + area_hoy_vivo
C_t = round(A_acum / 267.0, 3)

# 3. dA/dt y PREDICCION REAL M/X
dAdt = 0
prob_M = 0
prob_X = 0
pred_text = ""

try:
    if os.path.exists("tabla_30.csv"):
        df_old = pd.read_csv("tabla_30.csv")
        area_prev = int(df_old["Arkansas"].iloc[-1])
        dAdt = (area_hoy_vivo - area_prev) / 0.5  # cada 30 min
except:
    dAdt = 0

# Logica de prediccion
if C_t < 1.38: # <370
    prob_M = 5
    prob_X = 0
    horas = (370 - A_acum) / max(dAdt, 1) if dAdt>0 else 99
    pred_text = f"Tranquilo - Faltan {horas:.1f}h para Ac=370"
elif C_t < 1.91: # 370-510
    prob_M = 20
    pred_text = "Alerta leve - posible C fuerte"
elif C_t < 3.33: # 510-890
    prob_M = 45
    prob_X = 10
    pred_text = "Alerta M en 12h"
elif C_t >= 3.33: # >890 ya superado
    prob_M = 85
    prob_X = 45
    pred_text = "FLARE M/X INMINENTE 6H - C(t) supero 890"

if dAdt > 15:
    prob_M = min(90, prob_M + 15)
    prob_X = min(60, prob_X + 15)
    pred_text += f" | EMERGENCIA RAPIDA dA/dt={dAdt:.1f} MSH/h"

print(f"PRED: M={prob_M}% X={prob_X}% | {pred_text}")

# 4. GUARDA TABLA
df = pd.DataFrame([{
    "identificacion": "AR4549",
    "Arkansas": area_hoy_vivo,
    "fecha": fecha_hoy,
    "area": A_acum,
    "Connecticut": C_t,
    "dAdt_MSH_h": round(dAdt,2),
    "prob_M_6h": prob_M,
    "prob_X_6h": prob_X,
    "prediccion": pred_text,
    "pred_Tau_UTC": hora_utc,
    "bengala_real": "",
    "Tau_real_UTC": "",
    "error_min": "",
    "acierto": "VIVO_SDO_PRED"
}])
df.to_csv("tabla_30.csv", index=False)

# Guarda historial para dA/dt
if os.path.exists("historial_vivo.csv"):
    df_hist = pd.read_csv("historial_vivo.csv")
    df_hist = pd.concat([df_hist, df], ignore_index=True)
else:
    df_hist = df
df_hist.to_csv("historial_vivo.csv", index=False)
