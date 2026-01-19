import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta
import calendar
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ALQUILER DE VEHICULOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTÉTICA ORIGINAL (NEGRO Y DORADO) ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; font-family: 'Arial'; }
    .card-auto { 
        border: 2px solid #D4AF37; padding: 20px; border-radius: 20px; 
        background-color: #111111; text-align: center; margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.4);
    }
    .stButton>button { background-color: #D4AF37; color: black; font-weight: bold; border-radius: 10px; border: none; height: 45px; }
    .occupied { background-color: #ff4b4b; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; margin: auto; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1a1a; color: white; padding: 10px 25px; border-radius: 10px 10px 0 0; font-size: 16px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN DE SEGURIDAD (FUERZA BRUTA) ---
def conectar_google_sheets():
    try:
        # Intenta leer directamente de la raíz de secrets si no hay etiqueta
        cred_info = {k: v for k, v in st.secrets.items() if k != "gcp_service_account"}
        
        # Si existe la etiqueta, la prioriza
        if "gcp_service_account" in st.secrets:
            cred_info = dict(st.secrets["gcp_service_account"])
            
        cred_info["private_key"] = cred_info["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(cred_info, scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open("LISTA ALQUILERES DE VEHICULOS-")
        df = pd.DataFrame(sh.worksheet("reservas").get_all_records())
        
        if not df.empty:
            df.columns = [str(c).strip().upper() for c in df.columns]
            # Mapeo de columnas con nombres flexibles
            col_salida = next((c for c in df.columns if 'SALIDA' in c), None)
            col_entrega = next((c for c in df.columns if 'ENTREGA' in c), None)
            df['DT_INI'] = pd.to_datetime(df[col_salida], dayfirst=True, errors='coerce')
            df['DT_FIN'] = pd.to_datetime(df[col_entrega], dayfirst=True, errors='coerce')
        return df, None
    except Exception as e:
        return None, str(e)

# --- DB LOCAL PARA ADMIN ---
DB_NAME = 'jm_master_final.db'
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
    c.executemany("INSERT OR IGNORE INTO flota (nombre, precio, img, placa, km_actual, km_cambio, venc_seguro) VALUES (?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- INICIO APP ---
st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=250)
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)

df_cloud, error_msg = conectar_google_sheets()

tab1, tab2, tab3 = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with tab1:
    if error_msg: st.warning("⚠️ El Calendario se encuentra en modo Local (Sin conexión a Google Sheets)")
    
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    col_izq, col_der = st.columns(2)
    
    for i, (_, car) in enumerate(flota.iterrows()):
        with (col_izq if i % 2 == 0 else col_der):
            st.markdown(f'''<div class="card-auto">
                <h3>{car["nombre"]}</h3>
                <img src="{car["img"]}" width="100%">
                <p style="font-size:24px; color:#D4AF37; font-weight:bold;">R$ {car["precio"]}</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander("📅 DISPONIBILIDAD"):
                # Lógica de días ocupados
                dias_rojos = []
                if df_cloud is not None:
                    # Buscamos coincidencias por nombre de auto
                    df_auto = df_cloud[df_cloud.astype(str).apply(lambda x: car['nombre'].split()[0] in str(x).upper(), axis=1)]
                    for _, res in df_auto.iterrows():
                        if pd.notnull(res['DT_INI']):
                            delta = (res['DT_FIN'].date() - res['DT_INI'].date()).days + 1
                            for d in range(delta):
                                dias_rojos.append(res['DT_INI'].date() + timedelta(days=d))

                hoy = date.today()
                st.write(f"**{calendar.month_name[hoy.month]} {hoy.year}**")
                cal = calendar.monthcalendar(hoy.year, hoy.month)
                for week in cal:
                    wc = st.columns(7)
                    for idx, day in enumerate(week):
                        if day != 0:
                            f_actual = date(hoy.year, hoy.month, day)
                            if f_actual in dias_rojos: wc[idx].markdown(f'<div class="occupied">{day}</div>', unsafe_allow_html=True)
                            else: wc[idx].write(day)
                
                st.divider()
                if st.button("RESERVAR AHORA", key=f"btn{i}"):
                    txt = urllib.parse.quote(f"Hola JM! Quiero consultar el {car['nombre']}")
                    st.markdown(f'<a href="https://wa.me/595983515320?text={txt}" target="_blank">📲 Hablar por WhatsApp</a>', unsafe_allow_html=True)

with tab2:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d3601.216654955734!2d-54.6541667!3d-25.564444399999998!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2zMjXCsDMzJzUyLjAiUyA1NMKwMzknMTUuMCJX!5e0!3m2!1ses-419!2spy!4v1700000000000" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

with tab3:
    if st.text_input("Acceso Maestro", type="password") == "8899":
        # BUSCADOR
        st.subheader("🔍 BUSCADOR GLOBAL DE CLIENTES")
        if df_cloud is not None:
            busq = st.text_input("Escriba nombre, placa o fecha...")
            if busq:
                df_cloud = df_cloud[df_cloud.astype(str).apply(lambda x: busq.upper() in str(x).upper(), axis=1)]
            st.dataframe(df_cloud, use_container_width=True)
        
        st.divider()
        st.subheader("🛠️ CONTROL DE MANTENIMIENTO")
        conn = sqlite3.connect(DB_NAME); f_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for idx, r in f_adm.iterrows():
            with st.expander(f"🚗 {r['nombre']} ({r['placa']})"):
                c1, c2, c3 = st.columns(3)
                km_act = c1.number_input("KM Actual", value=r['km_actual'], key=f"ka{idx}")
                km_nxt = c2.number_input("Próx. Cambio", value=r['km_cambio'], key=f"kn{idx}")
                v_seg = c3.date_input("Venc. Seguro", value=pd.to_datetime(r['venc_seguro']).date(), key=f"vs{idx}")
                
                if km_act >= km_nxt: st.error("🚨 ¡CAMBIO DE ACEITE URGENTE!")
                if st.button("ACTUALIZAR DATOS", key=f"upd{idx}"):
                    conn.execute("UPDATE flota SET km_actual=?, km_cambio=?, venc_seguro=? WHERE nombre=?", (km_act, km_nxt, v_seg, r['nombre']))
                    conn.commit(); st.rerun()
        conn.close()
