import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- FUNCIONES GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("LISTA ALQUILERES DE VEHICULOS-")
        return spreadsheet
    except Exception as e:
        st.error(f"Error de conexión con Google: {e}")
        return None

def obtener_datos_cloud():
    try:
        sh = conectar_google_sheets()
        if not sh: return pd.DataFrame()
        worksheet = sh.worksheet("reservas")
        df = pd.DataFrame(worksheet.get_all_records())
        
        if not df.empty:
            # Normalizar nombres de columnas (quitar espacios y poner mayúsculas)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Mapeo de columnas corregido
            col_salida = 'SALIDA' if 'SALIDA' in df.columns else (df.columns[5] if len(df.columns) > 5 else None)
            col_entrega = 'ENTREGA' if 'ENTREGA' in df.columns else (df.columns[6] if len(df.columns) > 6 else None)
            col_auto = 'AUTO' if 'AUTO' in df.columns else (df.columns[4] if len(df.columns) > 4 else None)
            col_total = 'TOTAL' if 'TOTAL' in df.columns else (df.columns[7] if len(df.columns) > 7 else None)

            df['inicio'] = pd.to_datetime(df[col_salida], errors='coerce') if col_salida else None
            df['fin'] = pd.to_datetime(df[col_entrega], errors='coerce') if col_entrega else None
            df['auto_excel'] = df[col_auto].str.upper().str.strip() if col_auto else ""
            df['TOTAL_NUM'] = pd.to_numeric(df[col_total], errors='coerce').fillna(0) if col_total else 0
            
        return df
    except Exception as e:
        st.warning(f"Aviso: No se pudieron leer datos del Excel. {e}")
        return pd.DataFrame()

# --- BASE DE DATOS LOCAL ---
DB_NAME = 'jm_corporativo_v3.db' # Cambiamos nombre para forzar nueva estructura limpia

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    
    # Crear tabla con todas las columnas desde el inicio
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, 
                placa TEXT, color TEXT, km_actual INTEGER, km_cambio INTEGER, 
                venc_seguro DATE, cuota_venc DATE)''')

    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris", 0, 5000, "2026-12-31", "2026-02-10")
    ]
    
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        return round(requests.get("https://open.er-api.com/v6/latest/BRL").json()['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()

def obtener_fechas_ocupadas_unificado(nombre_auto_app):
    df = obtener_datos_cloud()
    bloqueadas = set()
    if df.empty: return bloqueadas
    busqueda = nombre_auto_app.upper()
    if "VOXY" in busqueda: busqueda = "VOXY GRIS"
    elif "VITZ NEGRO" in busqueda: busqueda = "VITZ NEGRO"
    elif "VITZ BLANCO" in busqueda: busqueda = "VITZ BLANCO"
    elif "TUCSON" in busqueda: busqueda = "HYUNDAI TUCSON BLANCO"
    
    if 'auto_excel' in df.columns:
        df_auto = df[df['auto_excel'] == busqueda]
        for _, row in df_auto.iterrows():
            if pd.notnull(row['inicio']) and pd.notnull(row['fin']):
                for i in range((row['fin'].date() - row['inicio'].date()).days + 1):
                    bloqueadas.add(row['inicio'].date() + timedelta(days=i))
    return bloqueadas

# --- INTERFAZ ---
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p>R$ {v["precio"]} / Gs. {v["precio"]*COTIZACION_DIA:,.0f}</p></div>''', unsafe_allow_html=True)
            with st.expander("Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas_unificado(v['nombre'])
                # (Aquí va tu código de calendario que ya funciona...)
                st.write(f"Fechas ocupadas: {len(ocupadas)}")

with t_adm:
    if st.text_input("Clave Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = obtener_datos_cloud()
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.subheader("📋 CONTRATOS EN EXCEL")
        busqueda = st.text_input("🔍 Buscar Cliente")
        if not res_df.empty:
            if busqueda: res_df = res_df[res_df['NOMBRE'].str.contains(busqueda, case=False, na=False)]
            st.dataframe(res_df, use_container_width=True)
        else:
            st.info("No se encontraron filas en la pestaña 'reservas'. Verifica que el Excel tenga datos.")

        st.divider()
        st.subheader("🛠️ MANTENIMIENTO Y SEGUROS")
        for idx, row in flota_adm.iterrows():
            with st.expander(f"🚗 {row['nombre']}"):
                c1, c2, c3 = st.columns(3)
                km_act = c1.number_input("KM Actual", value=int(row['km_actual']), key=f"km{idx}")
                km_prox = c2.number_input("KM Próx. Aceite", value=int(row['km_cambio']), key=f"kpc{idx}")
                venc_seg = c3.date_input("Venc. Seguro", value=pd.to_datetime(row['venc_seguro']).date(), key=f"vs{idx}")
                
                if km_act >= km_prox: st.error("🚨 CAMBIO DE ACEITE NECESARIO")
                if (venc_seg - date.today()).days < 7: st.warning("🚨 SEGURO POR VENCER")

                if st.button("Actualizar Auto", key=f"sv{idx}"):
                    conn.execute("UPDATE flota SET km_actual=?, km_cambio=?, venc_seguro=? WHERE nombre=?", (km_act, km_prox, venc_seg, row['nombre']))
                    conn.commit(); st.rerun()
        conn.close()
