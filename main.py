import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILO PREMIUM BORDO Y DORADO ---
st.markdown("""
    <style>
    .main { background-color: #000000; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'Georgia', serif; }
    .stTabs [data-baseweb="tab-list"] { background-color: #4A0404; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    .card-auto { 
        background: linear-gradient(135deg, #4A0404 0%, #2D0202 100%); 
        padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; 
        margin-bottom: 20px; color: white; text-align: center;
    }
    .stButton>button { 
        background-color: #D4AF37 !important; color: #4A0404 !important; 
        font-weight: bold; border-radius: 10px; border: none; width: 100%;
    }
    .insta-btn {
        background: #f09433; 
        background: -moz-linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
        background: -webkit-linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
        background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
        color: white !important; padding: 12px; border-radius: 10px; text-align: center; 
        text-decoration: none; display: block; font-weight: bold; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE NEGOCIO ---
def obtener_cotizacion():
    try:
        data = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion()
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Gris", "KMHJU81VBAU040691", "2010", "HYUNDAI"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", "NSP1352032141", "2015", "TOYOTA"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", "NSP1302097964", "2012", "TOYOTA"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris", "ZRR700415383", "2011", "TOYOTA")
    ]
    for a in autos:
        c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

def parse_date(dt):
    return datetime.fromisoformat(dt) if isinstance(dt, str) else dt

# --- TEXTO DEL CONTRATO LEGAL ---
def obtener_texto_contrato(res, v):
    # Estas dos líneas son la clave de la corrección:
    ini = parse_date(res['inicio'])
    fin = parse_date(res['fin'])
    
    dias = max(1, (fin - ini).days)
    total_gs = float(res['total']) * COTIZACION_DIA
    precio_dia_gs = total_gs / dias
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
* *Marca: {v['marca']}. 
* *Modelo: {v['nombre'].upper()}.
* *Año de fabricación: {v['anio']}.
* *Color: {v['color'].upper()}.
* *Número de chasis: {v['chasis']}.
* *Número de CHAPA: {v['placa']}.
* *Patente: {v['placa']}.

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
Ambas partes firman el presente contrato en señal de conformidad, en Ciudad del este el {datetime.now().strftime('%d/%m/%Y')}. ----------------------------------------------------
El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. 

JM ASOCIADOS                     FIRMA CLIENTE: {res['firma']}
R.U.C. 1.702.076-0                RG/CPF: {res['ci']}
Arrendador                        Arrendatario
"""


# --- INTERFAZ ---
st.title("JM ASOCIADOS | RENT-A-CAR")
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ PANEL ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"><p><b>R$ {v['precio']} / día</b><br>Estado: {v['estado']}</p></div>''', unsafe_allow_html=True)
            if v['estado'] == "Disponible":
                with st.expander("RESERVAR AHORA"):
                    # Lógica de reserva similar a la anterior...
                    st.write("Complete sus datos para el contrato.")
            else:
                st.warning("⚠️ Este vehículo está en mantenimiento o reservado.")

with t_ubi:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=..." width="100%" height="300"></iframe>', unsafe_allow_html=True)
    st.markdown('<a href="https://instagram.com/jm_asociados_consultoria" class="insta-btn">📸 INSTAGRAM OFICIAL</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Acceso Privado", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # --- SECCIÓN: BLOQUEO DE AUTOS ---
        st.subheader("🛠️ ESTADO DE LA FLOTA (Taller/Disponible)")
        f_df = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, fila in f_df.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"**{fila['nombre']}** - Actual: {fila['estado']}")
            if c2.button("CAMBIAR", key=fila['nombre']):
                nuevo = "Taller" if fila['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, fila['nombre']))
                conn.commit(); st.rerun()

        # --- SECCIÓN: FINANZAS Y PROYECCIÓN ---
        st.subheader("📈 PROYECCIÓN ANUAL Y ESTADÍSTICAS")
        res_df = pd.read_sql_query("SELECT total, inicio FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT monto, fecha FROM egresos", conn)
        
        if not res_df.empty:
            res_df['mes'] = pd.to_datetime(res_df['inicio']).dt.strftime('%m')
            graf_data = res_df.groupby('mes')['total'].sum().reset_index()
            fig = px.bar(graf_data, x='mes', y='total', title="Ingresos Mensuales (R$)", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)
            
            total_ingreso = res_df['total'].sum()
            total_egreso = egr_df['monto'].sum()
            st.info(f"💰 Balance Neto Actual: R$ {total_ingreso - total_egreso}")

        # --- SECCIÓN: GESTIÓN DE CONTRATOS ---
        st.subheader("📑 DESCARGAR CONTRATOS Y DATOS")
        todas = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in todas.iterrows():
            with st.expander(f"Contrato: {r['cliente']} ({r['auto']})"):
                v_data = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 10, obtener_texto_contrato(r, v_data).encode('latin-1', 'replace').decode('latin-1'))
                st.download_button("📥 Descargar PDF", pdf.output(dest='S').encode('latin-1'), f"JM_{r['cliente']}.pdf")
        
        # Exportar datos para contabilidad
        st.download_button("📊 Exportar Excel Proyección", todas.to_csv().encode('utf-8'), "proyeccion_jm.csv", "text/csv")
        
        conn.close()
