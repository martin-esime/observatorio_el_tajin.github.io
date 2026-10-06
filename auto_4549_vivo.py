import requests, os, datetime
from fpdf import FPDF

DEPOSITION_ID = "23196054"
TOKEN = os.environ.get("ZENODO_TOKEN")
k = 0.0039
A_acum = 650
Ct = k * A_acum

print(f"C(t): {Ct:.3f} >= 2.5 - LISTO PARA PUBLICAR")

if Ct >= 2.5:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"AR4549 v3.1 Live - {datetime.datetime.utcnow()}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, f"Region AR4549 beta-gamma-delta\nC(t)={Ct:.3f}\nArea acumulada={A_acum}\nFlares M1.4+M1.8 Oct 6\nPrediccion Tau: Oct 7 02-06 UTC")
    pdf_path = "AR4549_v3.1_live.pdf"
    pdf.output(pdf_path)

    params = {"access_token": TOKEN}
    r = requests.post(f"https://zenodo.org/api/deposit/depositions/{DEPOSITION_ID}/actions/newversion", params=params)
    new_id = r.json()['links']['latest_draft'].split('/')[-1]
    print(f"Nueva version draft: {new_id}")

    with open(pdf_path, 'rb') as f:
        requests.post(f"https://zenodo.org/api/deposit/depositions/{new_id}/files", params=params, data={'name': pdf_path}, files={'file': f})
    
    r = requests.post(f"https://zenodo.org/api/deposit/depositions/{new_id}/actions/publish", params=params)
    print(f"PUBLICADO: {r.json().get('doi')}")
