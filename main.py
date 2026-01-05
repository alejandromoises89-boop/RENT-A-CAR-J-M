import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA FINAL", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 10px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 50px; margin-bottom: 0; }
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: rgba(255,255,255,0.05) !important; color: white !important; }
        div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; border-radius: 12px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .card-auto { background: white; color: black; padding: 15px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 20px; }
        .resena-card { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 3px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_v11.db')
    c = conn.cursor()
    # Flota
    c.execute('''CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, ano TEXT)''')
    # Reservas (Incluyendo horas)
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini TEXT, h_ini TEXT, f_fin TEXT, h_fin TEXT, cliente TEXT, monto REAL, doc TEXT)''')
    # Usuarios y Reseñas
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, password TEXT, nombre TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, usuario TEXT, comentario TEXT, estrellas INTEGER)''')
    
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
            ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano) VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def verificar_bloqueo(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_final_v11.db')
    res = conn.execute("SELECT * FROM reservas WHERE auto_id = ? AND NOT (f_fin < ? OR f_ini > ?)", (auto_id, str(f_ini), str(f_fin))).fetchone()
    conn.close()
    return res is None

def generar_pdf(d, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Times", '', 10)
    pdf.ln(5)
    clausulas = f"""Este contrato certifica que el cliente {d['nombre']} (Doc: {d['doc']}) alquila el {d['auto']} (Chapa: {d['chapa']}).

DETALLES DE ENTREGA Y DEVOLUCIÓN:
- Entrega: {d['f1']} a las {d['h1']} hs.
- Devolución: {d['f2']} a las {d['h2']} hs.

12 CLÁUSULAS LEGALES INTEGRADAS:
1. El arrendatario asume responsabilidad civil y penal. 2. Depósito de garantía obligatorio. 
3. Uso exclusivo Mercosur. 4. Devolución en iguales condiciones de higiene y combustible..."""
    pdf.multi_cell(0, 6, clausulas)
    if firma_img:
        firma_img.save("temp_f.png")
        pdf.image("temp_f.png", x=140, y=pdf.get_y()+5, w=40)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. INICIO ---
init_db()
aplicar_estilos_premium()

if 'logged' not in st.session_state: st.session_state.logged = False

if not st.session_state.logged:
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO JM ASOCIADOS</p></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["ENTRAR",
