import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
# import styles # Asegúrate de que este archivo esté en tu GitHub
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Esto reemplaza a SQLite. Los datos ahora viven en tu nube de Google.
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    # Lee la pestaña "GENERAL" de tu Google Sheet
    return conn.read(worksheet="GENERAL", ttl="1m")

def guardar_reserva(datos_nueva_reserva):
    df_actual = leer_datos()
    nuevo_df = pd.concat([df_actual, pd.DataFrame([datos_nueva_reserva])], ignore_index=True)
    conn.update(worksheet="GENERAL", data=nuevo_df)
    st.cache_data.clear()

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()

# --- DATOS DE FLOTA (Estáticos para evitar borrar configuración) ---
FLOTA_DATOS = [
    {"nombre": "Hyundai Tucson Blanco", "precio": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "placa": "AAVI502"},
    {"nombre": "Toyota Vitz Blanco", "precio": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "placa": "AAVP719"},
    {"nombre": "Toyota Vitz Negro", "precio": 195.0, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "placa": "AAOR725"},
    {"nombre": "Toyota Voxy Gris", "precio": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "placa": "AAUG465"}
]

# --- FUNCIONES DE VALIDACIÓN ---
def obtener_fechas_ocupadas(auto):
    df = leer_datos()
    if df.empty or 'auto' not in df.columns: return set()
    
    df_auto = df[df['auto'] == auto]
    bloqueadas = set()
    for _, row in df_auto.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): 
                bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

# --- INTERFAZ ---
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    cols = st.columns(2)
    for i, v in enumerate(FLOTA_DATOS):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p><p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                # (Aquí va tu código de calendario que ya tenías, funciona igual)
                # ... [CÓDIGO DEL CALENDARIO] ...

                f_ini = st.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = st.date_input("Fecha Fin", key=f"d2{v['nombre']}")
                
                # --- PROCESO DE GUARDADO ---
                if st.button("CONFIRMAR RESERVA EN NUBE", key=f"btn{v['nombre']}"):
                    nueva_res = {
                        "cliente": "CLIENTE WEB", # Puedes añadir inputs para esto
                        "auto": v['nombre'],
                        "inicio": f_ini.strftime('%Y-%m-%d'),
                        "fin": f_fin.strftime('%Y-%m-%d'),
                        "total": (f_fin - f_ini).days * v['precio']
                    }
                    guardar_reserva(nueva_res)
                    st.success("¡Guardado en Google Sheets! Ya no se borrará con F5.")

# --- SECCIÓN ADMINISTRADOR ---
with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        st.subheader("Datos desde Google Sheets")
        df_gs = leer_datos()
        st.dataframe(df_gs)