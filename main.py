import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ALQUILER", layout="wide")

# --- ESTILOS REFORZADOS (BOTONES SIEMPRE VISIBLES) ---
st.markdown("""
<style>
    .stApp { background: #4A0404; color: #D4AF37; }
    .card-auto { background: rgba(0,0,0,0.5); padding: 15px; border: 1px solid #D4AF37; border-radius: 10px; margin: 10px 0; }
    /* Botones de contacto */
    .btn-wa { background-color: #25D366 !important; color: white !important; padding: 10px; border-radius: 5px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    .btn-ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important; color: white !important; padding: 10px; border-radius: 5px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS (PERSISTENTE) ---
def init_db():
    conn = sqlite3.connect('jm_final_database.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- LÓGICA DE REGISTRO MEJORADA ---
def registrar_usuario(n, e, p):
    try:
        with sqlite3.connect('jm_final_database.db') as db:
            db.execute("INSERT INTO usuarios (nombre, correo, password) VALUES (?, ?, ?)", (n, e, p))
            db.commit()
        return True
    except:
        return False

# --- INTERFAZ DE REGISTRO ---
if 'logueado' not in st.session_state:
    st.title("Registro de Usuario Nuevo")
    with st.form("registro"):
        nombre = st.text_input("Nombre Completo")
        correo = st.text_input("Correo Electrónico")
        passw = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Crear Cuenta"):
            if registrar_usuario(nombre, correo, passw):
                st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
            else:
                st.error("El correo ya está registrado o hay un error en la base de datos.")

# --- SECCIÓN DEL MAPA E INSTAGRAM (MODIFICADO) ---
st.header("📍 Nuestra Ubicación")
# Iframe oficial de J&M ASOCIADOS Consultoria
map_iframe = '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.916174880537!2d-54.61297472477833!3d-25.507856377508017!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68fbd65f8f4ed%3A0x936570e64fc771b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1715634567890!5m2!1ses!2spy" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>'
st.markdown(map_iframe, unsafe_allow_html=True)

st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-ig">Ir a Instagram Oficial</a>', unsafe_allow_html=True)

# --- BOTÓN WHATSAPP CORPORATIVO ---
def mostrar_boton_whatsapp(auto, total):
    mensaje = f"Hola JM ALQUILER, deseo confirmar mi reserva del {auto}. Total: {total}. Adjunto comprobante."
    url = f"https://wa.me/595991681191?text={urllib.parse.quote(mensaje)}"
    st.markdown(f'<a href="{url}" class="btn-wa">Enviar Comprobante al 0991681191</a>', unsafe_allow_html=True)

# Ejemplo de uso en la reserva
if st.button("Confirmar Alquiler"):
    # Aquí iría tu lógica de verificación de fechas
    st.warning("⚠️ Este vehículo no está disponible en las fechas seleccionadas.")
    # Si estuviera disponible:
    mostrar_boton_whatsapp("Toyota Vitz", "195.000 Gs")