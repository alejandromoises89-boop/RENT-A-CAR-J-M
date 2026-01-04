import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JM Alquiler de Autos", layout="wide")

    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        html { scroll-behavior: smooth; }
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; margin-bottom: 5px; font-size: 3rem; font-weight: bold; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 20px; font-weight: 300; letter-spacing: 2px; }
        .cotizacion-texto { text-align: center; color: #D4AF37; font-weight: bold; border: 1px solid #D4AF37; padding: 10px; border-radius: 10px; background: rgba(255,255,255,0.05); margin-bottom: 15px; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        
        /* Botones Redes Sociales y Acción */
        .btn-notif { display: flex; align-items: center; justify-content: center; padding: 12px; border-radius: 10px; text-decoration: none !important; font-weight: bold; margin-top: 8px; width: 100%; border: none; transition: 0.3s; }
        .btn-whatsapp { background-color: #25D366; color: white !important; }
        .btn-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white !important; }
        .btn-email { background-color: #D4AF37; color: black !important; }
        .btn-icon { margin-right: 10px; font-size: 22px; }
        .btn-notif:hover { transform: scale(1.02); opacity: 0.9; }
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


