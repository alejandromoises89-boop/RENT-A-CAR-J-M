import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import base64

# --- 1. CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #1a0404 0%, #000000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 4.5rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.5rem; margin-bottom: 40px; letter-spacing: 4px; font-weight: 300; }
        .card-auto { background-color: #ffffff; color: #1a1a1a; padding: 25px; border-radius: 20px; border-left: 8px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
        .historial-card { background-color: #262626; padding: 15px; border-radius: 15px; border: 1px solid #444; margin-bottom: 10px; }
        .btn-interactivo { display: inline-flex; align-items: center; justify-content: center; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin: 5px; color: white !important; transition: 0.3s; }
        .btn-wa { background-color: #25D366; }
        .btn-ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #bc1888); }
        .logout-box { text-align: center; margin-top: 80px; padding-bottom: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_auto_system.db')
    c = conn.cursor()
    # Usuarios con KYC completo
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, 
        doc_tipo TEXT, doc_num TEXT, tel TEXT, direccion TEXT)''')
    # Reservas con balance financiero
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, monto_egreso REAL,
        inicio TEXT, fin TEXT, timestamp TEXT)''')
    # Reseñas
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER)''')
    conn.commit()
    conn.close()

# Función para verificar solapamiento de fechas y autos
def verificar_bloqueo(auto, inicio, fin):
    conn = sqlite3.connect('jm_auto_system.db')
    c = conn.cursor()
    # Lógica: No debe haber ninguna reserva donde las fechas se crucen
    c.execute('''SELECT * FROM reservas WHERE auto=? AND NOT (fin < ? OR inicio > ?)''', 
              (auto, inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None # True si está disponible

init_db()

# --- 3. GESTIÓN DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN REORGANIZADO (Minimalista) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ALQUILER DE AUTOS</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        opcion = st.radio("Acceso al Portal", ["Ingresar", "Registrarse como Nuevo Cliente"], horizontal=
