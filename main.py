import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta, time
import calendar
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ALQUILER DE VEHICULOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTÉTICA DORADA Y NEGRA ORIGINAL ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; font-family: 'Arial'; }
    .card-auto { 
        border: 2px solid #D4AF37; padding: 20px; border-radius: 20px; 
        background-color: #111111; text-align: center; margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.3);
    }
    .stButton>button { background-color: #D4AF37; color: black; font-weight: bold; border-radius: 10px; width: 100%; border: none; }
    .occupied { background-color: #ff4b4b; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; margin: auto; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1a1a; border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS ---
def obtener_datos_cloud():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Truco para corregir saltos de línea en la llave
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open("LISTA ALQUILERES DE VEHICULOS-")
        df = pd.DataFrame(sh.worksheet("reservas").get_all_records())
        
        if not df.empty:
            df.columns = [str(c).strip().upper() for c in df.columns]
            c_ini = next((c for c in df.columns if 'SALIDA' in c), None)
            c_fin = next((c for c in df.columns if 'ENTREGA' in c), None)
            df['DT_I'] = pd.to_datetime(df[c_ini], dayfirst=True, errors='coerce')
            df['DT_F'] = pd.to_datetime(df[c_fin], dayfirst=True, errors='coerce')
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# --- BASE DE DATOS LOCAL ---
DB_NAME = 'jm_permanente_2026.db'
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, placa TEXT, 
                color TEXT, km_actual INTEGER, km_cambio INTEGER, 
                venc_seguro DATE, cuota_venc DATE, estado TEXT)''')
    
    autos = [
        ("HYUNDAI TUCSON BLANCO", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "AAVI502", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ BLANCO", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "AAVP719", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ NEGRO", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "AAOR725", "Negro", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VOXY GRIS", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "AAUG465", "Gris", 0, 5000, "2026-12-31", "2026-02-10", "Disponible")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- INTERFAZ ---
st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=250)
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)

df_cloud, error_msg = obtener_datos_cloud()

tab1, tab2, tab3 = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with tab1:
    if error_msg: st.error(f"Error de conexión: {error_msg}")
    
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    col_a, col_b = st.columns(2)
    for i, (_, row) in enumerate(flota.iterrows()):
        with (col_a if i % 2 == 0 else col_b):
            st.markdown(f'<div class="card-auto"><h3>{row["nombre"]}</h3><img src="{row["img"]}" width="100%"><p style="font-size:24px; color:#D4AF37;">R$ {row["precio"]}</p></div>', unsafe_allow_html=True)
            with st.expander("📅 VER DISPONIBILIDAD"):
                ocupados = []
                if not df_cloud.empty:
                    # Filtro inteligente por nombre
                    df_v = df_cloud[df_cloud.astype(str).apply(lambda x: row['nombre'] in x.values, axis=1)]
                    for _, rv in df_v.iterrows():
                        if pd.notnull(rv['DT_I']):
                            for d in range((rv['DT_F'].date() - rv['DT_I'].date()).days + 1):
                                ocupados.append(rv['DT_I'].date() + timedelta(days=d))

                h = date.today()
                st.write(f"**{calendar.month_name[h.month]} {h.year}**")
                cal = calendar.monthcalendar(h.year, h.month)
                for week in cal:
                    cols = st.columns(7)
                    for idx, day in enumerate(week):
                        if day != 0:
                            f = date(h.year, h.month, day)
                            if f in ocupados: cols[idx].markdown(f'<div class="occupied">{day}</div>', unsafe_allow_html=True)
                            else: cols[idx].write(day)
                
                if st.button("RESERVAR ESTE AUTO", key=f"res{i}"):
                    txt = urllib.parse.quote(f"Hola JM! Deseo el {row['nombre']}")
                    st.markdown(f'<a href="https://wa.me/595983515320?text={txt}" target="_blank">📲 Enviar WhatsApp</a>', unsafe_allow_html=True)

with tab2:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d14402.135402506482!2d-54.6166164!3d-25.5205417!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ses!2spy!4v1710000000000" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

with tab3:
    if st.text_input("Contraseña Maestro", type="password") == "8899":
        st.subheader("🔍 BUSCADOR DE CONTRATOS (EXCEL)")
        if not df_cloud.empty:
            q = st.text_input("Buscar cliente...")
            if q: df_cloud = df_cloud[df_cloud.astype(str).apply(lambda x: q.upper() in x.str.upper().values, axis=1)]
            st.dataframe(df_cloud, use_container_width=True)
        
        st.divider()
        st.subheader("🛠️ MANTENIMIENTO Y SEGUROS")
        conn = sqlite3.connect(DB_NAME); f_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for idx, r in f_adm.iterrows():
            with st.expander(f"🚗 {r['nombre']} - {r['placa']}"):
                k1, k2, k3 = st.columns(3)
                km_a = k1.number_input("KM Actual", value=r['km_actual'], key=f"km{idx}")
                km_c = k2.number_input("Próx. Aceite", value=r['km_cambio'], key=f"kc{idx}")
                v_s = k3.date_input("Venc. Seguro", value=pd.to_datetime(r['venc_seguro']).date(), key=f"vs{idx}")
                
                if km_a >= km_c: st.error("🚨 CAMBIO DE ACEITE REQUERIDO")
                if st.button("Guardar Cambios", key=f"save{idx}"):
                    conn.execute("UPDATE flota SET km_actual=?, km_cambio=?, venc_seguro=? WHERE nombre=?", (km_a, km_c, v_s, r['nombre']))
                    conn.commit(); st.rerun()
        conn.close()
