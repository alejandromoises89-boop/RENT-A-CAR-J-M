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

# Intentar aplicar los estilos premium si el archivo existe
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
    
    # Inserción de flota inicial con la Tucson sin fondo
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
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
    if c.fetchone()[0] == "En Taller": return False
    # Evitar solapamiento de fechas
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
                # --- CALENDARIO TIPO AIRBNB HORIZONTAL FORZADO ---
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses_display = [
                    (date.today().month, date.today().year), 
                    ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)
                ]

                html_cal = """
                <style>
                    .airbnb-container { display: flex; flex-direction: row; gap: 25px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }
                    .airbnb-month { min-width: 200px; flex: 1; font-family: sans-serif; }
                    .airbnb-header { font-weight: 600; font-size: 15px; margin-bottom: 12px; color: white; text-transform: capitalize; }
                    .airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }
                    .airbnb-day-name { font-size: 11px; color: #888; padding-bottom: 5px; }
                    .airbnb-cell { position: relative; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; color: white; }
                    .airbnb-raya { position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; left: 0; z-index: 1; }
                    .airbnb-ocupado { color: #555 !important; }
                </style>
                <div class="airbnb-container">
                """
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div class="airbnb-month"><div class="airbnb-header">{nombre_mes} {a}</div><div class="airbnb-grid">'
                    for d_nom in ["L","M","M","J","V","S","D"]:
                        html_cal += f'<div class="airbnb-day-name">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia)
                                es_ocu = f_act in ocupadas
                                raya = '<div class="airbnb-raya"></div>' if es_ocu else ""
                                html_cal += f'<div class="airbnb-cell {"airbnb-ocupado" if es_ocu else ""}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)

                st.divider()
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(10,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(12,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", placeholder="Ej: Guillerme Oliveira", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("Número de WhatsApp", key=f"w{v['nombre']}")
                    c_pais = st.text_input("País / Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        # --- CONTRATO COMPLETO ---
                        st.markdown(f"""
                        <div style="background-color: #f9f9f9; color: #333; padding: 20px; border-radius: 10px; height: 350px; overflow-y: scroll; font-family: 'Courier New', monospace; font-size: 13px; border: 2px solid #D4AF37; text-align: justify; line-height: 1.5; -webkit-overflow-scrolling: touch;">
                            <center><b>CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR</b></center><br>
                            <b>ARRENDADOR:</b> J&M ASOCIADOS. CI: 1.702.076-0. Domicilio: CURUPAYTU ESQUINA FARID RAHAL.<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}. Doc: {c_d.upper()}. Domicilio: {c_pais.upper()}.<br><br>
                            <b>PRIMERA - OBJETO:</b> {v['nombre'].upper()}. Chapa: {v['placa']}. Color: {v['color'].upper()}. El vehículo se recibe en perfecto estado con soporte técnico VIDEO.<br><br>
                            <b>SEGUNDA - DURACIÓN:</b> {dias} días. Desde {dt_i.strftime('%d/%m/%Y %H:%M')} hasta {dt_f.strftime('%d/%m/%Y %H:%M')}.<br><br>
                            <b>TERCERA - PRECIO:</b> Gs. {v['precio']*COTIZACION_DIA:,.0f} / día. TOTAL: Gs. {total_gs:,.0f}.<br><br>
                            <b>CUARTA - DEPÓSITO:</b> Gs. 5.000.000 en caso de siniestro.<br><br>
                            <b>QUINTA - RESPONSABILIDAD:</b> El ARRENDATARIO es responsable PENAL y CIVIL de todo lo ocurrido dentro del vehículo.<br><br>
                            <b>SEXTA - KILOMETRAJE:</b> Límite 200km/día. Excedente: 100.000 Gs adicionales.<br><br>
                            <b>SÉPTIMA - SEGURO:</b> Cobertura civil, accidentes y rastreo satelital. Negligencia no cubierta.<br><br>
                            <b>DÉCIMA SEGUNDA:</b> Firmado en CDE el {date.today().strftime('%d/%m/%Y')}.<br><br>
                            <div style="display: flex; justify-content: space-between;">
                                <span>______________________<br>J&M ASOCIADOS</span>
                                <span>______________________<br>{c_n.upper()}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- CASILLA DE ACEPTACIÓN ---
                        acepto = st.checkbox("He leído el contrato y acepto todos los términos y condiciones.", key=f"check{v['nombre']}")
                        
                        st.markdown(f'<div style="background-color:#1a1c23; padding:15px; border-radius:10px; border:1px solid #D4AF37; margin-top:10px;"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        
                        foto = st.file_uploader("Adjuntar Comprobante de Pago", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                texto_wa = f"Hola JM, soy {c_n}.\nHe leído el contrato y acepto los términos.\n🚗 Vehículo: {v['nombre']}\n🗓️ Periodo: {dt_i.strftime('%d/%m/%Y')} al {dt_f.strftime('%d/%m/%Y')}\n💰 Total: R$ {total_r}\nAdjunto comprobante."
                                link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(texto_wa)}"
                                st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva Guardada!")
                            else:
                                st.error("Por favor, adjunte el comprobante.")
                        if not acepto:
                            st.warning("Debes aceptar el contrato para habilitar el botón de confirmación.")
                else:
                    st.error("Vehículo no disponible en las fechas seleccionadas.")


with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden;"><iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy"></iframe></div>', unsafe_allow_html=True)
    cs1, cs2 = st.columns(2)
    cs1.markdown('<a href="https://instagram.com/jm_asociados_consultoria" target="_blank"><div style="background: linear-gradient(45deg, #f09433, #bc1888); color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">📸 INSTAGRAM</div></a>', unsafe_allow_html=True)
    cs2.markdown('<a href="https://wa.me/595991681191" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">💬 WHATSAPP</div></a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL ESTRATÉGICO")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("INGRESOS TOTALES", f"R$ {ing:,.2f}")
        c_m2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_m3.metric("UTILIDAD NETA", f"R$ {ing - egr:,.2f}")

        cg1, cg2 = st.columns(2)
        with cg1:
            if not res_df.empty:
                fig1 = px.pie(res_df, values='total', names='auto', hole=0.4, color_discrete_sequence=['#D4AF37', '#B8860B', '#FFD700'])
                st.plotly_chart(fig1, use_container_width=True)
        with cg2:
            fig2 = px.bar(x=["Ingresos", "Gastos"], y=[ing, egr], color=["Ingresos", "Gastos"], color_discrete_map={"Ingresos": "#D4AF37", "Gastos": "#800020"})
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("💸 CARGAR GASTO"):
            with st.form("g"):
                c_g = st.text_input("Concepto"); m_g = st.number_input("Monto R$")
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (c_g, m_g, date.today())); conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2,1,1])
            ca1.write(f"**{f['nombre']}** ({f['placa']})")
            ca2.write("🟢 Disponible" if f['estado'] == "Disponible" else "🔴 Taller")
            if ca3.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre'])); conn.commit(); st.rerun()

        st.subheader("📑 REGISTRO DE RESERVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | Periodo: {r['inicio']} al {r['fin']} | Total: R$ {r['total']}")
                if r['comprobante']: st.image(r['comprobante'], width=200)
                if st.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()