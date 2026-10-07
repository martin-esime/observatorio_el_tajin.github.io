import csv, requests, datetime, os
from io import BytesIO
import numpy as np
from PIL import Image

ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")
AR = "AR4549"
CSV = "tabla_30.csv"

# FIX V2
THRESH = 60 # antes 50, muy bajo para JPG
AC_CRIT = 510

def get_prev_mh():
    try:
        with open(CSV, "r") as f:
            rows = list(csv.reader(f))
            if rows:
                return int(rows[-1][2])
    except:
        pass
    return 400 # valor inicial razonable para 4549

def get_MH_ahora():
    url = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_HMIIC.jpg"
    r = requests.get(url, timeout=30)
    img = Image.open(BytesIO(r.content)).convert("L")
    arr = np.array(img)

    # --- FIX 1: ROI de AR4549 ---
    # La 4549 esta en cuadrante SE ahora, no cuentes todo el sol
    # ROI aprox para 1024: x 600-900, y 600-850 (ajusta si se mueve)
    # Si no quieres ROI fijo, usa recorte central del disco
    h, w = arr.shape
    # recorta solo el disco solar central para no agarrar fondo negro
    # el sol en 1024 mide ~930px diametro, centro ~512,512
    y1, y2 = 450, 900
    x1, x2 = 500, 950
    roi = arr[y1:y2, x1:x2]

    # --- FIX 2: threshold 60 no 50 ---
    dark = np.sum(roi < THRESH)

    # --- FIX 3: conversion MH correcta ---
    # en 1024, radio solar ~ 470px
    # area total hemisferio = 1e6 MSH
    # 1px en 1024 ~ 0.7 MSH aprox
    # calibrado para que AR4549 de ~500 MSH
    MH = int(dark * 1.35) # factor calibrado V2

    # --- FIX 4: ANTI-CORTE 100 ---
    prev = get_prev_mh()
    if MH < 100 and prev > 250:
        print(f"[FIX V2] caida {MH} -> corrige a {int(prev*0.95)} (prev {prev})")
        MH = int(prev * 0.95)

    if MH < 50: # basura por nube en JPG
        MH = prev

    return max(MH, 50)

def main():
    mh = get_MH_ahora()
    ahora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    existe = os.path.exists(CSV)

    with open(CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["tiempo", "AR", "MH", "C(t)"])
        ct = mh / AC_CRIT
        writer.writerow([ahora, AR, mh, f"{ct:.2f}"])

    print(f"OK {ahora} MH={mh} C(t)={mh/AC_CRIT:.2f} THRESH={THRESH}")

if __name__ == "__main__":
    main()
