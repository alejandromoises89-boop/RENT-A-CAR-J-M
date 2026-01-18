import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# Intentar importar estilos si existe el archivo
try:
    import styles
except ImportError:
    pass

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- FUNCIONES GOOGLE SHEETS ---
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("LISTA ALQUILERES DE VEHICULOS-")
    return spreadsheet

def obtener_datos_cloud():
    try:
        sh = conectar_google_sheets()
        worksheet = sh.worksheet("reservas")
        df = pd.DataFrame(worksheet.get_all_records())
        if not df.empty:
            df['inicio'] = pd.to_datetime(df[' SALIDA'], errors='coerce')
            df['fin'] = pd.to_datetime(df[' ENTREGA'], errors='coerce')
            df['auto_excel'] = df['AUTO'].str.upper().str.strip()
            df['TOTAL'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return pd.DataFrame()

def obtener_fechas_ocupadas_unificado(nombre_auto_app):
    df = obtener_datos_cloud()
    bloqueadas = set()
    if df.empty: return bloqueadas
    
    busqueda = nombre_auto_app.upper()
    if "VOXY" in busqueda: busqueda = "VOXY GRIS"
    elif "VITZ NEGRO" in busqueda: busqueda = "VITZ NEGRO"
    elif "VITZ BLANCO" in busqueda: busqueda = "VITZ BLANCO"
    elif "TUCSON" in busqueda: busqueda = "HYUNDAI TUCSON BLANCO"

    df_auto = df[df['auto_excel'] == busqueda]
    for _, row in df_auto.iterrows():
        if pd.notnull(row['inicio']) and pd.notnull(row['fin']):
            start = row['inicio'].date()
            end = row['fin'].date()
            for i in range((end - start).days + 1):
                bloqueadas.add(start + timedelta(days=i))
    return bloqueadas

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()
DB_NAME = 'jm_corporativo_permanente.db'

# --- BASE DE DATOS LOCAL CON MANTENIMIENTO ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    # Añadimos columnas de mantenimiento y seguros
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
        c.execute("INSERT OR IGNORE INTO flota (nombre, precio, img, estado, placa, color, km_actual, km_cambio, venc_seguro, cuota_venc) VALUES (?,?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    
    df_cloud = obtener_datos_cloud()
    if df_cloud.empty: return True
    
    busqueda = auto.upper()
    if "VOXY" in busqueda: busqueda = "VOXY GRIS"
    elif "VITZ NEGRO" in busqueda: busqueda = "VITZ NEGRO"
    elif "VITZ BLANCO" in busqueda: busqueda = "VITZ BLANCO"
    elif "TUCSON" in busqueda: busqueda = "HYUNDAI TUCSON BLANCO"
    
    df_auto = df_cloud[df_cloud['auto_excel'] == busqueda]
    for _, row in df_auto.iterrows():
        if pd.notnull(row['inicio']) and pd.notnull(row['fin']):
            if not (t_fin <= row['inicio'] or t_ini >= row['fin']):
                return False
    return True

# --- INTERFAZ ---
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p><p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas_unificado(v['nombre'])
                meses_display = [(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]

                html_cal = """<style>.airbnb-container { display: flex; flex-direction: row; gap: 25px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }.airbnb-month { min-width: 200px; flex: 1; }.airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }.airbnb-cell { position: relative; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; color: white; }.airbnb-raya { position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; left: 0; z-index: 1; }</style><div class="airbnb-container">"""
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div class="airbnb-month"><div style="font-weight: 600; color: white; margin-bottom: 12px; text-transform: capitalize;">{nombre_mes} {a}</div><div class="airbnb-grid">'
                    for d_nom in ["L","M","M","J","V","S","D"]: html_cal += f'<div style="font-size: 11px; color: #888; padding-bottom: 5px;">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia); es_ocu = f_act in ocupadas; raya = '<div class="airbnb-raya"></div>' if es_ocu else ""
                                html_cal += f'<div class="airbnb-cell">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                st.markdown(html_cal + "</div>", unsafe_allow_html=True)

                st.divider()
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"d2{v['nombre']}")
                h_ini = c1.time_input("Hora Entrega", time(8,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input("Hora Retorno", time(17,0), key=f"h2{v['nombre']}")

                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    
                    if c_n and c_d and c_w:
                        st.info(f"Total: R$ {total_r:,.2f}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            sh = conectar_google_sheets()
                            worksheet = sh.worksheet("reservas")
                            worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), c_n, c_d, c_w, v['nombre'], dt_i.strftime('%Y-%m-%d %H:%M:%S'), dt_f.strftime('%Y-%m-%d %H:%M:%S'), total_r])
                            st.success("Reserva enviada!")
                else:
                    st.error("No disponible")

with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden;"><iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.123!2d-54.6!3d-25.5!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzAwLjAiUyA1NMKwMzYnMDAuMCJX!5e0!3m2!1ses!2spy!4v1642512000000!5m2!1ses!2spy"></iframe></div>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = obtener_datos_cloud()
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # --- BUSCADOR Y LISTA DE CONTRATOS ---
        st.subheader("📋 GESTIÓN DE CONTRATOS (NUBE)")
        busqueda = st.text_input("🔍 Buscar por Nombre de Cliente")
        if not res_df.empty:
            if busqueda:
                res_df = res_df[res_df['NOMBRE'].str.contains(busqueda, case=False, na=False)]
            st.dataframe(res_df[['NOMBRE', 'AUTO', ' SALIDA', ' ENTREGA', 'TOTAL']], use_container_width=True)
        
        # --- MÉTRICAS ---
        ing_total = res_df['TOTAL'].sum() if not res_df.empty else 0
        egr_total = egr_df['monto'].sum() if not egr_df.empty else 0
        st.columns(3)[0].metric("INGRESOS", f"R$ {ing_total:,.2f}")
        st.columns(3)[1].metric("GASTOS", f"R$ {egr_total:,.2f}")
        st.columns(3)[2].metric("UTILIDAD", f"R$ {ing_total - egr_total:,.2f}")

        # --- GESTIÓN DE FLOTA Y MANTENIMIENTO ---
        st.divider()
        st.subheader("🛠️ GESTIÓN DE FLOTA Y MANTENIMIENTO")
        
        for index, row in flota_adm.iterrows():
            with st.expander(f"🚗 {row['nombre']} - {row['placa']}"):
                col1, col2, col3 = st.columns(3)
                
                # Edición de datos
                n_precio = col1.number_input("Precio R$", value=float(row['precio']), key=f"pr{index}")
                n_placa = col2.text_input("Placa", value=row['placa'], key=f"pl{index}")
                n_color = col3.text_input("Color", value=row['color'], key=f"cl{index}")
                
                # Mantenimiento
                km_act = col1.number_input("KM Actual", value=int(row['km_actual']), key=f"km{index}")
                km_prox = col2.number_input("Próx. Cambio Aceite", value=int(row['km_cambio']), key=f"kpc{index}")
                venc_seg = col3.date_input("Venc. Seguro", value=pd.to_datetime(row['venc_seguro']).date(), key=f"vs{index}")
                venc_cuota = col1.date_input("Venc. Próx. Cuota", value=pd.to_datetime(row['cuota_venc']).date(), key=f"vc{index}")
                
                # Alertas Visuales
                dias_seguro = (venc_seg - date.today()).days
                if dias_seguro < 0: st.error(f"🚨 SEGURO VENCIDO HACE {abs(dias_seguro)} DÍAS")
                elif dias_seguro < 30: st.warning(f"⚠️ Seguro vence en {dias_seguro} días")
                
                if km_act >= km_prox: st.error(f"🚨 REQUIERE CAMBIO DE ACEITE (Sobrepasado por {km_act - km_prox} KM)")
                
                if st.button("GUARDAR CAMBIOS", key=f"sav{index}"):
                    conn.execute("""UPDATE flota SET precio=?, placa=?, color=?, km_actual=?, 
                                    km_cambio=?, venc_seguro=?, cuota_venc=? WHERE nombre=?""", 
                                 (n_precio, n_placa, n_color, km_act, km_prox, venc_seg, venc_cuota, row['nombre']))
                    conn.commit()
                    st.success("Datos actualizados")
                    st.rerun()

        # --- GASTOS ---
        st.subheader("💸 REGISTRO DE EGRESOS")
        with st.form("nuevo_gasto"):
            c1, c2 = st.columns(2)
            conc = c1.text_input("Concepto (Ej: Repuesto, Patente, Limpieza)")
            mont = c2.number_input("Monto R$", min_value=0.0)
            if st.form_submit_button("Registrar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (conc, mont, date.today()))
                conn.commit()
                st.rerun()
        
        conn.close()
