import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

# --- ESTILO JM PREMIUM (BORDO Y DORADO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@400;700&display=swap');
    .stApp { background-color: #4A0404; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'Playfair Display', serif !important; }
    p, span, label, div { color: #D4AF37 !important; font-family: 'Montserrat', sans-serif !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #310202; border-radius: 10px; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #D4AF37 !important; background-color: #5a0505 !important; }
    .card-auto { background-color: #4A0404; padding: 20px; border-radius: 15px; border: 1px solid #D4AF37; text-align: center; margin-bottom: 15px; }
    .stButton>button { background-color: #4A0404 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #D4AF37 !important; color: #4A0404 !important; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #310202 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; }
    .contrato-box { background-color: #310202; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px; height: 350px; overflow-y: scroll; color: #D4AF37; font-size: 13px; text-align: justify; margin-bottom: 20px; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

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
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Blanco", "KMHJU81VBAU040691", "2010", "HYUNDAI"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", "NSP1352032141", "2015", "TOYOTA"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", "NSP1302097964", "2012", "TOYOTA"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris", "ZRR700415383", "2011", "TOYOTA")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- TEXTO DEL CONTRATO ---
def obtener_texto_contrato(res, v):
    dias = max(1, (res['fin'] - res['inicio']).days)
    precio_dia_gs = v['precio'] * COTIZACION_DIA
    total_gs = dias * precio_dia_gs
    
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR
Entre: 
ARRENDADOR:
Nombre: JM ASOCIADOS 
Cédula de Identidad: 1.702.076-0
Domicilio: CURUPAYTU ESQUINA FARID RAHAL
Teléfono: +595983635573

Y, ARRENDATARIO
Nombre: {res['cliente']}
Cédula de Identidad: RG/CPF. {res['ci']}
Domicilio: {res['domicilio']}
Teléfono: {res['celular']}

Se acuerda lo siguiente:
 PRIMERA - Objeto del Contrato.
El arrendador otorga en alquiler al arrendatario el siguiente vehículo:
* Marca: {v['marca']}. 
* Modelo: {v['nombre'].upper()}.
* Año de fabricación: {v['anio']}.
* Color: {v['color'].upper()}.
* Número de chasis: {v['chasis']}.
* Número de CHAPA: {v['placa']}.
* Patente: {v['placa']}.

El vehículo se encuentra en perfecto estado de funcionamiento y libre de cargas o gravámenes. El arrendatario confirma la recepción del vehículo en buen estado, tras realizar una inspección visual y técnica con soporte Técnico VIDEO del Vehículo. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. ------------------------------------------------------------------------------------

SEGUNDA - *Duración del Contrato
El presente contrato tendrá una duración de ( {dias} ) días, comenzando el {res['inicio'].strftime('%d/%m/%Y')} a las {res['inicio'].strftime('%H:%M')} hs y finalizando el {res['fin'].strftime('%d/%m/%Y')} a las {res['fin'].strftime('%H:%M')} hs. de entrega, salvo que se acuerde otra cosa por ambas partes mediante una extensión o terminación anticipada. ------------------------------------------------------

TERCERA - Precio y Forma de Pago
El arrendatario se compromete a pagar al arrendador la cantidad de {int(precio_dia_gs/1000)} mil guaraníes ({precio_dia_gs:,.0f}) por cada día de alquiler X DIÁS TOTAL DE: {total_gs:,.0f}Gs.------------------------------------------------------------
El pago se realizará de la siguiente manera:
 Forma de pago: En Transferencia Electrónica, El monto total será pagado por adelantado, en caso de exceder el tiempo se pagará a la entrega del vehículo lo excedido de acuerdo a lo que corresponda. ------------------------

CUARTA - Depósito de Seguridad.
El arrendatario pagara cinco millones de guaraníes (Gs. 5.000.000) en caso de siniestro (accidente) para cubrir los daños al vehículo durante el periodo de alquiler. --------------------------------------------------------------------------------------

 QUINTA - Condiciones de Uso del Vehículo.
1. El vehículo será utilizado exclusivamente para fines personales dentro del territorio nacional. ---------------------------------------------------------------
2. El ARRENDATARIO es responsable PENAL y CIVIL, de todo lo ocurrido dentro del vehículo y/o encontrado durante el alquiler. --------------------
3. El arrendatario se compromete a no subarrendar el vehículo ni permitir que terceros lo conduzcan sin autorización previa del arrendador. -----------------------------------------------------------------------------
4. El uso del vehículo fuera de los límites del país deberá ser aprobado por el arrendador. ---------------------------------------------------------------------

SEXTA - Kilometraje y Excesos
El alquiler incluye un límite de 200 kilómetros por día. En caso de superar este límite, el arrendatario pagará 100.000 guaraníes adicionales por los kilómetros excedente. ------------------------------------------------------------------------  

 SÉPTIMA - Seguro.
• El vehículo cuenta con un seguro básico que cubre---------------------------
• Responsabilidad CIVIL en caso de daños a terceros. -------------------------
• Cobertura en caso de accidentes. -------------------------------------------------
• Servicio de rastreo satelital. --------------------------------------------------------
• El arrendatario será responsable de los daños que no estén cubiertos por el seguro, tales como daños por negligencia o uso inapropiado del vehículo. ---------------------------------------------------------------------------------

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
Ambas partes firman el presente contrato en señal de conformidad, en Ciudad del este el {datetime.now().strftime('%d/%m/%Y')}. ----------------------------------------------------
El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. 

JM ASOCIADOS                     FIRMA CLIENTE: {res['firma']}
R.U.C. 1.702.076-0                RG/CPF: {res['ci']}
Arrendador                        Arrendatario"""

# --- INTERFAZ ---
st.markdown(f"<h1>JM ASOCIADOS | 1 R$ = {COTIZACION_DIA:,.0f} Gs.</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p><b>R$ {v['precio']} / día</b></p></div>''', unsafe_allow_html=True)
            with st.expander(f"Alquilar {v['nombre']}"):
                if v['estado'] == "No Disponible":
                    st.error("⚠️ VEHÍCULO EN TALLER / NO DISPONIBLE")
                else:
                    st.subheader("📄 LECTURA DE CONTRATO")
                    res_prev = {'cliente':'........', 'ci':'........', 'domicilio':'........', 'celular':'........', 'inicio':datetime.now(), 'fin':datetime.now(), 'firma':'........'}
                    st.markdown(f'<div class="contrato-box">{obtener_texto_contrato(res_prev, v)}</div>', unsafe_allow_html=True)
                    
                    acepta = st.checkbox("He leído y acepto los términos y condiciones", key=f"check{v['nombre']}")
                    
                    if acepta:
                        st.divider()
                        c1, c2 = st.columns(2)
                        dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                        dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                        c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                        c_d = st.text_input("CI / RG / CPF", key=f"d{v['nombre']}")
                        c_dom = st.text_input("Domicilio", key=f"dom{v['nombre']}")
                        c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                        c_fir = st.text_input("Firma Digital (Nombre)", key=f"f{v['nombre']}")
                        
                        total = max(1, (dt_f - dt_i).days) * v['precio']
                        st.markdown(f"**Monto: R$ {total} | PIX Llave: 24510861818**")
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                                         (c_n, c_d, c_w, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir, c_dom))
                            conn.commit(); conn.close()
                            
                            msj_wa = f"Hola JM, soy {c_n}. Alquiler {v['nombre']} por R$ {total}. Adjunto comprobante."
                            link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}"
                            st.markdown(f'<a href="{link_wa}" target="_blank" style="text-decoration:none;"><div style="background-color:#25
