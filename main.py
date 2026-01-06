import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)
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

# --- BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES ---
def generar_contrato_pdf(res, v_datos):
    # v_datos trae: marca, nombre, anio, color, chasis, placa
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Empresa
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 8, "CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    pdf.ln(5)
    
    # Datos fijos y del cliente
    pdf.set_font("Arial", size=9)
    dias = max(1, (pd.to_datetime(res['fin']) - pd.to_datetime(res['inicio'])).days)
    total_gs = res['total'] * 1400  # Ajusta tu tasa aquí
    precio_dia_gs = total_gs / dias

    texto_intro = f"""CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR
Entre: 
ARRENDADOR:
Nombre: JM ASOCIADOS 
Cédula de Identidad: 1.702.076-0
Domicilio: CURUPAYTU ESQUINA FARID RAHAL
Teléfono: +595983635573
Y, ARRENDATARIO
Nombre: 
Cédula de Identidad: 
Domicilio: 
Teléfono: 
Se acuerda lo siguiente:
 PRIMERA - Objeto del Contrato.
El arrendador otorga en alquiler al arrendatario el siguiente vehículo:
*Marca:  
*Modelo: 
*Año de fabricación: 
*Número de chasis: 
*Número de CHAPA: 
*Patente: 
El vehículo se encuentra en perfecto estado de funcionamiento y libre de cargas o gravámenes. El arrendatario confirma la recepción del vehículo en buen estado, tras realizar una inspección visual y técnica con soporte Técnico VIDEO del Vehículo. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. ------------------------------------------------------------------------------------
SEGUNDA - *Duración del Contrato
El presente contrato tendrá una duración de  días, comenzando el  a las  hs y finalizando el  a las  hs. de entrega, salvo que se acuerde otra cosa por ambas partes mediante una extensión o terminación anticipada. ------------------------------------------------------
TERCERA - Precio y Forma de Pago
El arrendatario se compromete a pagar al arrendador la cantidad de    por cada día de alquiler X DIÁS TOTAL DE: .------------------------------------------------------------
El pago se realizará de la siguiente manera:
 Forma de pago: En Transferencia Electrónica, El monto total será pagado por adelantado, en caso de exceder el tiempo se pagará a la entrega del vehículo lo excedido de acuerdo a lo que corresponda. ------------------------
CUARTA - Depósito de Seguridad.
El arrendatario pagara cinco millones de guaraníes (Gs. 5.000.000) en caso de siniestro (accidente) para cubrir los daños al vehículo durante el periodo de alquiler. --------------------------------------------------------------------------------------
 QUINTA - Condiciones de Uso del Vehículo.
1.	El vehículo será utilizado exclusivamente para fines personales dentro del territorio nacional. ---------------------------------------------------------------
2.	El ARRENDATARIO es responsable PENAL y CIVIL, de todo lo ocurrido dentro del vehículo y/o encontrado durante el alquiler. --------------------
3.	 El arrendatario se compromete a no subarrendar el vehículo ni permitir que terceros lo conduzcan sin autorización previa del arrendador. -----------------------------------------------------------------------------
4.	El uso del vehículo fuera de los límites del país deberá ser aprobado por el arrendador. ---------------------------------------------------------------------
SEXTA - Kilometraje y Excesos
El alquiler incluye un límite de 200 kilómetros por día. En caso de superar este límite, el arrendatario pagará 100.000 guaraníes adicionales por los kilómetros excedente. ------------------------------------------------------------------------  
 SÉPTIMA - Seguro.
•	El vehículo cuenta con un seguro básico que cubre---------------------------
•	Responsabilidad CIVIL en caso de daños a terceros. -------------------------
•	Cobertura en caso de accidentes. -------------------------------------------------
•	Servicio de rastreo satelital. --------------------------------------------------------
•	El arrendatario será responsable de los daños que no estén cubiertos por el seguro, tales como daños por negligencia o uso inapropiado del vehículo. ---------------------------------------------------------------------------------
 OCTAVA - Mantenimiento y Reparaciones
El arrendatario se compromete a mantener el vehículo en buen estado de funcionamiento. (Agua, combustible, limpieza) ---------------------------------------En caso de desperfectos técnicos o accidentes, el arrendatario deberá notificar inmediatamente al arrendador. ------------------------------------------------
Las reparaciones necesarias debido al desgaste normal del vehículo serán responsabilidad del arrendador, mientras que las reparaciones debido a uso indebido o negligente serán responsabilidad del arrendatario. --------------------
NOVENA - Devolución del Vehículo.
El arrendatario devolverá el vehículo en la misma condición en la que lo recibió, excepto por el desgaste normal. Si el vehículo no se devuelve en la fecha y hora acordada, el arrendatario pagará una penalización de media diaria y/o una diaria completa por cada día adicional. -------------------------------
DÉCIMA – Incumplimiento.
En caso de incumplimiento de alguna de las cláusulas de este contrato, el arrendador podrá rescindir el mismo de manera inmediata, sin perjuicio de reclamar daños y perjuicios. ----------------------------------------------------------------
UNDÉCIMA - Jurisdicción y Ley Aplicable.
Para cualquier disputa derivada de este contrato, las partes se someten a la jurisdicción de los tribunales del Alto Paraná, Paraguay, y se regirán por la legislación vigente en el país. ---------------------------------------------------------------
DÉCIMA SEGUNDA - Firma de las Partes.
Ambas partes firman el presente contrato en señal de conformidad, en Ciudad del este el . ----------------------------------------------------
El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. 
JM ASOCIADOS                     FIRMA CLIENTE: 
R.U.C. 1.702.076-0                RG/CPF: 
Arrendador                        Arrendatario
.
"""
    pdf.multi_cell(0, 5, texto_intro)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(90, 10, "      _________________________")
    pdf.cell(90, 10, "      _________________________")
    pdf.ln(5)
    pdf.cell(90, 10, "            JM ASOCIADOS")
    pdf.cell(90, 10, f"            CLIENTE: {res['cliente']}")
    pdf.ln(5)
    pdf.cell(90, 10, "             Arrendador")
    pdf.cell(90, 10, f"             RG/CPF: {res['ci']}")

    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "No Disponible":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_en_guaranies = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom: 2px;">
                        R$ {v['precio']} / día
                    </p>
                    <p style="font-weight: bold; color: #28a745; margin-top: 0px;">
                        Gs. {precio_en_guaranies:,.0f} / día
                    </p>
                </div>
            ''', unsafe_allow_html=True)
            with st.expander(f"Alquilar {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total}</b><br>Llave: 24510861818<br>Marina Baez - Santander</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read()))
                                conn.commit(); conn.close()
                                
                                st.success("¡Reserva Guardada con éxito!")

                                # MENSAJE WHATSAPP PROFESIONAL
                                msj_wa = (
                                    f"Hola JM, soy {c_n}.\n\n"
                                    f"📄 Mis datos: \n"
                                    f"Documento/CPF: {c_d}\n\n"
                                    f"🚗 Detalles del Alquiler: \n"
                                    f"Vehículo: {v['nombre']}\n"
                                    f"🗓️ Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                    f"🗓️ Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                    f"💰 Monto Pagado: R$ {total}\n\n"
                                    f"Aquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!"
                                )
                                texto_url = urllib.parse.quote(msj_wa)
                                link_wa = f"https://wa.me/595991681191?text={texto_url}"
                                
                                st.markdown(f'''
                                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">
                                            📲 ENVIAR DATOS Y COMPROBANTE AL WHATSAPP
                                        </div>
                                    </a>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("Por favor, adjunte la foto del comprobante.")

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('''
        <div style="border: 2px solid #D4AF37; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <iframe 
                src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14404.144865004746!2d-54.618683!3d-25.503831!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685764d7883a9%3A0xc3f8e6583907c030!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1700000000000!5m2!1ses!2spy" 
                width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy">
            </iframe>
        </div>
    ''', unsafe_allow_html=True)
    
    # BOTÓN DE INSTAGRAM PERSONALIZADO
    st.markdown('''
        <br>
        <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" style="text-decoration:none;">
            <div style="background-color:#E1306C; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">
                📸 VISITAR INSTAGRAM OFICIAL: JM ASOCIADOS
            </div>
        </a>
    ''', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave Admin", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        st.title("📊 BALANCE Y FINANZAS")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS", f"R$ {ing:,.2f}")
        c_f2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_f3.metric("NETO", f"R$ {ing - egr:,.2f}")
        
        if not res_df.empty:
            fig = px.bar(res_df, x='auto', y='total', color='auto', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🛠️ ESTADO DE FLOTA")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            col_b1, col_b2 = st.columns([3, 1])
            col_b1.write(f"{f['nombre']} - ({f['estado']})")
            if col_b2.button("CAMBIAR", key=f"sw{f['nombre']}"):
                nuevo = "No Disponible" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                ca, cb = st.columns(2)
                if r['comprobante']: ca.image(r['comprobante'], width=200)
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                
                if cb.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
