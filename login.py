import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")

# --- 2. CONTROL DE SESIÓN (EL MURO) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'vista' not in st.session_state:
    st.session_state.vista = "login"

# --- 3. ESTILOS CSS (LOGIN VS APP) ---
def cargar_estilos_login():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle, #4A0404 0%, #1A0000 100%); }
        .title-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 50px; font-weight: bold; text-align: center; letter-spacing: 5px; }
        .subtitle-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 20px; text-align: center; text-transform: uppercase; }
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05)!important; border: 1px solid #D4AF37!important; color: #D4AF37!important; }
        .stButton>button { background-color: #600000!important; color: #D4AF37!important; border: 1px solid #D4AF37!important; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def cargar_estilos_app():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        .header-app { background-color: #4A0404; padding: 20px; color: #D4AF37; text-align: center; font-family: 'Times New Roman', serif; border-bottom: 5px solid #D4AF37; }
        .car-card { border: 1px solid #DDD; padding: 20px; border-radius: 10px; background: #FFF; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); text-align: center; }
        .stTabs [data-baseweb="tab-list"] { gap: 50px; }
        .stTabs [data-baseweb="tab"] { font-size: 20px; color: #4A0404; font-family: 'Times New Roman', serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCIONES DE LÓGICA ---
def validar_login(u, p):
    return u == "admin" and p == "2026"

# --- 5. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    cargar_estilos_login()
    st.markdown('<p class="title-jm">ACCESO A JM</p><p class="subtitle-jm">ALQUILER DE VEHÍCULOS</p>', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>🔒</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.session_state.vista == "login":
            with st.form("login"):
                user = st.text_input("USUARIO / TELÉFONO")
                pw = st.text_input("CONTRASEÑA", type="password")
                if st.form_submit_button("ENTRAR"):
                    if validar_login(user, pw):
                        st.session_state.autenticado = True
                        st.rerun()
                    else:
                        st.error("Acceso Denegado")
            
            if st.button("INGRESAR CON BIOMETRIA"): st.info("Escaneando...")
            c1, c2 = st.columns(2)
            if c1.button("CREAR CUENTA"): st.session_state.vista = "registro"; st.rerun()
            if c2.button("OLVIDÉ MI CLAVE"): st.session_state.vista = "recuperar"; st.rerun()

        elif st.session_state.vista == "registro":
            st.markdown("<h2 style='color:#D4AF37; text-align:center;'>REGISTRO</h2>", unsafe_allow_html=True)
            with st.form("reg"):
                st.text_input("Nombre Completo")
                st.text_input("Documento (CPF/RG/DNI)")
                st.text_input("WhatsApp")
                if st.form_submit_button("GUARDAR"): 
                    st.success("Registrado"); st.session_state.vista = "login"; st.rerun()
            if st.button("Volver"): st.session_state.vista = "login"; st.rerun()

# --- 6. PANTALLA PRINCIPAL (POS-LOGIN) ---
else:
    cargar_estilos_app()
    st.markdown('<div class="header-app"><h1>JM ASOCIADOS - PANEL DE GESTIÓN</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚗 CATÁLOGO", "📜 HISTORIAL", "📍 UBICACIÓN", "🛡️ ADMIN"])

    with tab1:
        st.subheader("Seleccione su Vehículo")
        # Aquí puedes colocar los contenedores de los autos con sus specs técnicas
        col_car1, col_car2 = st.columns(2)
        with col_car1:
            st.markdown("""
            <div class="car-card">
                <img src="https://i.ibb.co/Y7ZHY8kX/pngegg.png" width="250">
                <h3>Toyota Vitz 2012</h3>
                <p><b>Specs:</b> Automático | Nafta | 5 Pasajeros</p>
                <p>✅ Carta Verde | ✅ ABS | ✅ KM Libre (PY/BR/AR)</p>
                <h4 style="color:#D4AF37;">R$ 195 / día</h4>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Alquilar Vitz"):
                st.markdown("### Pagar con PIX: 24510861818")
                st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX")

    with tab3:
        st.subheader("Ubicación Estratégica")
        st.markdown('<iframe src="http://googleusercontent.com/maps.google.com/2" width="100%" height="400"></iframe>', unsafe_allow_html=True)

    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.autenticado = False
        st.rerun()
