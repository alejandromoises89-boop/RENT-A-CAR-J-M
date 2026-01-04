import streamlit as st
from login import pantalla_acceso  # Importamos tu login premium
from app_functions import pantalla_principal  # Importamos la app de J&M

# 1. Configuración global (Se hereda a todos los archivos)
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")

# 2. El "Muro de Seguridad"
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# 3. Lógica de Swapping (Intercambio)
if not st.session_state.autenticado:
    # Solo carga el código del login. El resto de la app ni siquiera se ejecuta.
    pantalla_acceso()
else:
    # Una vez logueado, limpia la pantalla y carga la interfaz de usuario/admin.
    pantalla_principal()
