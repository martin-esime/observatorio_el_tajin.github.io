import drms, os, pandas as pd
from datetime import datetime
import numpy as np

# CONFIG TAJIN
EMAIL = 'tu_email@tajin.mx' # cambia por tu email JSOC registrado
HARP = 13792 # HARP de AR 4549, cambia si nace otra
CSV = "historial_vivo.csv"

c = drms.Client(email=EMAIL)
# baja el SHARP mas reciente con AREA
q = c.query(f'hmi.sharp_cea_720s[{HARP}][2026/1d@720s]', key=['T_REC','AREA_ACR','USFLUX'])
print(q.tail())
area = float(q['AREA_ACR'].iloc[-1]) # ya viene en MSH real, sin contar pixeles
# fallback si AREA_ACR es 0
if area < 10:
    area = float(q['AREA'].iloc[-1]) if 'AREA' in q else 500

# --- TU MISMA LOGICA ABAS, no se toca CSV ---
fecha = datetime.utcnow().strftime("%d-%m-%Y")
utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
dt = 0.5/24.0

if os.path.exists(CSV) and os.path.getsize(CSV)>60:
    old = pd.read_csv(CSV)
    area_prev = int(old["Arkansas"].iloc[-1])
    dAdt = (area - area_prev)/0.5
    A_acum = float(old["A_acum_MSHdia"].iloc[-1]) + area*dt
else:
    dAdt = 0
    A_acum = 410 + area
    old = None

C370, C510, C890 = A_acum/370, A_acum/510, A_acum/890
if C890>=1: pM,pX,txt=85,45,"SUPER-X INMINENTE 6H - cruzo 890"
elif C510>=1: pM,pX,txt=45,10,"Alerta M en 12h - cruzo 510"
elif C370>=1: pM,pX,txt=20,2,"Cruzo 370 - C fuerte"
else: pM,pX,txt=5,0,f"Faltan {370-A_acum:.0f} para 370"
if dAdt>15: pM=min(90,pM+15); pX=min(60,pX+15); txt+=f" | EMERGENCIA dA/dt={dAdt:.1f}"

print(f"JSOC SHARP {HARP}: area={area:.1f} A_acum={A_acum:.1f} dAdt={dAdt:.1f}")

row = {"identificacion":"AR4549","Arkansas":int(area),"fecha":fecha,"A_acum_MSHdia":round(A_acum,2),
"C_t_370":round(C370,3),"C_t_510":round(C510,3),"C_t_890":round(C890,3),
"dAdt_MSH_h":round(dAdt,2),"prob_M_6h":pM,"prob_X_6h":pX,"prediccion":txt,"pred_Tau_UTC":utc,"acierto":"VIVO_JSOC_SHARP"}

df = pd.DataFrame([row])
if old is not None and len(old)>0:
    pd.concat([old,df]).to_csv(CSV, index=False)
else:
    df.to_csv(CSV, index=False)

pd.read_csv(CSV).tail(30).to_csv("tabla_30.csv", index=False)
