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

# --- FUNCIONES GOOGLE SHEETS (UNIFICADAS Y CORREGIDAS) ---
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("LISTA DE ALQUILERES DE VEHICULOS")
    return spreadsheet

def obtener_datos_cloud():
    try:
        sh = conectar_google_sheets()
        worksheet = sh.worksheet("reservas")
        df = pd.DataFrame(worksheet.get_all_records())
        if not df.empty:
            df['inicio'] = pd.to_datetime(df['inicio'])
            df['fin'] = pd.to_datetime(df['fin'])
            # BLOQUEO AUTOMÁTICO: Filtramos para que solo muestre lo anterior a 2026
            fecha_limite = pd.Timestamp(2026, 1, 1)
            df = df[df['inicio'] < fecha_limite]
        return df
    except Exception as e:
        return pd.DataFrame()

# Aplicar estilo premium
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

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

# --- BASE DE DATOS LOCAL ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE VALIDACIÓN ---
def obtener_fechas_ocupadas(auto):
    df = obtener_datos_cloud()
    bloqueadas = set()
    if df.empty: return bloqueadas
    
    df_auto = df[df['auto'] == auto]
    for _, row in df_auto.iterrows():
        try:
            start = row['inicio'].date()
            end = row['fin'].date()
            for i in range((end - start).days + 1): 
                bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    
    df_cloud = obtener_datos_cloud()
    if df_cloud.empty: return True
    
    df_auto = df_cloud[df_cloud['auto'] == auto]
    for _, row in df_auto.iterrows():
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
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
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
                                html_cal += f'<div class="airbnb-cell {"airbnb-ocupado" if es_ocu else ""}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                st.markdown(html_cal + "</div>", unsafe_allow_html=True)

                st.divider()
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"d2{v['nombre']}")

                es_finde_i = f_ini.weekday() >= 5
                es_finde_f = f_fin.weekday() >= 5
                h_max_i = time(12, 0) if es_finde_i else time(17, 0)
                h_max_f = time(12, 0) if es_finde_f else time(17, 0)
                
                h_ini = c1.time_input(f"Hora Entrega (8:00 - {h_max_i.strftime('%H:%M')})", time(8,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input(f"Hora Retorno (8:00 - {h_max_f.strftime('%H:%M')})", h_max_f, key=f"h2{v['nombre']}")

                horario_valido = True
                if h_ini < time(8,0) or h_ini > h_max_i:
                    st.error(f"⚠️ Entrega permitida solo de 08:00 a {h_max_i.strftime('%H:%M')}")
                    horario_valido = False
                if h_fin < time(8,0) or h_fin > h_max_f:
                    st.error(f"⚠️ Retorno permitido solo de 08:00 a {h_max_f.strftime('%H:%M')}")
                    horario_valido = False

                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                if esta_disponible(v['nombre'], dt_i, dt_f) and horario_valido:
                    c_n = st.text_input("Nombre Completo", placeholder="Ej: Guillerme Oliveira", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("Número de WhatsApp", key=f"w{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f"""
                        <div style="background-color: #f9f9f9; color: #333; padding: 25px; border-radius: 10px; height: 300px; overflow-y: scroll; font-family: 'Courier New', monospace; font-size: 13px; border: 2px solid #D4AF37; text-align: justify; line-height: 1.5;">
                            <center><b style="font-size: 16px;">CONTRATO DE ALQUILER DE VEHÍCULO</b></center><br>
                            <b>ARRENDADOR:</b> J&M ASOCIADOS. C.I.: 1.702.076-0.<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}. Doc: {c_d.upper()}.<br><br>
                            <b>DURACIÓN:</b> {dias} días. Desde {dt_i.strftime('%d/%m/%Y %H:%M')} hasta {dt_f.strftime('%d/%m/%Y %H:%M')}.<br><br>
                            <b>PRECIO TOTAL:</b> Gs. {total_gs:,.0f} / R$ {total_r:,.2f}.<br>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        acepto = st.checkbox("He leído y acepto los términos.", key=f"chk{v['nombre']}")
                        st.markdown(f'<div style="background-color:#1a1c23; padding:15px; border-radius:10px; border:1px solid #D4AF37; margin-top:10px;"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818 - Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                try:
                                    # Guardar en Google Sheets
                                    sh = conectar_google_sheets()
                                    worksheet = sh.worksheet("reservas")
                                    worksheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), c_n, c_d, c_w, v['nombre'], dt_i.strftime('%Y-%m-%d %H:%M:%S'), dt_f.strftime('%Y-%m-%d %H:%M:%S'), total_r])
                                    
                                    # Guardar en SQLite Local
                                    conn = sqlite3.connect(DB_NAME)
                                    conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                    conn.commit(); conn.close()
                                    
                                    texto_wa = f"Hola JM, soy {c_n}.\nHe realizado una reserva.\n🚗 {v['nombre']}\n🗓️ {dt_i.strftime('%d/%m/%Y')} al {dt_f.strftime('%d/%m/%Y')}\n💰 R$ {total_r}"
                                    link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(texto_wa)}"
                                    st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                                    st.success("¡Reserva confirmada!")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                else:
                    if horario_valido: st.error("Vehículo no disponible en las fechas seleccionadas.")

with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden;"><iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d14402.046808728952!2d-54.6366113!3d-25.5213456!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ses!2spy!4v1700000000000"></iframe></div>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = obtener_datos_cloud()
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        ing_r = res_df['total'].sum() if not res_df.empty else 0
        egr_r = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("INGRESOS", f"R$ {ing_r:,.2f}")
        c_m2.metric("GASTOS", f"R$ {egr_r:,.2f}")
        c_m3.metric("UTILIDAD", f"R$ {ing_r - egr_r:,.2f}")

        # Ajuste de Precios
        st.subheader("💰 PRECIOS")
        for _, f in flota_adm.iterrows():
            cp1, cp2 = st.columns([3, 1])
            nuevo_p = cp2.number_input(f"R$ {f['nombre']}", value=float(f['precio']), key=f"p_{f['nombre']}")
            if nuevo_p != f['precio']:
                conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (nuevo_p, f['nombre']))
                conn.commit(); st.rerun()

        # Gestión de Estado
        st.subheader("🛠️ ESTADO FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2, 1, 1])
            ca1.write(f"{f['nombre']}")
            if ca3.button("CAMBIAR", key=f"st_{f['nombre']}"):
                nuevo_est = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo_est, f['nombre']))
                conn.commit(); st.rerun()

        # Gastos
        with st.expander("➕ NUEVO GASTO"):
            with st.form("g"):
                conc = st.text_input("Concepto")
                monto = st.number_input("R$", step=1.0)
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (conc, monto, date.today()))
                    conn.commit(); st.rerun()

        conn.close()
