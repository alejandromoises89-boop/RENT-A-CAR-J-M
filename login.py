import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")

# --- 2. GESTIÓN DE ESTADOS (CONTROL TOTAL) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'vista_login' not in st.session_state:
    st.session_state.vista_login = "inicio"
if 'reservas_db' not in st.session_state:
    st.session_state.reservas_db = pd.DataFrame(columns=["ID", "Cliente", "Auto", "Inicio", "Fin", "Total", "Estado"])

# --- 3. ESTILOS CSS ---

def cargar_estilos_login():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle, #4A0404 0%, #1A0000 100%); }
        .title-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 50px; font-weight: bold; text-align: center; letter-spacing: 5px; margin-bottom:0px; }
        .subtitle-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 18px; text-align: center; text-transform: uppercase; letter-spacing: 3px; }
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05)!important; border: 1px solid #D4AF37!important; color: #D4AF37!important; }
        .stButton>button { background-color: #600000!important; color: #D4AF37!important; border: 1px solid #D4AF37!important; font-family: 'Times New Roman', serif; font-weight: bold; width: 100%; border-radius: 5px; }
        .stButton>button:hover { background-color: #800000!important; border: 1px solid #FFF!important; }
    </style>
    """, unsafe_allow_html=True)

def cargar_estilos_app():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        .header-app { background-color: #4A0404; padding: 20px; color: #D4AF37; text-align: center; font-family: 'Times New Roman', serif; border-bottom: 5px solid #D4AF37; }
        .car-card { border: 1px solid #DDD; padding: 20px; border-radius: 10px; background: #FFF; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); text-align: center; }
        .stTabs [data-baseweb="tab-list"] { gap: 30px; }
        .stTabs [data-baseweb="tab"] { font-size: 18px; color: #4A0404; font-family: 'Times New Roman', serif; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE DISPONIBILIDAD ---
def verificar_disponibilidad(auto, inicio, fin):
    df = st.session_state.reservas_db
    conflictos = df[df['Auto'] == auto]
    for _, reserva in conflictos.iterrows():
        if not (fin < reserva['Inicio'] or inicio > reserva['Fin']):
            return False
    return True

# --- 5. INTERFAZ DE LOGIN (ESTÉTICA PREMIUM) ---
if not st.session_state.autenticado:
    cargar_estilos_login()
    st.markdown('<p class="title-jm">ACCESO A JM</p><p class="subtitle-jm">ALQUILER DE VEHÍCULOS</p>', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>🔒</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.session_state.vista_login == "inicio":
            with st.form("login_form"):
                u = st.text_input("USUARIO / TELÉFONO")
                p = st.text_input("CONTRASEÑA", type="password")
                if st.form_submit_button("ENTRAR"):
                    if u == "admin" and p == "2026":
                        st.session_state.autenticado = True
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
            
            if st.button("INGRESAR CON BIOMETRÍA"):
                st.info("Iniciando escaneo biométrico...")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("CREAR CUENTA"):
                    st.session_state.vista_login = "registro"
                    st.rerun()
            with c2:
                if st.button("OLVIDÉ MI CLAVE"):
                    st.session_state.vista_login = "recuperar"
                    st.rerun()
            
            st.divider()
            if st.button("SALIR DEL SISTEMA"):
                st.stop()

        elif st.session_state.vista_login == "registro":
            st.markdown("<h3 style='color:#D4AF37; text-align:center;'>REGISTRO DE NUEVO CLIENTE</h3>", unsafe_allow_html=True)
            with st.form("reg"):
                st.text_input("Nombre Completo")
                st.text_input("Documento (DNI/RG/CPF)")
                st.text_input("WhatsApp")
                st.text_input("Contraseña Nueva", type="password")
                if st.form_submit_button("REGISTRAR Y GUARDAR"):
                    st.success("Cuenta creada exitosamente")
                    st.session_state.vista_login = "inicio"
                    st.rerun()
            if st.button("VOLVER"):
                st.session_state.vista_login = "inicio"
                st.rerun()

        elif st.session_state.vista_login == "recuperar":
            st.markdown("<h3 style='color:#D4AF37; text-align:center;'>RECUPERAR CONTRASEÑA</h3>", unsafe_allow_html=True)
            st.text_input("Ingrese su correo o teléfono registrado")
            if st.button("ENVIAR CÓDIGO"):
                st.success("Código enviado satisfactoriamente")
            if st.button("VOLVER"):
                st.session_state.vista_login = "inicio"
                st.rerun()
