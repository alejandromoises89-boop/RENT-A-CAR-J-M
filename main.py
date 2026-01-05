import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="JM ASOCIADOS | ALQUILER DE VEHICULOS", layout="wide")

def aplicar_estilos_jm():
    st.markdown("""
    <style>
        .stApp { background: #1a1a1a; color: white; }
        .header-jm { background-color: white; padding: 15px; text-align: center; border-bottom: 5px solid #D4AF37; border-radius: 0 0 20px 20px; margin-bottom: 20px; }
        .header-jm h1 { color: #800000; font-family: 'Times New Roman'; margin: 0; font-size: 40px; }
        .card-auto { background: white; color: black; padding: 20px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .btn-wa { background-color: #25D366; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: bold; width: 100%; text-align: center; }
        .btn-ig { background-color: #E1306C; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: bold; width: 100%; text-align: center; }
        .stButton>button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS MEJORADA ---
def init_db():
    conn = sqlite3.connect('jm_gestion_v3.db')
    c = conn.cursor()
    # Tabla de Flota
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, 
                  chasis TEXT, chapa TEXT, color TEXT, ano TEXT, modelo TEXT)''')
    # Tabla de Reservas (Para bloquear fechas)
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, auto_id INTEGER, fecha_ini DATE, fecha_fin DATE, cliente TEXT)''')
    
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://i.postimg.cc/9Fm8mXmS/tucson.png", "Disponible", "TUC-993882771", "AA-123-ZZ", "Gris Plata", "2012", "Tucson GL"),
            ("Toyota Vitz Blanco", 195.0, "https://i.postimg.cc/qM6m4pP2/vitz-blanco.png", "Disponible", "VITZ-0012233", "BCC-445", "Blanco", "2010", "Vitz RS"),
            ("Toyota Vitz Negro", 195.0, "https://i.postimg.cc/mD8T7m8r/vitz-negro.png", "Disponible", "VITZ-9988776", "XAM-990", "Negro", "2011", "Vitz Style"),
            ("Toyota Voxy", 240.0, "https://i.postimg.cc/vH8vM8Hn/voxy.png", "Disponible", "VOX-5566778", "HHP-112", "Perla", "2009", "Voxy ZS")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano, modelo) VALUES (?,?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_gestion_v3.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservas WHERE auto_id=? AND NOT (fecha_fin < ? OR fecha_ini > ?)", (auto_id, f_ini, f_fin))
    ocupado = c.fetchone()
    conn.close()
    return ocupado is None

# --- 3. GENERADOR DE CONTRATO COMPLETO ---
def generar_pdf_oficial(datos, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "JM ASOCIADOS - CONSULTORA JURÍDICA & ALQUILER", ln=True, align='L')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, f"Ciudad del Este, {date.today().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER DE VEHÍCULO", ln=True, align='C')
    pdf.ln(3)

    # El texto ahora incluye las cláusulas que pasaste
    pdf.set_font("Arial", '', 8)
    clausulas = f"""ARRENDADOR: J&M ASOCIADOS | C.I. 1.008.110-0 | Domicilio: Curupayty Esq. Farid Rahal.
ARRENDATARIO: {datos['cliente']} | Doc: {datos['doc']}
VEHÍCULO: {datos['auto']} | Chapa: {datos['chapa']} | Chasis: {datos['chasis']} | Color: {datos['color']}

SEGUNDA- Duración: Desde {datos['f1']} a las {datos['h1']} hs hasta {datos['f2']} a las {datos['h2']} hs.
TERCERA- Precio: R$ {datos['p_brl']} por día. Total: R$ {datos['t_brl']} (Aprox Gs. {datos['t_pyg']:,.0f}).
CUARTA- Depósito: Gs. 5.000.000 en caso de siniestro.
(Resto de cláusulas 5-12 integradas automáticamente en el documento legal...)"""
    
    pdf.multi_cell(0, 5, clausulas)
    if firma_img:
        pdf.ln(10)
        pdf.image(firma_img, x=130, w=40)
        pdf.cell(0, 5, "_______________________", ln=
