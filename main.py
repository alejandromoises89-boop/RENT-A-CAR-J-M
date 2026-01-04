import streamlit as st
import pandas as pd

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="J&M ASOCIADOS - Login", layout="centered")

# --- 2. LÓGICA DE SESIÓN (EL BLINDAJE) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 3. ESTILO CSS "ESTUDIO PRESTIGE" ---
st.markdown("""
<style>
    /* Fondo Degradado Bordó a Negro */
    .stApp {
        background: radial-gradient(circle, #600000 0%, #1a0000 100%);
    }

    /* Contenedor del Login */
    .login-box {
        text-align: center;
        padding: 40px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 20px;
    }

    /* Logo J&M Estilo Serigrafía Cursiva */
    .logo-jm {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 70px;
        color: #D4AF37;
        text-shadow: 0px 0px 15px rgba(212, 175, 55, 0.6);
        margin-bottom: 0px;
    }

    .slogan {
        color: #D4AF37;
        font-family: 'Garamond', serif;
        letter-spacing: 4px;
        font-size: 14px;
        margin-top: -10px;
        text-transform: uppercase;
    }

    /* Candado Dorado */
    .lock-icon {
        font-size: 40px;
        color: #D4AF37;
        margin: 20px 0;
    }

    /* Inputs Traslúcidos con Borde Dorado Fino */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #D4AF37 !important;
        color: #D4AF37 !important;
        border-radius: 5px !important;
        text-align: center;
    }

    /* Botón ENTRAR Bordó Intenso */
    .stButton>button {
        background-color: #400000 !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
        font-weight: bold !important;
        font-size: 18px !important;
        width: 100%;
        height: 50px;
        border-radius: 5px !important;
        margin-top: 20px;
    }
    
    .stButton>button:hover {
        background-color: #600000 !important;
        box-shadow: 0px 0px 15px rgba(212, 175, 55, 0.4);
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# --- 4. CUERPO DEL LOGIN ---
def pantalla_login():
    with st.container():
        # Encabezado
        st.markdown('<h1 class="logo-jm">J&M</h1>', unsafe_allow_html=True)
        st.markdown('<p class="slogan">Asociados - Alquiler de Vehículos</p>', unsafe_allow_html=True)
        
        # Imagen de autos (opcional, si tienes una URL de imagen real puedes ponerla aquí)
        # st.image("URL_DE_TU_IMAGEN_AUTOS", use_column_width=True)
        
        # Icono de Seguridad
        st.markdown('<div class="lock-icon">🔒</div>', unsafe_allow_html=True)

        # Formulario Blindado
        with st.form("login_form"):
            usuario = st.text_input("USUARIO / TELÉFONO", placeholder="Ej: 0991681191")
            clave = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            
            submit = st.form_submit_button("ENTRAR")
            
            if submit:
                # AQUÍ defines tu usuario y clave maestros
                if usuario == "admin" and clave == "2026":
                    st.session_state.autenticado = True
                    st.success("Acceso concedido. Cargando sistema...")
                    st.rerun()
                elif usuario == "" or clave == "":
                    st.warning("Por favor, complete todos los campos.")
                else:
                    st.error("Credenciales incorrectas. Intente de nuevo.")

# --- 5. CONTROL DE FLUJO ---
if not st.session_state.autenticado:
    pantalla_login()
else:
    # Una vez que entra, aquí va el resto de tu App
    st.markdown('<h2 style="color:#D4AF37;">Bienvenido al Panel de Control J&M</h2>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # Aquí seguirían tus pestañas (Historial, Panel Admin, etc.)
    # ...
