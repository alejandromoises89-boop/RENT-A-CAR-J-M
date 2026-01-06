import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. FUNCIÓN DE COTIZACIÓN (REAL A GUARANÍ) ---
def obtener_cotizacion():
    try:
        # API de tipo de cambio en tiempo real
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0  # Valor de respaldo si falla el internet

COTIZACION_DIA = obtener_cotizacion()

# --- 2. CONFIGURACIÓN VISUAL Y ESTILOS ---
st.set_page_config(page_title="JM ASOCIADOS | Gestión Corporativa", layout="wide")

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Playfair+Display:ital@0;1&display=swap');
        .stApp {{ background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }}
        .logo-jm {{ font-family: 'Cinzel', serif; color: #D4AF37; font-size: 4rem; text-align: center; margin: 0; }}
        .cotizacion-barra {{ text-align: center; background: rgba(212,175,55,0.2); padding: 10px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #D4AF37; }}
        .card-auto {{ background: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; text-align: center; margin-bottom: 10px; }}
        .documento-papel {{ background: white; color: black; padding: 40px; font-family: 'Times New Roman', serif; border: 1px solid #ccc; line-height: 1.4; }}
        .clausula-header {{ font-weight: bold; text-decoration: underline; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, 
                  inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, 
                  nacionalidad TEXT, direccion TEXT, total_pyg REAL)''')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
          ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/PGrYTDhJ/2098.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNCION PDF (12 CLÁUSULAS) ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=9)
    
    clausulas = f"""
    En Ciudad del Este, a {datetime.now().strftime('%d/%m/%Y')}, entre JM ASOCIADOS (Locador) y {res['cliente']} (Locatario), CI: {res['ci']}, Nacionalidad: {res['nacionalidad']}, Domicilio: {res['direccion']}.

    1. OBJETO: El Locador cede el vehículo {res['auto']}, Placa {placa}, Color {color}.
    2. PLAZO: De {res['inicio']} a {res['fin']}.
    3. PRECIO: R$ {res['total']} (Equivalente a Gs. {res['total_pyg']:,.0f}).
    4. RESPONSABILIDAD: El Locatario asume responsabilidad civil y penal por cualquier evento.
    5. COMBUSTIBLE: Debe retornar con el mismo nivel entregado.
    6. MULTAS: Cargo exclusivo del Locatario.
    7. PROHIBICIONES: No conducir bajo efectos de alcohol o sustancias.
    8. MANTENIMIENTO: El Locatario debe velar por el buen estado mecánico.
    9. SEGURO: El deducible en caso de siniestro será cubierto por el Locatario.
    10. LÍMITE: Prohibido salir del país sin autorización escrita.
    11. RESCISIÓN: El incumplimiento de estas cláusulas anula el contrato.
    12. JURISDICCIÓN: Tribunales de Ciudad del Este.

    Firmas: ____________________ (Locador)      ____________________ (Locatario)
    """
    pdf.multi_cell(0, 6, clausulas)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFAZ ---
st.markdown('<div class="logo-jm">JM</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cotizacion-barra">Cotización Online: 1 Real = {COTIZACION_DIA:,.0f} Gs.</div>', unsafe_allow_html=True)

t_res, t_adm = st.tabs(["📋 RESERVAS Y CATÁLOGO", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto">
                <h3>{v["nombre"]}</h3>
                <img src="{v["img"]}" width="100%">
                <h4 style="color:#D4AF37; margin:0;">R$ {v['precio']} / Gs. {precio_gs:,.0f}</h4>
            </div>''', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                c_d = st.text_input("Documento/CI", key=f"d{v['nombre']}")
                c_nac = st.text_input("Nacionalidad", value="Paraguaya", key=f"nac{v['nombre']}")
                c_dir = st.text_input("Dirección/Hotel", key=f"dir{v['nombre']}")
                
                d1 = st.date_input("Inicio", key=f"d1{v['nombre']}")
                d2 = st.date_input("Fin", value=date.today() + timedelta(days=2), key=f"d2{v['nombre']}")
                
                dias = max(1, (d2 - d1).days)
                total_brl = dias * v['precio']
                total_pyg = total_brl * COTIZACION_DIA
                
                st.write(f"**Total {dias} días: R$ {total_brl} (Gs. {total_pyg:,.0f})**")
                
                foto = st.file_uploader("Foto Comprobante PIX", type=['jpg','png'], key=f"f{v['nombre']}")
                
                if st.button("CONFIRMAR ALQUILER", key=f"btn{v['nombre']}"):
                    if c_n and c_d and foto:
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT INTO reservas (cliente, ci, auto, inicio, fin, total, comprobante, nacionalidad, direccion, total_pyg) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                     (c_n, c_d, v['nombre'], d1, d2, total_brl, foto.read(), c_nac, c_dir, total_pyg))
                        conn.commit(); conn.close()
                        st.success("¡Reserva guardada!")
                        st.balloons()
                    else: st.error("Complete todos los campos y adjunte el pago.")

with t_adm:
    if st.text_input("Clave Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        reservas = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        for _, r in reservas.iterrows():
            with st.expander(f"Contrato #{r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | Total: Gs. {r['total_pyg']:,.0f}")
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                placa, color = (f_d[0], f_d[1]) if f_d else ("N/A", "N/A")
                
                pdf = generar_contrato_pdf(r, placa, color)
                st.download_button("📥 DESCARGAR CONTRATO PDF", pdf, f"Contrato_{r['cliente']}.pdf")
        conn.close()
