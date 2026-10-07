import requests, os, datetime, glob
import numpy as np
from astropy.io import fits
from fpdf import FPDF

DEPOSITION_ID = "23196054"
TOKEN = os.environ.get("ZENODO_TOKEN")
k = 0.0039

# --- TU CALCULO PIXEL X PIXEL ---
area_pixel_Mm2 = 0.36 * 0.36 # HMI CEA
MSH = 3.04 # 1 MSH = 3.04 Mm2

# Busca el ultimo Bz.fits de AR4549 que baja tu cron
archivo = sorted(glob.glob("*4549*Bz.fits"))[-1] if glob.glob("*4549*Bz.fits") else []
if not archivo:
    archivo = sorted(glob.glob("hmi.sharp_cea_720s.*Bz.fits"))[-1]

Bz = fits.getdata(archivo, ext=1)
mask = np.abs(Bz) > 500 # tu umbral
pixeles = np.sum(mask)
area_Mm2 = pixeles * area_pixel_Mm2
area_hoy = area_Mm2 / MSH # MSH reales del magnetograma

# Acumulada de tabla_30.csv
import pandas as pd
try:
    df = pd.read_csv("tabla_30.csv")
    A_acum = df["area_acumulada"].iloc[-1] + area_hoy
except:
    A_acum = area_hoy

Ct = k * A_acum
print(f"Pixel count: {pixeles} Area hoy: {area_hoy:.1f} MSH A_acum: {A_acum:.1f} C(t)={Ct:.3f}")

# --- PUBLICACION ---
if Ct >= 2.5:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,f"AR4549 v4.0 Live Magnetograma - {datetime.datetime.utcnow()}",ln=True)
    pdf.set_font("Arial","",11)
    pdf.multi_cell(0,7,f"Region AR4549 beta-gamma-delta\nArchivo: {archivo}\nPixeles >500G: {pixeles}\nArea hoy={area_hoy:.1f} MSH\nArea acumulada={A_acum:.1f}\nC(t)={Ct:.3f}\nFlares M1.4+M1.8 Oct 6\nFormula: t=(Acrit-Aactual)/(dA/dt)")
    pdf_path = f"AR4549_v4.0_mag_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
    pdf.output(pdf_path)

    params = {"access_token": TOKEN}
    r = requests.post(f"https://zenodo.org/api/deposit/depositions/{DEPOSITION_ID}/actions/newversion", params=params)
    new_id = r.json()['links']['latest_draft'].split('/')[-1]
    with open(pdf_path,'rb') as f:
        requests.post(f"https://zenodo.org/api/deposit/depositions/{new_id}/files", params=params, data={'name': pdf_path}, files={'file': f})
    r = requests.post(f"https://zenodo.org/api/deposit/depositions/{new_id}/actions/publish", params=params)
    print(f"PUBLICADO: {r.json().get('doi')}")
