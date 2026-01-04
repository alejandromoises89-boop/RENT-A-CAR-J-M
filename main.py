import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO REFINADO ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
        
        .stApp { 
            background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); 
            color: white; 
        }
        
        /* Estilo Serigrafía Dorada Romana */
        .logo-romano {
            text-align: center;
            font-family: 'Playfair Display', serif;
            color: #D4AF37;
            font-size: 6rem;
            line-height: 1;
            margin-bottom: 0px;
            text-shadow: 2px 2px 0px rgba(0,0,0,0.2), 
                         0 0 15px rgba(212, 175, 55, 0.4);
            letter-spacing: 8px;
        }
        
        .sub-header-pro {
            text-align: center;
            color: #f0f0f0;
            font-size: 0.9rem;
            margin-bottom: 50px;
            letter-spacing: 5px;
            font-weight: 300;
            text-transform: uppercase;
            opacity: 0.8;
        }

        .card-auto { 
            background-color: white; 
            color: #1a1a1a; 
            padding: 25px; 
            border-radius: 15px; 
            border: 1px solid #D4AF37; 
            margin-bottom: 20px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA (SE MANTIENE IGUAL) ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, 
        tel TEXT, doc_tipo TEXT, doc_num TEXT, nacionalidad TEXT, direccion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, 
        monto_egreso REAL, inicio TEXT, fin TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. ACCESO (LOGIN CON DISEÑO CORREGIDO) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Logo único estilo Serigrafía Dorada
    st.markdown('<div class="logo-romano">JM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header-pro">Asociados Consultoría</div>', unsafe_allow_html=True)
    
    col_login = st.columns([1, 1.2, 1])[1]
    with col_login:
        modo = st.radio("Acceso", ["Ingresar", "Registrarse"], horizontal=True)
        
        if modo == "Ingresar":
            u_mail = st.text_input("Correo")
            u_pass = st.text_input("Clave", type="password")
            if st.button("ACCEDER AL SISTEMA"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios WHERE correo=? AND password=?", (u_mail, u_pass))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user
                    st.session_state.user_name = user[1]
                    st.rerun()
                else: st.error("❌ Credenciales inválidas")
        else:
            with st.form("registro_kyc"):
                st.write("### Registro de Nuevo Cliente")
                n = st.text_input("Nombre Completo")
                e = st.text_input("Correo")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("COMPLETAR REGISTRO"):
                    try:
                        conn = sqlite3.connect('jm_final_safe.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password) VALUES (?,?,?)", (n, e, p))
                        conn.commit()
                        st.success("✅ Cuenta creada.")
                    except: st.error("❌ Error: Correo ya registrado.")

# --- 4. PORTAL JM (ALQUILER / ADMIN / UBICACIÓN) ---
else:
    # Se mantiene toda la lógica de gestión de reservas, exportación y borrado anterior
    st.markdown(f'<h4 style="text-align:right; color:#D4AF37;">👤 {st.session_state.user_name}</h4>', unsafe_allow_html=True)
    # ... Resto del código de pestañas ...
