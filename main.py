import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO JM PREMIUM ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap');
        
        .stApp { 
            background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); 
            color: white; 
        }
        
        /* LOGO SERIGRAFÍA DORADA CLÁSICA */
        .logo-container {
            text-align: center;
            padding: 40px 0;
        }
        
        .logo-jm {
            font-family: 'Cinzel', serif;
            color: #D4AF37;
            font-size: 7rem;
            line-height: 0.8;
            margin: 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .logo-sub {
            font-family: 'Cinzel', serif;
            color: #D4AF37;
            font-size: 1.2rem;
            letter-spacing: 10px;
            text-transform: uppercase;
            margin-top: 10px;
            font-weight: 400;
        }

        /* Estilo de los inputs y botones */
        .stTextInput>div>div>input {
            background-color: rgba(255,255,255,0.05) !important;
            color: white !important;
            border: 1px solid #D4AF37 !important;
        }
        
        .stButton>button {
            background-color: #D4AF37 !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 5px !important;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS (Persistencia de Usuarios) ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    # Tabla de usuarios con todos los campos necesarios para que no vuelvan a registrarse
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, 
        nombre TEXT, 
        correo TEXT UNIQUE, 
        password TEXT, 
        tel TEXT, 
        doc_tipo TEXT, 
        doc_num TEXT, 
        nacionalidad TEXT, 
        direccion TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, 
        cliente TEXT, 
        auto TEXT, 
        monto_ingreso REAL, 
        monto_egreso REAL, 
        inicio TEXT, 
        fin TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE ACCESO ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Encabezado Formal
    st.markdown("""
        <div class="logo-container">
            <div class="logo-jm">JM</div>
            <div class="logo-sub">Alquiler de Autos</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        tab_login, tab_reg = st.tabs(["INGRESAR", "REGISTRARSE"])
        
        with tab_login:
            st.write("### Acceso Clientes")
            u_email = st.text_input("Correo Electrónico", key="login_email")
            u_pass = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.button("ENTRAR"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios WHERE correo=? AND password=?", (u_email, u_pass))
                user = c.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user # Aquí se guardan todos los datos registrados
                    st.session_state.user_name = user[1]
                    st.success(f"Bienvenido de nuevo, {user[1]}")
                    st.rerun()
                else:
                    st.error("Credenciales no encontradas. Si es nuevo, por favor regístrese.")
        
        with tab_reg:
            st.write("### Registro Único")
            with st.form("form_registro"):
                nombre = st.text_input("Nombre Completo")
                email = st.text_input("Correo")
                tel = st.text_input("WhatsApp (ej: 0981...)")
                passw = st.text_input("Crear Contraseña", type="password")
                
                st.write("---")
                doc_t = st.selectbox("Documento", ["C.I.", "CPF", "Pasaporte"])
                doc_n = st.text_input("Número de Documento")
                
                if st.form_submit_button("REGISTRAR Y GUARDAR DATOS"):
                    if nombre and email and passw:
                        try:
                            conn = sqlite3.connect('jm_final_safe.db')
                            conn.cursor().execute("""
                                INSERT INTO usuarios (nombre, correo, password, tel, doc_tipo, doc_num) 
                                VALUES (?,?,?,?,?,?)""", (nombre, email, passw, tel, doc_t, doc_n))
                            conn.commit()
                            conn.close()
                            st.success("¡Datos guardados! Ya puede ingresar con su correo.")
                        except sqlite3.IntegrityError:
                            st.error("Este correo ya está registrado.")
                    else:
                        st.warning("Complete los campos principales.")

# --- 4. PORTAL INTERNO ---
else:
    st.markdown(f'<h4 style="text-align:right; color:#D4AF37; font-family:Cinzel;">👤 {st.session_state.user_name}</h4>', unsafe_allow_html=True)
    
    # Aquí irían tus pestañas de Alquiler, Historial, Ubicación y Admin
    # ... (Se mantiene la lógica anterior de alquiler y administración) ...
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()
