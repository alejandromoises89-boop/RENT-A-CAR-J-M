import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ALQUILER", layout="wide")

st.markdown("""
<style>
    .stApp { background: #1a1a1a; color: #D4AF37; }
    .card-auto { background: #262626; padding: 15px; border-radius: 10px; border: 1px solid #D4AF37; margin-bottom: 10px; }
    .btn-contact { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 5px; font-weight: bold; text-decoration: none; margin: 5px 0; }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_v9.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, tel_cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- 3. LÓGICA DE BLOQUEO ---
def verificar_disponibilidad(auto, t_inicio, t_fin):
    conn = sqlite3.connect('jm_v9.db')
    c = conn.cursor()
    # Bloquea si hay solapamiento de fechas y horas
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. SESIÓN Y LOGIN ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_data' not in st.session_state: st.session_state.u_data = {}

if not st.session_state.logueado:
    st.title("JM - Iniciar Sesión")
    correo = st.text_input("Usuario (Correo)")
    clave = st.text_input("Contraseña", type="password")
    
    col1, col2 = st.columns(2)
    if col1.button("Ingresar"):
        conn = sqlite3.connect('jm_v9.db')
        user = conn.execute("SELECT nombre, celular FROM usuarios WHERE correo=? AND password=?", (correo, clave)).fetchone()
        conn.close()
        if user:
            st.session_state.logueado = True
            st.session_state.u_data = {"nombre": user[0], "celular": user[1]}
            st.rerun()
        else: st.error("Error de acceso")

    if col2.button("Crear cuenta"):
        st.info("Formulario de registro rápido")
        with st.form("reg"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); c = st.text_input("WhatsApp (Ej: 0991...)")
            if st.form_submit_button("Registrar"):
                conn = sqlite3.connect('jm_v9.db')
                conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n, e, p, c))
                conn.commit(); conn.close(); st.success("Creado"); st.rerun()

# --- 5. APP PRINCIPAL ---
else:
    tab1, tab2 = st.tabs(["🚗 Vehículos", "📍 Ubicación"])

    with tab1:
        conn = sqlite3.connect('jm_v9.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, a in df.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{a["nombre"]}</h3><img src="{a["img"]}" width="200"></div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                f_i = c1.date_input("Fecha Entrega", key=f"fi{a['nombre']}")
                h_i = c1.time_input("Hora Entrega", time(9, 0), key=f"hi{a['nombre']}")
                f_d = c2.date_input("Fecha Devolución", key=f"fd{a['nombre']}")
                h_d = c2.time_input("Hora Devolución", time(9, 0), key=f"hd{a['nombre']}")
                
                dt_i = datetime.combine(f_i, h_i)
                dt_d = datetime.combine(f_d, h_d)

                if st.button(f"Reservar {a['nombre']}"):
                    if verificar_disponibilidad(a['nombre'], dt_i, dt_d):
                        total = max(1, (dt_d - dt_i).days) * a['precio']
                        conn = sqlite3.connect('jm_v9.db')
                        conn.execute("INSERT INTO reservas (cliente, tel_cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?,?)",
                                     (st.session_state.u_data['nombre'], st.session_state.u_data['celular'], a['nombre'], dt_i, dt_d, total))
                        conn.commit(); conn.close()
                        
                        st.success("¡Reserva confirmada!")
                        # WHATSAPP AL CLIENTE con los datos correspondientes
                        msg = (f"*JM ALQUILER - COMPROBANTE*\n\n"
                               f"Hola {st.session_state.u_data['nombre']},\n"
                               f"Auto: {a['nombre']}\n"
                               f"Entrega: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                               f"Devolución: {dt_d.strftime('%d/%m/%Y %H:%M')}\n"
                               f"Total: R$ {total}\n\n"
                               f"Realice el pago al PIX: 24510861818")
                        
                        # Se envía al número que el cliente registró
                        num_cliente = st.session_state.u_data['celular'].replace(" ", "").replace("-", "")
                        st.markdown(f'<a href="https://wa.me/{num_cliente}?text={urllib.parse.quote(msg)}" class="btn-contact wa">ENVIAR COMPROBANTE A MI WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("Vehículo no disponible en ese horario.")

    with tab2:
        st.subheader("Ubicación Exacta")
        # El mapa ahora usa un iFrame estándar de Google Maps para asegurar visualización
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.217316315354!2d-54.616641!3d-25.531114!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMxJzUyLjAiUyA1NMKwMzcnMDAuMCJX!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="400" style="border:1px solid #D4AF37;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">WhatsApp Corporativo: 0991681191</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-contact ig">Instagram Oficial</a>', unsafe_allow_html=True)