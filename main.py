import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import calendar
import urllib.parse

# --- CONFIGURACIÓN JM ---
st.set_page_config(page_title="JM ALQUILER", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; }
    .card-auto { border: 2px solid #D4AF37; padding: 15px; border-radius: 15px; background-color: #111111; margin-bottom: 20px; }
    .occupied { background-color: #ff4b4b; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; margin: auto; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE ---
def conectar_google():
    try:
        # Busca la clave en el diccionario de secretos
        if "gcp_service_account" not in st.secrets:
            return None, "Clave 'gcp_service_account' no encontrada."
        
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open("LISTA ALQUILERES DE VEHICULOS-")
        df = pd.DataFrame(sh.worksheet("reservas").get_all_records())
        
        if not df.empty:
            df.columns = [str(c).strip().upper() for c in df.columns]
            # Mapeo de fechas flexible
            c_ini = next((c for c in df.columns if 'SALIDA' in c), None)
            c_fin = next((c for c in df.columns if 'ENTREGA' in c), None)
            df['DT_I'] = pd.to_datetime(df[c_ini], dayfirst=True, errors='coerce')
            df['DT_F'] = pd.to_datetime(df[c_fin], dayfirst=True, errors='coerce')
        return df, None
    except Exception as e:
        return None, str(e)

# --- BASE DE DATOS LOCAL ---
DB_NAME = 'jm_final_v4.db'
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, placa TEXT, 
                km_actual INTEGER, km_cambio INTEGER, venc_seguro DATE)''')
    
    autos = [
        ("HYUNDAI TUCSON BLANCO", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "AAVI502", 0, 5000, "2026-12-31"),
        ("TOYOTA VITZ BLANCO", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "AAVP719", 0, 5000, "2026-12-31"),
        ("TOYOTA VITZ NEGRO", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "AAOR725", 0, 5000, "2026-12-31"),
        ("TOYOTA VOXY GRIS", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "AAUG465", 0, 5000, "2026-12-31")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- HEADER ---
st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=200)
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)

df_cloud, err = conectar_google()

t1, t2, t3 = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMIN"])

with t1:
    if err: st.warning(f"⚠️ Nota: Calendario Offline ({err})")
    
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    col_a, col_b = st.columns(2)
    for i, (_, row) in enumerate(flota.iterrows()):
        with (col_a if i % 2 == 0 else col_b):
            st.markdown(f'<div class="card-auto"><h3>{row["nombre"]}</h3><img src="{row["img"]}" width="100%"><p style="font-size:22px; color:#D4AF37;">R$ {row["precio"]}</p></div>', unsafe_allow_html=True)
            with st.expander("📅 DISPONIBILIDAD"):
                # Mostrar días ocupados
                dias_ocupados = []
                if df_cloud is not None:
                    # Filtramos por nombre del vehículo
                    df_v = df_cloud[df_cloud.astype(str).apply(lambda x: row['nombre'].split()[0] in str(x).upper(), axis=1)]
                    for _, rv in df_v.iterrows():
                        if pd.notnull(rv['DT_I']):
                            for d in range((rv['DT_F'].date() - rv['DT_I'].date()).days + 1):
                                dias_ocupados.append(rv['DT_I'].date() + timedelta(days=d))

                h = date.today()
                cal = calendar.monthcalendar(h.year, h.month)
                for week in cal:
                    cols = st.columns(7)
                    for idx, day in enumerate(week):
                        if day != 0:
                            f = date(h.year, h.month, day)
                            if f in dias_ocupados: cols[idx].markdown(f'<div class="occupied">{day}</div>', unsafe_allow_html=True)
                            else: cols[idx].write(day)
                
                if st.button("COTIZAR", key=f"btn{i}"):
                    msg = urllib.parse.quote(f"Hola JM! Consulto disponibilidad de {row['nombre']}")
                    st.markdown(f'<a href="https://wa.me/595983515320?text={msg}" target="_blank">📲 WhatsApp</a>', unsafe_allow_html=True)

with t2:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=..." width="100%" height="400" style="border:2px solid #D4AF37; border-radius:10px;"></iframe>', unsafe_allow_html=True)

with t3:
    if st.text_input("Clave", type="password") == "8899":
        st.subheader("🔍 BUSCADOR DE CONTRATOS")
        if df_cloud is not None:
            q = st.text_input("Buscar cliente...")
            if q: df_cloud = df_cloud[df_cloud.astype(str).apply(lambda x: q.upper() in str(x).upper(), axis=1)]
            st.dataframe(df_cloud, use_container_width=True)
        
        st.divider()
        st.subheader("🛠️ MANTENIMIENTO")
        conn = sqlite3.connect(DB_NAME); f_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for idx, r in f_adm.iterrows():
            with st.expander(f"🚗 {r['nombre']} ({r['placa']})"):
                c1, c2 = st.columns(2)
                km_a = c1.number_input("KM Actual", value=r['km_actual'], key=f"km{idx}")
                v_s = c2.date_input("Seguro Vence", value=pd.to_datetime(r['venc_seguro']).date(), key=f"vs{idx}")
                if st.button("Guardar", key=f"sv{idx}"):
                    conn.execute("UPDATE flota SET km_actual=?, venc_seguro=? WHERE nombre=?", (km_a, v_s, r['nombre']))
                    conn.commit(); st.rerun()
        conn.close()
