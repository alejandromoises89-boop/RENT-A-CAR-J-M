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
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/cK92Y5Hf/tucson-Photoroom.png", "Disponible", "AAVI502", "Blanco"),
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
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    c_pais = st.text_input("País / Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    # --- CONTRATO (FUERA DEL IF DE DATOS PARA QUE SE VEA SIEMPRE) ---
                    st.markdown(f"""
                    <div style="background-color: #f9f9f9; color: #333; padding: 25px; border-radius: 10px; height: 350px; overflow-y: scroll; font-family: 'Courier New', monospace; font-size: 13px; border: 2px solid #D4AF37; text-align: justify; line-height: 1.5; -webkit-overflow-scrolling: touch;">
                        <center><b style="font-size: 16px;">CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR</b></center><br>
                            Entre:<br>
                            <b>ARRENDADOR:</b> J&M ASOCIADOS. CI: 1.702.076-0. Domicilio: CURUPAYTU ESQUINA FARID RAHAL. Teléfono: +595983635573<br><br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}. Doc: {c_d.upper()}. Domicilio: {c_pais.upper()}. Teléfono: {c_w}<br><br>
                            
                            Se acuerda lo siguiente:<br><br>
                            
                            <b>PRIMERA - Objeto del Contrato.</b> El arrendador otorga en alquiler al arrendatario el siguiente vehículo: {v['nombre'].upper()}. Color: {v['color'].upper()}. Chapa/Patente: {v['placa']}. El vehículo se encuentra en perfecto estado de funcionamiento. El arrendatario confirma la recepción del vehículo en buen estado, tras realizar una inspección visual y técnica con soporte Técnico VIDEO del Vehículo. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. ------------------------------------------------------------------------------------<br><br>

                            <b>SEGUNDA - Duración del Contrato.</b> El presente contrato tendrá una duración de {dias} días, comenzando el {dt_i.strftime('%d/%m/%Y')} a las {dt_i.strftime('%H:%M')}hs y finalizando el {dt_f.strftime('%d/%m/%Y')} a las {dt_f.strftime('%H:%M')} hs. de entrega. ------------------------------------------------------<br><br>

                            <b>TERCERA - Precio y Forma de Pago.</b> El arrendatario se compromete a pagar al arrendador la cantidad de Gs. {v['precio'] * COTIZACION_DIA:,.0f} por día. <b>TOTAL: Gs. {total_gs:,.0f}</b>. El pago se realizará por adelantado vía Efectivo y/o Transferencia. En caso de exceder el tiempo se pagará a la entrega del vehículo lo excedido de acuerdo a lo que corresponda. ------------------------<br><br>

                            <b>CUARTA - Depósito de Seguridad.</b> El arrendatario pagará cinco millones de guaraníes (Gs. 5.000.000) en caso de siniestro (accidente) para cubrir los daños al vehículo durante el periodo de alquiler. --------------------------------------------------------------------------------------<br><br>

                            <b>QUINTA - Condiciones de Uso del Vehículo.</b> 1. El vehículo será utilizado exclusivamente para fines personales dentro del territorio nacional. 2. El ARRENDATARIO es responsable PENAL y CIVIL, de todo lo ocurrido dentro del vehículo y/o encontrado durante el alquiler. 3. El arrendatario se compromete a no subarrendar el vehículo ni permitir que terceros lo conduzcan sin autorización previa del arrendador. 4. El uso del vehículo fuera de los límites del país deberá ser aprobado por el arrendador. ---------------------------------------------------------------------<br><br>

                            <b>SEXTA - Kilometraje y Excesos.</b> El alquiler incluye un límite de 200 kilómetros por día. En caso de superar este límite, el arrendatario pagará 100.000 guaraníes adicionales por los kilómetros excedente. ------------------------------------------------------------------------<br><br>

                            <b>SÉPTIMA - Seguro.</b> El vehículo cuenta con un seguro básico que cubre Responsabilidad CIVIL en caso de daños a terceros, Cobertura en caso de accidentes y Servicio de rastreo satelital. El arrendatario será responsable de los daños que no estén cubiertos por el seguro, tales como daños por negligencia o uso inapropiado del vehículo. ---------------------------------------------------------------------------------<br><br>

                            <b>OCTAVA - Mantenimiento y Reparaciones.</b> El arrendatario se compromete a mantener el vehículo en buen estado de funcionamiento (Agua, combustible, limpieza). En caso de desperfectos, el arrendatario deberá notificar inmediatamente al arrendador. Las reparaciones por desgaste normal serán responsabilidad del arrendador, mientras que las debidas a negligencia serán del arrendatario. --------------------<br><br>

                            <b>NOVENA - Devolución del Vehículo.</b> El arrendatario devolverá el vehículo en la misma condición en la que lo recibió, excepto por el desgaste normal. Si el vehículo no se devuelve en la fecha y hora acordada, el arrendatario pagará una penalización de media diaria y/o una diaria completa por cada día adicional. -------------------------------<br><br>

                            <b>DÉCIMA – Incumplimiento.</b> En caso de incumplimiento de alguna de las cláusulas de este contrato, el arrendador podrá rescindir el mismo de manera inmediata, sin perjuicio de reclamar daños y perjuicios. ----------------------------------------------------------------<br><br>

                            <b>UNDÉCIMA - Jurisdicción y Ley Aplicable.</b> Para cualquier disputa derivada de este contrato, las partes se someten a la jurisdicción de los tribunales del Alto Paraná, Paraguay, y se regirán por la legislación vigente en el país. ---------------------------------------------------------------<br><br>

                            <b>DÉCIMA SEGUNDA - Firma de las Partes.</b> Ambas partes firman el presente contrato en señal de conformidad, en Ciudad del Este el {date.today().strftime('%d/%m/%Y')}.<br><br>
                            El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR.<br><br><br>
                            
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    __________________________<br>
                                    <b>J&M ASOCIADOS</b><br>
                                    Arrendador
                                </div>
                                <div>
                                    __________________________<br>
                                    <b>{c_n.upper()}</b><br>
                                    Arrendatario
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        # --- FIN DEL BLOQUE DEL CONTRATO ---

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
