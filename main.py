import streamlit as st
import sqlite3
import pandas as pd
import requests
import urllib.parse
import plotly.express as px
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion_real()

# --- ESTILO PREMIUM JM (BORDO Y DORADO) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@300;400;700&display=swap');
    .stApp {{ background-color: #4A0404; }}
    h1, h2, h3 {{ color: #D4AF37 !important; font-family: 'Playfair Display', serif !important; }}
    p, span, label, div {{ color: #D4AF37 !important; font-family: 'Montserrat', sans-serif !important; }}
    .stTabs [data-baseweb="tab-list"] {{ background-color: #310202; border-radius: 10px; }}
    .stTabs [aria-selected="true"] {{ background-color: #5a0505 !important; border-bottom: 3px solid #D4AF37 !important; }}
    .card-auto {{ background-color: #4A0404; padding: 20px; border-radius: 15px; border: 1px solid #D4AF37; text-align: center; margin-bottom: 15px; }}
    .stButton>button {{ background-color: #4A0404 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; }}
    .stButton>button:hover {{ background-color: #D4AF37 !important; color: #4A0404 !important; }}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{ background-color: #310202 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; }}
    .contrato-legal {{
        background-color: #310202; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px;
        height: 350px; overflow-y: scroll; color: #D4AF37; font-size: 13px; text-align: justify; margin-bottom: 20px; white-space: pre-wrap;
    }}
    .metric-box {{ background-color: #310202; padding: 15px; border-radius: 10px; border-left: 5px solid #D4AF37; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- FUNCIÓN PARA GENERAR EL TEXTO DEL CONTRATO DINÁMICO ---
def generar_texto_contrato(res, v):
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

El vehículo se encuentra en perfecto estado de funcionamiento y libre de cargas o gravámenes. El arrendatario confirma la recepción del vehículo en buen estado, tras realizar una inspección visual y técnica con soporte Técnico VIDEO del Vehículo. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR.

SEGUNDA - Duración del Contrato
El presente contrato tendrá una duración de ( {dias} ) días, comenzando el {res['inicio'].strftime('%d/%m/%Y')} a las {res['inicio'].strftime('%H:%M')} hs y finalizando el {res['fin'].strftime('%d/%m/%Y')} a las {res['fin'].strftime('%H:%M')} hs. de entrega, salvo que se acuerde otra cosa por ambas partes mediante una extensión o terminación anticipada.

TERCERA - Precio y Forma de Pago
El arrendatario se compromete a pagar al arrendador la cantidad de {int(precio_dia_gs/1000)} mil guaraníes ({precio_dia_gs:,.0f}) por cada día de alquiler X DIÁS TOTAL DE: {total_gs:,.0f} Gs.
El pago se realizará de la siguiente manera:
Forma de pago: En Transferencia Electrónica, El monto total será pagado por adelantado, en caso de exceder el tiempo se pagará a la entrega del vehículo lo excedido de acuerdo a lo que corresponda.

CUARTA - Depósito de Seguridad.
El arrendatario pagara cinco millones de guaraníes (Gs. 5.000.000) en caso de siniestro (accidente) para cubrir los daños al vehículo durante el periodo de alquiler.

QUINTA - Condiciones de Uso del Vehículo.
1. El vehículo será utilizado exclusivamente para fines personales dentro del territorio nacional.
2. El ARRENDATARIO es responsable PENAL y CIVIL, de todo lo ocurrido dentro del vehículo y/o encontrado durante el alquiler.
3. El arrendatario se compromete a no subarrendar el vehículo ni permitir que terceros lo conduzcan sin autorización previa del arrendador.
4. El uso del vehículo fuera de los límites del país deberá ser aprobado por el arrendador.

SEXTA - Kilometraje y Excesos
El alquiler incluye un límite de 200 kilómetros por día. En caso de superar este límite, el arrendatario pagará 100.000 guaraníes adicionales por los kilómetros excedente.

SÉPTIMA - Seguro.
• El vehículo cuenta con un seguro básico que cubre Responsabilidad CIVIL en caso de daños a terceros y cobertura en caso de accidentes.
• Servicio de rastreo satelital.
• El arrendatario será responsable de los daños que no estén cubiertos por el seguro, tales como daños por negligencia o uso inapropiado del vehículo.

OCTAVA - Mantenimiento y Reparaciones
El arrendatario se compromete a mantener el vehículo en buen estado de funcionamiento (Agua, combustible, limpieza). En caso de desperfectos, el arrendatario deberá notificar inmediatamente al arrendador. Las reparaciones por desgaste normal son del arrendador; por negligencia, del arrendatario.

NOVENA - Devolución del Vehículo.
El arrendatario devolverá el vehículo en la misma condición en la que lo recibió. Si no se devuelve en la fecha pactada, pagará una penalización de media diaria y/o una diaria completa adicional.

DÉCIMA – Incumplimiento.
En caso de incumplimiento, el arrendador podrá rescindir el contrato inmediatamente y reclamar daños y perjuicios.

UNDÉCIMA - Jurisdicción y Ley Aplicable.
Tribunales del Alto Paraná, Paraguay.

DÉCIMA SEGUNDA - Firma de las Partes.
Ambas partes firman en señal de conformidad en Ciudad del Este el {datetime.now().strftime('%d/%m/%Y')}.

JM ASOCIADOS                     FIRMA CLIENTE: {res['firma']}
R.U.C. 1.702.076-0               RG/CPF: {res['ci']}
Arrendador                       Arrendatario"""

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
    for a in autos: c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit(); conn.close()

init_db()

# --- INTERFAZ ---
st.markdown(f"<h1>J&M ASOCIADOS 🚗 <span style='font-size:15px; color:white;'>Cotización: 1 R$ = {COTIZACION_DIA:,.0f} Gs.</span></h1>", unsafe_allow_html=True)
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f"""<div class="card-auto"><h3>{v['nombre']}</h3><img src="{v['img']}" width="220"><p><b>R$ {v['precio']} / día</b></p></div>""", unsafe_allow_html=True)
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller": st.error("⚠️ VEHÍCULO EN TALLER")
                else:
                    # PREVISUALIZACIÓN CON DATOS VACÍOS PARA LECTURA
                    res_dummy = {'cliente': '........', 'ci': '........', 'domicilio': '........', 'celular': '........', 'inicio': datetime.now(), 'fin': datetime.now(), 'firma': '........'}
                    st.subheader("📄 CONTRATO Y CLÁUSULAS JM")
                    st.markdown(f'<div class="contrato-legal">{generar_texto_contrato(res_dummy, v)}</div>', unsafe_allow_html=True)
                    
                    acepta = st.checkbox("He leído y acepto los términos del contrato", key=f"c_{v['nombre']}")
                    
                    if acepta:
                        st.divider()
                        c1, c2 = st.columns(2)
                        dt_i = datetime.combine(c1.date_input("Inicio", key=f"fi_{v['nombre']}"), c1.time_input("Hora I", time(9,0), key=f"hi_{v['nombre']}"))
                        dt_f = datetime.combine(c2.date_input("Fin", key=f"ff_{v['nombre']}"), c2.time_input("Hora F", time(10,0), key=f"hf_{v['nombre']}"))
                        c_n = st.text_input("Nombre Completo", key=f"n_{v['nombre']}")
                        c_ci = st.text_input("CI / RG / CPF", key=f"ci_{v['nombre']}")
                        c_dom = st.text_input("Domicilio Actual", key=f"d_{v['nombre']}")
                        c_tel = st.text_input("Celular", key=f"t_{v['nombre']}")
                        c_fir = st.text_input("Firma Digital (Nombre)", key=f"f_{v['nombre']}")
                        
                        total_brl = max(1, (dt_f - dt_i).days) * v['precio']
                        st.success(f"TOTAL: R$ {total_brl} (Gs. {total_brl*COTIZACION_DIA:,.0f})")
                        
                        foto = st.file_uploader("Subir Comprobante PIX (Llave: 24510861818)", type=['jpg','png'], key=f"p_{v['nombre']}")
                        
                        if st.button("CONFIRMAR Y PAGAR", key=f"btn_{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                                        (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total_brl, foto.read(), c_fir, c_dom))
                            conn.commit(); conn.close()
                            
                            msg = f"Hola JM, reserva de {c_n}. Auto: {v['nombre']}. Total R$ {total_brl}."
                            url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.markdown(f'<a href="{url_wa}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none;">📲 ENVIAR A WHATSAPP</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Password Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        # MÉTRICAS
        c1, c2, c3 = st.columns(3)
        ing = res_df['total'].sum()
        egr = egr_df['monto'].sum()
        c1.markdown(f"<div class='metric-box'>INGRESOS<br>R$ {ing:,.2f}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'>EGRESOS<br>R$ {egr:,.2f}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'>NETO<br>R$ {ing-egr:,.2f}</div>", unsafe_allow_html=True)
        
        # GRÁFICO
        if not res_df.empty:
            fig = px.pie(res_df, names='auto', values='total', title="Rendimiento por Auto", color_discrete_sequence=px.colors.sequential.YlOrBr)
            st.plotly_chart(fig, use_container_width=True)

        # GASTOS
        with st.expander("➕ CARGAR GASTO"):
            cg = st.text_input("Concepto"); mg = st.number_input("Monto R$")
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (cg, mg, date.today())); conn.commit(); st.rerun()

        # FLOTA
        st.subheader("🛠️ GESTIÓN FLOTA")
        f_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in f_adm.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{f['nombre']}** ({f['estado']})")
            if col2.button("TALLER / DISP", key=f"sw_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # REGISTROS Y PDF
        st.subheader("📑 REGISTROS Y CONTRATOS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                r['inicio'] = datetime.fromisoformat(r['inicio'])
                r['fin'] = datetime.fromisoformat(r['fin'])
                
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
                txt_c = generar_texto_contrato(r, v_res)
                pdf.multi_cell(0, 8, txt_c.encode('latin-1', 'replace').decode('latin-1'))
                
                st.download_button(f"📥 Descargar PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['id']}.pdf")
                if st.button("🗑️ Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
