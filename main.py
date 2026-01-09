import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

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

# --- BASE DE DATOS ---
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
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
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

                html_cal = """<style>.airbnb-container { display: flex; gap: 20px; overflow-x: auto; padding: 10px 0; }.airbnb-month { min-width: 200px; }.airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }.airbnb-cell { position: relative; height: 30px; display: flex; align-items: center; justify-content: center; font-size: 12px; }.airbnb-raya { position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; z-index: 1; }</style><div class="airbnb-container">"""
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div class="airbnb-month"><div style="color:white; font-weight:bold; margin-bottom:10px;">{nombre_mes} {a}</div><div class="airbnb-grid">'
                    for d_nom in ["L","M","M","J","V","S","D"]: html_cal += f'<div style="color:#888; font-size:10px;">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia); es_ocu = f_act in ocupadas; raya = '<div class="airbnb-raya"></div>' if es_ocu else ""
                                html_cal += f'<div class="airbnb-cell" style="color: {"#555" if es_ocu else "white"}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                st.markdown(html_cal + "</div>", unsafe_allow_html=True)

                st.divider()
                # --- DATOS DEL CLIENTE Y HORARIOS ---
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Inicio", key=f"d1{v['nombre']}")
                f_fin = c2.date_input("Fin", key=f"d2{v['nombre']}")

                # Lógica de Horarios Solicitada
                es_finde = f_fin.weekday() >= 5 
                hora_limite = time(12, 0) if es_finde else time(17, 0)
                msg_h = "Sáb/Dom/Fer (Máx 12:00)" if es_finde else "Lun a Vie (Máx 17:00)"
                
                h_ini = c1.time_input("Hora Entrega", time(10,0), key=f"h1{v['nombre']}")
                h_fin = c2.time_input(f"Retorno - {msg_h}", hora_limite, key=f"h2{v['nombre']}")

                if h_fin > hora_limite:
                    st.warning(f"La devolución debe ser antes de las {hora_limite.strftime('%H:%M')}")
                    h_fin = hora_limite

                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    
                    dias = max(1, (f_fin - f_ini).days)
                    total_r = dias * v['precio']
                    
                    if c_n and c_d and c_w:
                        st.markdown(f"""<div style="background:#f9f9f9; color:#333; padding:15px; border-radius:10px; height:250px; overflow-y:scroll; font-size:12px; border:2px solid #D4AF37;">
                            <center><b>CONTRATO J&M ASOCIADOS</b></center><br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}<br><b>DOC:</b> {c_d.upper()}<br><b>AUTO:</b> {v['nombre']}<br>
                            <b>RETORNO:</b> {f_fin.strftime('%d/%m/%Y')} {h_fin.strftime('%H:%M')}hs.<br><br>
                            <b>CLAUSULAS:</b> El cliente es responsable penal y civil de todo lo ocurrido. Límite 200km/día. Excedente Gs. 100.000.<br><br>
                            <b>FIRMA:</b> Al firmar abajo acepta los términos.
                        </div>""", unsafe_allow_html=True)
                        
                        st.markdown("### ✒️ FIRMA DIGITAL")
                        firma = st.text_input("Escriba su nombre completo para firmar:", key=f"f_dig_{v['nombre']}")
                        acepto = st.checkbox("Acepto los términos", key=f"chk{v['nombre']}")
                        
                        st.markdown(f'<div style="background:#1a1c23; padding:10px; border-radius:10px; border:1px solid #D4AF37;">PIX: R$ {total_r}<br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Comprobante", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not (acepto and len(firma)>5)):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (f"{c_n} (FIRMADO: {firma})", c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                texto_wa = f"Hola JM, soy {c_n}.\nReserva firmada.\n🚗 {v['nombre']}\n🗓️ Retorno: {dt_f.strftime('%d/%m/%Y %H:%M')}\n💰 R$ {total_r}"
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(texto_wa)}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva Guardada!")
                            else: st.error("Adjunte comprobante")
                else: st.error("No disponible")

# --- UBICACIÓN ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="300" src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d3601.2427807094056!2d-54.606272!3d-25.530349!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2zMjXCsDMxJzQ5LjMiUyA1NMKwMzYnMjIuNiJX!5e0!3m2!1ses!2spy!4v1715800000000!5m2!1ses!2spy"></iframe>', unsafe_allow_html=True)

# --- ADMINISTRADOR ---
with t_adm:
    if st.text_input("Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        st.metric("UTILIDAD NETA", f"R$ {res_df['total'].sum() - egr_df['monto'].sum():,.2f}")

        st.subheader("📑 RESERVAS ACTUALES")
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                st.write(f"DOC: {r['ci']} | Fin: {r['fin']}")
                if r['comprobante']: st.image(r['comprobante'], width=150)
                if st.button("Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()