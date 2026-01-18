import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta, time
import calendar
import urllib.parse

# --- 1. CONFIGURACIÓN VISUAL (TU ESTÉTICA ORIGINAL) ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png"
)

st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; font-family: 'Arial'; }
    .card-auto { 
        border: 2px solid #D4AF37; padding: 20px; border-radius: 20px; 
        background-color: #111111; text-align: center; margin-bottom: 25px;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.2);
    }
    .stButton>button { 
        background-color: #D4AF37; color: black; border-radius: 10px; 
        font-weight: bold; width: 100%; border: none;
    }
    .occupied { 
        background-color: #ff385c; color: white; border-radius: 50%; 
        width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; 
        margin: auto; font-weight: bold;
    }
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a; border-radius: 10px 10px 0 0; color: white; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        # Intento de conexión usando los secretos de Streamlit
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("LISTA ALQUILERES DE VEHICULOS-")
    except Exception as e:
        return None

def obtener_datos_cloud():
    sh = conectar_google_sheets()
    if sh:
        try:
            worksheet = sh.worksheet("reservas")
            df = pd.DataFrame(worksheet.get_all_records())
            if not df.empty:
                df.columns = [str(c).strip().upper() for c in df.columns]
                # Detectar columnas críticas
                col_ini = next((c for c in df.columns if 'SALIDA' in c), None)
                col_fin = next((c for c in df.columns if 'ENTREGA' in c), None)
                col_auto = next((c for c in df.columns if 'AUTO' in c), None)
                
                df['FECHA_INICIO'] = pd.to_datetime(df[col_ini], dayfirst=True, errors='coerce')
                df['FECHA_FIN'] = pd.to_datetime(df[col_fin], dayfirst=True, errors='coerce')
                df['AUTO_BUSQUEDA'] = df[col_auto].str.upper().str.strip()
                return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 3. BASE DE DATOS LOCAL (FLOTA Y MANTENIMIENTO) ---
DB_NAME = 'jm_sistema_completo.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, placa TEXT, 
                color TEXT, km_actual INTEGER, km_cambio INTEGER, 
                venc_seguro DATE, cuota_venc DATE, estado TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    
    autos = [
        ("HYUNDAI TUCSON BLANCO", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "AAVI502", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ BLANCO", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "AAVP719", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ NEGRO", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "AAOR725", "Negro", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VOXY GRIS", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "AAUG465", "Gris", 0, 5000, "2026-12-31", "2026-02-10", "Disponible")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 4. INTERFAZ PRINCIPAL ---
st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=250)
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)

t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

# --- PESTAÑA RESERVAS ---
with t_res:
    df_cloud = obtener_datos_cloud()
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    
    col1, col2 = st.columns(2)
    for i, (_, car) in enumerate(flota.iterrows()):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
                <div class="card-auto">
                    <h3>{car['nombre']}</h3>
                    <img src="{car['img']}" width="100%">
                    <p style="font-size:22px; color:#D4AF37; font-weight:bold;">R$ {car['precio']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📅 VER DISPONIBILIDAD"):
                # Calendario Visual
                ocupadas = set()
                if not df_cloud.empty:
                    # Filtramos las reservas del Excel para este auto
                    df_res = df_cloud[df_cloud['AUTO_BUSQUEDA'] == car['nombre']]
                    for _, r in df_res.iterrows():
                        if pd.notnull(r['FECHA_INICIO']) and pd.notnull(r['FECHA_FIN']):
                            delta = (r['FECHA_FIN'].date() - r['FECHA_INICIO'].date()).days + 1
                            for d in range(delta):
                                ocupadas.add(r['FECHA_INICIO'].date() + timedelta(days=d))
                
                # Mostrar el mes actual
                hoy = date.today()
                cal = calendar.monthcalendar(hoy.year, hoy.month)
                st.write(f"**{calendar.month_name[hoy.month]} {hoy.year}** (Rojo = Ocupado)")
                
                for week in cal:
                    cols = st.columns(7)
                    for d_idx, day in enumerate(week):
                        if day == 0: cols[d_idx].write("")
                        else:
                            fecha_celda = date(hoy.year, hoy.month, day)
                            if fecha_celda in ocupadas:
                                cols[d_idx].markdown(f'<div class="occupied">{day}</div>', unsafe_allow_html=True)
                            else:
                                cols[d_idx].write(day)
                
                st.divider()
                f_i = st.date_input("Inicio", key=f"ini{i}")
                f_f = st.date_input("Fin", key=f"fin{i}")
                if st.button("RESERVAR POR WHATSAPP", key=f"btn{i}"):
                    texto = f"Hola JM! Quiero reservar el {car['nombre']} del {f_i} al {f_f}"
                    url = f"https://wa.me/595983515320?text={urllib.parse.quote(texto)}"
                    st.markdown(f'<a href="{url}" target="_blank">Click aquí para enviar WhatsApp</a>', unsafe_allow_html=True)

# --- PESTAÑA UBICACIÓN ---
with t_ubi:
    st.markdown("### Nuestra Ubicación")
    st.markdown('<iframe src="http://googleusercontent.com/maps.google.com/7" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

# --- PESTAÑA ADMINISTRADOR ---
with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        # 1. Buscador de Clientes
        st.subheader("🔍 BUSCADOR DE CLIENTES (Desde Google Sheets)")
        if not df_cloud.empty:
            busqueda = st.text_input("Escribe nombre o placa...")
            if busqueda:
                df_cloud = df_cloud[df_cloud.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            st.dataframe(df_cloud, use_container_width=True)
        else:
            st.error("⚠️ No se pudo conectar con el Excel. Revisa tus 'Secrets'.")

        # 2. Gestión de Flota y Alertas
        st.divider()
        st.subheader("🛠️ GESTIÓN DE MANTENIMIENTO")
        conn = sqlite3.connect(DB_NAME)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for idx, row in flota_adm.iterrows():
            with st.expander(f"🚗 {row['nombre']} ({row['placa']})"):
                c1, c2, c3 = st.columns(3)
                km_a = c1.number_input("KM Actual", value=row['km_actual'], key=f"kma{idx}")
                km_c = c2.number_input("Próximo Cambio", value=row['km_cambio'], key=f"kmc{idx}")
                v_s = c3.date_input("Venc. Seguro", value=pd.to_datetime(row['venc_seguro']).date(), key=f"vs{idx}")
                
                # Alertas visuales
                if km_a >= km_c: st.error("🚨 CAMBIO DE ACEITE NECESARIO")
                if (v_s - date.today()).days < 10: st.warning("🚨 SEGURO POR VENCER")

                if st.button("Guardar Cambios", key=f"sv{idx}"):
                    conn.execute("UPDATE flota SET km_actual=?, km_cambio=?, venc_seguro=? WHERE nombre=?", (km_a, km_c, v_s, row['nombre']))
                    conn.commit(); st.rerun()
        conn.close()
