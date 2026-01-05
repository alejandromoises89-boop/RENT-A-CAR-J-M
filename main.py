import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ALQUILER V2", layout="wide")

# Estilos CSS (Incluye el nuevo botón de Instagram)
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    .card-auto { background-color: rgba(0,0,0,0.4); padding: 20px; border-left: 4px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; }
    .btn-ig { background-color: #E1306C; color: white !important; display: block; width: 100%; padding: 10px; text-align: center; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 10px; }
    .wa { background-color: #25D366; color: white !important; display: block; width: 100%; padding: 10px; text-align: center; border-radius: 5px; text-decoration: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE DISPONIBILIDAD ---
def verificar_disponibilidad(auto_nombre, f_inicio, f_fin):
    conn = sqlite3.connect('jm_final_google_v7.db')
    c = conn.cursor()
    # Busca reservas que se solapen con las fechas seleccionadas
    query = """
        SELECT COUNT(*) FROM reservas 
        WHERE auto = ? AND (
            (inicio <= ? AND fin >= ?) OR 
            (inicio <= ? AND fin >= ?) OR
            (? <= inicio AND ? >= fin)
        )
    """
    c.execute(query, (auto_nombre, f_inicio, f_inicio, f_fin, f_fin, f_inicio, f_fin))
    count = c.fetchone()[0]
    conn.close()
    return count == 0

# --- 3. INTERFAZ ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
    if st.button("🔴 INICIAR SESIÓN CON GOOGLE"):
        st.session_state.logueado = True
        st.session_state.u_name = "Usuario Google"
        st.rerun()
else:
    tabs = st.tabs(["🚗 Reservar", "📍 Ubicación y Redes", "📊 Admin"])

    with tabs[0]:
        st.subheader("Nuestra Flota")
        conn = sqlite3.connect('jm_final_google_v7.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()

        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{a["nombre"]}</h3><p>R$ {a["precio"]} / día</p></div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    d_i = st.date_input("Fecha Inicio", date.today(), key=f"d1_{a['nombre']}")
                with col2:
                    d_f = st.date_input("Fecha Fin", date.today() + timedelta(days=1), key=f"d2_{a['nombre']}")
                
                if st.button(f"Verificar y Reservar {a['nombre']}", key=f"btn_{a['nombre']}"):
                    if verificar_disponibilidad(a['nombre'], d_i, d_f):
                        # Guardar Reserva
                        total = (d_f - d_i).days * a['precio']
                        conn = sqlite3.connect('jm_final_google_v7.db')
                        conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)",
                                     (st.session_state.u_name, a['nombre'], d_i, d_f, total))
                        conn.commit(); conn.close()
                        
                        st.success("✅ ¡Fechas bloqueadas para ti!")
                        
                        # Mensaje WhatsApp Dinámico
                        msg = (f"Reserva JM: {a['nombre']}\nFechas: {d_i} al {d_f}\n"
                               f"Por favor, envía el comprobante al corporativo: 0991681191")
                        st.markdown(f'<a href="https://wa.me/595981000000?text={urllib.parse.quote(msg)}" class="wa">📲 RECIBIR DATOS PIX EN WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Lo sentimos, este vehículo ya está alquilado en esas fechas.")

    with tabs[1]:
        st.markdown("### Visítanos en Ciudad del Este")
        # Ubicación exacta de JM Automotores
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m13!1d3601.234!2d-54.6550001!3d-25.5011973!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685a483edf7dd%3A0xa8775cd7ad35f185!2sJM%20Automotores!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen=""></iframe>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### Síguenos en Redes")
        st.markdown('<a href="https://www.instagram.com/jmautomotorespy/" class="btn-ig">📸 INSTAGRAM CORPORATIVO</a>', unsafe_allow_html=True)
