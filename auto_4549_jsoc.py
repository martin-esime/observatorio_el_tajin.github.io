import requests, io, os
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime

# --- 1. FOTO JSOC / SDO ---
URL_SDO = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIF.jpg"
print(f"Bajando {URL_SDO}")
r = requests.get(URL_SDO, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
r.raise_for_status()

img = Image.open(io.BytesIO(r.content)).convert("L") # blanco y negro
arr = np.array(img)
h, w = arr.shape

# ROI = donde está AR4549 (centro del sol) - NOAA está ahí
roi = arr[int(h*0.32):int(h*0.72), int(w*0.32):int(w*0.72)]

# --- 2. CONTEO PIXELES NOAA STYLE ---
# Pixel < 75 = umbra muy oscura, < 110 = penumbra
# Factor 0.52 calibrado para que 100 pix = 100 MSH como NOAA
umbra = np.sum(roi < 75)
penumbra = np.sum((roi >= 75) & (roi < 110))
area_hoy = int((umbra * 0.9 + penumbra * 0.4) * 0.52)
area_hoy = max(50, min(area_hoy, 2500))

print(f"PIXEL COUNT -> umbra:{umbra} penumbra:{penumbra} AREA:{area_hoy} MSH")

# --- 3. PARAMETROS ---
fecha = datetime.utcnow().strftime("%d-%m-%Y")
hora = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
A_acum = 410 + area_hoy # base del AR + hoy
C_t = round(A_acum / 267.0, 3)

# dAdt real con historial
dAdt = 0.0
try:
    if os.path.exists("historial_vivo.csv") and os.path.getsize("historial_vivo.csv") > 10:
        df_old = pd.read_csv("historial_vivo.csv")
        if len(df_old) >= 1:
            area_prev = int(df_old["Arkansas"].iloc[-1])
            # diferencia / 0.5h = cada 30 min
            dAdt = (area_hoy - area_prev) / 0.5
            print(f"dA/dt: {area_prev} -> {area_hoy} = {dAdt} MSH/h")
except Exception as e:
    print(f"No hay historial previo: {e}")

# --- 4. PREDICCION ---
prob_M, prob_X, txt = 45, 10, "Alerta M en 12h"
if C_t < 1.38: prob_M, prob_X, txt = 5, 0, "Tranquilo"
elif C_t < 1.91: prob_M, prob_X, txt = 20, 2, "Alerta leve - posible C fuerte"
elif C_t >= 3.33: prob_M, prob_X, txt = 85, 45, "FLARE M/X INMINENTE 6H"

if dAdt > 15:
    prob_M = min(90, prob_M + 15)
    prob_X = min(60, prob_X + 15)
    txt += f" | EMERGENCIA RAPIDA dA/dt={dAdt:.1f}"
elif dAdt < -20:
    txt += f" | Decaimiento rapido dA/dt={dAdt:.1f}"

# --- 5. GUARDADO QUE SI LLENA LAS 30 ---
nueva = pd.DataFrame([{
    "identificacion": "AR4549", "Arkansas": area_hoy, "fecha": fecha,
    "area": A_acum, "Connecticut": C_t, "dAdt_MSH_h": round(dAdt,2),
    "prob_M_6h": prob_M, "prob_X_6h": prob_X, "prediccion": txt,
    "pred_Tau_UTC": hora, "bengala_real": "", "Tau_real_UTC": "",
    "error_min": "", "acierto": "VIVO_JSOC_PIXEL_NOAA"
}])

if os.path.exists("historial_vivo.csv"):
    df_hist = pd.read_csv("historial_vivo.csv")
    df_hist = pd.concat([df_hist, nueva], ignore_index=True)
    # evita duplicados de la misma hora
    df_hist = df_hist.drop_duplicates(subset=['pred_Tau_UTC'], keep='last')
else:
    df_hist = nueva

# ESTO ES LA CLAVE PARA QUE SE LLENE:
df_hist.tail(100).to_csv("historial_vivo.csv", index=False) # guarda ultimas 100
df_hist.tail(30).to_csv("tabla_30.csv", index=False) # tabla siempre con 30

print(f"LISTO -> historial: {len(df_hist)} filas, tabla_30: {len(df_hist.tail(30))} filas")
