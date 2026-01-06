import streamlit as st
import sqlite3
import pandas as pd
import requests
import urllib.parse
import plotly.express as px
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real()

# --- ESTILO ELEGANTE JM (BORDO PROFUNDO Y LETRAS DORADAS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@300;400;700&display=swap');

    .stApp {{ background-color: #4A0404; }}
    
    h1, h2, h3 {{ 
        color: #D4AF37 !important; 
        font-family: 'Playfair Display', serif !important; 
        letter-spacing: 2px;
    }}
    
    p, span, label, div {{ 
        color: #D4AF37 !important; 
        font-family: 'Montserrat', sans-serif !important; 
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ background-color: #310202; border-radius: 10px; }}
    .stTabs [data-baseweb="tab"] {{ color: #D4AF37 !important; font-size: 16px; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 3px solid #D4AF37 !important; background-color: #5a0505 !important; }}

    /* Cards de Autos */
    .card-auto {{ 
        background-color: #4A0404; 
        padding: 25px; 
        border-radius: 20px; 
        border: 1px solid #D4AF37; 
        text-align: center;
        margin-bottom: 20px;
    }}
    
    /* Botones JM */
    .stButton>button {{ 
        background-color: #4A0404 !important; 
        color: #D4AF37 !important; 
        border: 1px solid #D4AF37 !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stButton>button:hover {{ background-color: #D4AF37 !important; color: #4A0404 !important; }}

    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: #310202 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }}

    .metric-box {{
        background-color: #310202;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #D4AF37;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- TEXTO LEGAL COMPLETO ---
def obtener_texto_contrato(res, v):
    ini = res['inicio'] if isinstance(res['inicio'], datetime) else datetime.fromisoformat(res['inicio'])
    fin = res['fin'] if isinstance(res['fin'], datetime) else datetime.fromisoformat(res['fin'])
    total_gs = float(res['total']) * COTIZACION_DIA
    return f"""CONTRATO DE ALQUILER Y AUTORIZACIÓN PARA CONDUCIR - JM ASOCIADOS
------------------------------------------------------------------------------------
ARRENDADOR: JM ASOCIADOS | CI: 1.702.076-0
ARRENDATARIO: {res['cliente']} | CI/RG: {res['ci']} | TEL: {res['celular']}

VEHÍCULO: {v['marca']} {v['nombre']} | AÑO: {v['anio']}
COLOR: {v['color']} | PLACA: {v['placa']} | CHASIS: {v['chasis']}

PERIODO: DESDE {ini.strftime('%d/%m/%Y %H:%M')} HASTA {fin.strftime('%d/%m/%Y %H:%M')}
COSTO TOTAL: R$ {res['total']} (Cotización Gs. {COTIZACION_DIA:,.0f} | Total Gs. {total_gs:,.0f})

CLAUSULAS PRINCIPALES:
1. El vehículo se entrega en perfecto estado visual y mecánico.
2. EL ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EN TODO EL MERCOSUR.
3. El arrendatario es responsable penal y civil de todo lo ocurrido dentro del vehículo.
4. Depósito de siniestro de Gs. 5.000.000 en caso de accidente.

FIRMA CONFORMIDAD: {res['firma']}
FECHA: {datetime.now().strftime('%d/%m/%Y')}
------------------------------------------------------------------------------------"""

# --- BASE DE DATOS ---
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
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- INTERFAZ ---
st.markdown(f"<h1>J&M ASOCIADOS 🚗 <span style='font-size:15px; color:white;'>Cotización Hoy: 1 R$ = {COTIZACION_DIA:,.0f} Gs.</span></h1>", unsafe_allow_html=True)
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f"""<div class="card-auto">
                <h3>{v['nombre']}</h3>
                <img src="{v['img']}" width="250">
                <p><b>R$ {v['precio']} | Gs. {v['precio']*COTIZACION_DIA:,.0f} / día</b></p>
                </div>""", unsafe_allow_html=True)
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller":
                    st.error("⚠️ VEHÍCULO EN MANTENIMIENTO")
                else:
                    c1, c2 = st.columns(2)
                    dt_i = datetime.combine(c1.date_input("Inicio", key=f"fi_{v['nombre']}"), c1.time_input("Hora", time(9,0), key=f"hi_{v['nombre']}"))
                    dt_f = datetime.combine(c2.date_input("Fin", key=f"ff_{v['nombre']}"), c2.time_input("Hora ", time(10,0), key=f"hf_{v['nombre']}"))
                    c_n = st.text_input("Nombre Completo", key=f"n_{v['nombre']}")
                    c_ci = st.text_input("Documento CI/RG", key=f"ci_{v['nombre']}")
                    c_fir = st.text_input("Firma Digital", key=f"f_{v['nombre']}")
                    
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    if c_n and c_ci:
                        res_temp = {'cliente':c_n, 'ci':c_ci, 'celular':'+595', 'inicio':dt_i, 'fin':dt_f, 'total':total, 'firma':c_fir, 'domicilio':''}
                        st.text_area("Contrato:", obtener_texto_contrato(res_temp, v), height=150)
                        st.markdown(f"**Total PIX: R$ {total}** | Llave: 24510861818")
                        foto = st.file_uploader("Comprobante", type=['jpg','png'], key=f"p_{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"b_{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, auto, inicio, fin, total, comprobante, firma) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_ci, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir))
                            conn.commit(); conn.close()
                            msg = f"Reserva de {c_n}. Auto: {v['nombre']}. Total R$ {total}."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank" style="color:#D4AF37; text-decoration:none; border:1px solid #D4AF37; padding:10px; border-radius:10px;">📲 ENVIAR WHATSAPP</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Acceso Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # --- FINANZAS ---
        st.subheader("📊 FINANZAS Y ESTADÍSTICAS")
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        ing = res_df['total'].sum()
        egr = egr_df['monto'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'>INGRESOS<br>R$ {ing:,.2f}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'>EGRESOS<br>R$ {egr:,.2f}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'>NETO<br>R$ {ing-egr:,.2f}</div>", unsafe_allow_html=True)
        
        if not res_df.empty:
            fig = px.pie(res_df, names='auto', values='total', title="Ventas por Vehículo", color_discrete_sequence=px.colors.sequential.YlOrBr)
            st.plotly_chart(fig, use_container_width=True)

        # --- CARGAR GASTO ---
        with st.expander("➕ REGISTRAR GASTO"):
            con_g = st.text_input("Concepto Gasto")
            mon_g = st.number_input("Monto R$", min_value=0.0)
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con_g, mon_g, date.today()))
                conn.commit(); st.rerun()

        # --- GESTIÓN DE FLOTA ---
        st.subheader("🛠️ ESTADO DE FLOTA")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{f['nombre']}** - ({f['estado']})")
            if col2.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # --- RESERVAS Y PDF ---
        st.subheader("📑 CONTRATOS Y ELIMINAR")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 10, obtener_texto_contrato(r, v_res).encode('latin-1', 'replace').decode('latin-1'))
                
                c_a, c_b = st.columns(2)
                c_a.download_button(f"📥 PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['id']}.pdf")
                if c_b.button("🗑️ Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
