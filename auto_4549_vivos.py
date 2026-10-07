# auto_4549_vivo.py - Observatorio El Tajin - AR4549 vivo + alerta a Chava
import os, smtplib, csv, requests
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIG ===
AR = "AR4549"
AREA_ACTUAL = 510  # esto luego lo lees de tu magnetograma real
PROB_M = 45
PROB_X = 10
PRED_TEXTO = "Alerta M en 12h"
TAU_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

CSV_FILE = "tabla_30.csv"

def actualiza_csv():
    with open(CSV_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region","area","prob_M_6h","prob_X_6h","prediccion","tau_utc","actualizado"])
        w.writerow([AR, AREA_ACTUAL, PROB_M, PROB_X, PRED_TEXTO, TAU_UTC, datetime.now().isoformat()])
    print(f"CSV actualizado: {AR} {AREA_ACTUAL} M:{PROB_M}%")

def alerta_correo_chava():
    user = os.getenv("zuleymacopal@gmail.com")
    pwd = os.getenv("tanchiwis")
    dest = os.getenv("salvador074@hotmail.com")
    
    if not user or not pwd or not dest:
        print("Faltan secrets, no se envia correo")
        return

    if PROB_M < 40 and PROB_X < 5:
        print("Sin riesgo, no se alerta a Chava")
        return

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = dest
    msg["Subject"] = f"[{AR}] Alerta vivo - M:{PROB_M}% X:{PROB_X}% - {PRED_TEXTO}"

    cuerpo = f"""Chava,

Reporte automatico Observatorio El Tajin:

Region: {AR}
Area: {AREA_ACTUAL}
Prob M 6h: {PROB_M}%
Prob X 6h: {PROB_X}%
Prediccion: {PRED_TEXTO}
Tau: {TAU_UTC}

CSV: tabla_30.csv actualizado.

Es automatico, nomas para que estes al tiro.

- Monitor vivo
"""
    msg.attach(MIMEText(cuerpo, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, pwd.replace(" ", ""))
        server.send_message(msg)
    print(f"Alerta enviada a Chava: {dest}")

if __name__ == "__main__":
    actualiza_csv()
    alerta_correo_chava()
