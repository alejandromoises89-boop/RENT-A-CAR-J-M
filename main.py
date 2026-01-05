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

# --- 1. CONFIGURACIÓN E IDENTIDAD VISUAL JM ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA OFICIAL", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        /* Fondo degradado Bordó */
        .stApp { 
            background: linear-gradient(180deg, #5e0000 0%, #1a0000 100%); 
            color: white; 
        }
        
        /* Encabezado Dorado Tipografía Romana */
        .header-jm { text-align: center; padding: 10px; }
        .header-jm h1 { 
            color: #D4AF37; 
            font-family: 'Times New Roman', serif; 
            font-size: 70px; 
            margin-bottom: -15px;
            font-weight: normal;
        }
        .header-jm p { 
            color: #D4AF37; 
            font-size: 22px; 
            font-style: italic;
        }

        /* Inputs con bordes dorados finos */
        .stTextInput>div>div>input {
            border: 1px solid #D4AF37 !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: white !important;
            border-radius: 8px !important;
        }
        
        /* Botón de Entrada destacado */
        div.stButton > button {
            background-color: #8B0000 !important;
            color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important;
            font-weight: bold !important;
            width: 100%;
            height: 45px;
            border-radius: 5px;
            text-transform: uppercase;
        }

        /* Pestañas Blancas con Hover Bordó */
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 8px; padding: 4px; }
        .stTabs [data-baseweb="tab"] { color: #000 !important; font-weight: bold; }
        .stTabs [data-baseweb="tab"]:hover { border-bottom: 3px solid #800000 !important; }
        
        /* Cards de Catálogo elegante */
        .card-auto {
            background: #ffffff;
            color: #333;
            padding: 20px;
            border-radius: 12px;
            border-left: 8px solid #D4AF37;
            margin-bottom: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }
        
        .btn-social {
            display: inline-block;
            padding: 10px;
            border-radius: 8px;
            color: white !important;
            font-weight: bold;
            text-align: center;
            width: 100%;
            margin-top: 10px;
            text-decoration: none;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_database_v5.db')
    c = conn.cursor()
    # Flota con datos técnicos
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, 
                  chasis TEXT, chapa TEXT, color TEXT, ano TEXT, modelo TEXT)''')
    # Reservas para bloqueo de fechas
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini DATE, f_fin DATE, cliente TEXT, total REAL)''')
    # Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (email TEXT PRIMARY KEY, nombre TEXT, tel TEXT, doc TEXT, direccion TEXT)''')
    
    if c.execute("SELECT count(*) FROM flota").fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://i.postimg.cc/9Fm8mXmS/tucson.png", "Disponible", "TUC-99388", "AA-123-ZZ", "Gris Plata", "2012", "GL"),
            ("Toyota Vitz Blanco", 195.0, "https://i.postimg.cc/qM6m4pP2/vitz-blanco.png", "Disponible", "VTZ-00122", "BCC-445", "Blanco", "2010", "RS"),
            ("Toyota Vitz Negro", 195.0, "https://i.postimg.cc/mD8T7m8r/vitz-negro.png", "Disponible", "VTZ-99887", "XAM-990", "Negro", "2011", "Style"),
            ("Toyota Voxy", 240.0, "https://i.postimg.cc/vH8vM8Hn/voxy.png", "Disponible", "VOX-55667", "HHP-112", "Perla", "2009", "ZS")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano, modelo) VALUES (?,?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def check_disponibilidad(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_database_v5.db')
    res = conn.execute("SELECT * FROM reservas WHERE auto_id=? AND NOT (f_fin < ? OR f_ini > ?)", (auto_id, f_ini, f_fin)).fetchone()
    conn.close()
    return res is None

# --- 3. GENERADOR DE CONTRATO JM (12 CLÁUSULAS) ---
def generar_contrato_pdf(datos, firma_path=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 5, "JM CONSULTORA-CONTABILIDAD-JURIDICA-SERVICIOS MIGRACIONES", ln=True)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"CDE, {date.today().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    
    pdf.set_font("Times", '', 9)
    # Bloque de datos y cláusulas resumidas para el PDF
    texto = f"""
    ARRENDADOR: J&M ASOCIADOS | CI: 1.008.110-0
    ARRENDATARIO: {datos['cliente']} | DOC: {datos['doc']} | TEL: {datos['tel']}
    
    PRIMERA: El vehículo {datos['auto']} (Chapa: {datos['chapa']}, Chasis: {datos['chasis']}) se entrega en perfecto estado.
    SEGUNDA: Duración desde {datos['f_ini']} {datos['h_ini']}hs hasta {datos['f_fin']} {datos['h_fin']}hs.
    TERCERA: Precio R$ {datos['total_brl']} / Gs. {datos['total_pyg']:,.0f}.
