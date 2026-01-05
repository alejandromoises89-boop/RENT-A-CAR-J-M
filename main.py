import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTÉTICA ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    input, [data-baseweb="input"] { background-color: rgba(0,0,0,0.7) !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; }
    .card-auto { background-color: rgba(0,0,0,0.4); padding: 20px; border-left: 4px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .btn-contact { display: block; width: 100%; padding: 10px; text-align: center; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 10px; border: 1px solid #D4AF37; }
    .wa { background-color: #25D366; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_name' not in st.session_state: st.session_state.u_name = ""
if 'u_celular' not in st.session_state: st.session_state.u_celular = ""

def init_db():
    conn = sqlite3.connect('jm_final_google_v7.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, celular TEXT, auto TEXT, inicio DATE, fin DATE, total REAL, contrato_blob BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, chapa TEXT, color TEXT, año TEXT)')
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "HHP-112", "Perla", "2009")
    ]
    c.execute("DELETE FROM flota")
    c.executemany("INSERT INTO flota VALUES (?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- 3. ACCESO CON GOOGLE (SIMULADO PROFESIONAL) ---
if not st.session_state.logueado:
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; padding:50px;'>", unsafe_allow_html=True)
    if st.button("🔴 INICIAR SESIÓN CON GOOGLE"):
        # Al usar Google, el sistema "toma" los datos de la cuenta automáticamente
        st.session_state.logueado = True
        st.session_state.u_name = "Usuario Google"
        st.session_state.u_celular = "595981000000" # Se inicializa para evitar errores
        st.success("Conectado con Google con éxito")
        st.rerun()
    
    st.markdown("---")
    if st.button("🔑 Acceso Administrador"):
        admin_pass = st.text_input("Contraseña Admin", type="password")
        if admin_pass == "8899":
            st.session_state.logueado = True
            st.session_state.u_name = "admin"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- 4. APLICACIÓN PRINCIPAL ---
    st.sidebar.write(f"Conectado como: {st.session_state.u_name}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logueado = False; st.rerun()

    tabs = st.tabs(["🚗 Flota", "📍 Ubicación", "🛡️ Admin Máster"])

    with tabs[0]:
        # Para que el WhatsApp funcione, pedimos el celular una sola vez si no lo tenemos
        if st.session_state.u_name != "admin" and st.session_state.u_celular == "595981000000":
            st.info("Complete su perfil de Google para continuar")
            st.session_state.u_celular = st.text_input("Confirme su número de WhatsApp (con código de país, ej: 595...)")

        conn = sqlite3.connect('jm_final_google_v7.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:300px;">
                    <h3>{a['nombre']}</h3>
                    <p>{a['color']} | {a['año']} | R$ {a['precio']} / día</p>
                </div>''', unsafe_allow_html=True)
                
                with st.expander("RESERVAR AHORA"):
                    d_i = st.date_input("Recogida", date.today(), key=f"i_{a['nombre']}")
                    d_f = st.date_input("Devolución", d_i + timedelta(days=1), key=f"f_{a['nombre']}")
                    total = (d_f - d_i).days * a['precio']
                    
                    if st.button("CONFIRMAR Y RECIBIR DATOS PIX", key=f"b_{a['nombre']}"):
                        conn = sqlite3.connect('jm_final_google_v7.db')
                        conn.execute("INSERT INTO reservas (cliente, celular, auto, inicio, fin, total) VALUES (?,?,?,?,?,?)",
                                     (st.session_state.u_name, st.session_state.u_celular, a['nombre'], d_i, d_f, total))
                        conn.commit(); conn.close()
                        
                        # MENSAJE AL WHATSAPP DEL CLIENTE CON INSTRUCCIONES
                        msg = (f"JM ALQUILER DE VEHÍCULOS 🚗\n\n"
                               f"Hola {st.session_state.u_name}, hemos recibido tu reserva:\n"
                               f"✅ Vehículo: {a['nombre']}\n"
                               f"📅 Fechas: {d_i} al {d_f}\n"
                               f"💰 Total: R$ {total}\n\n"
                               f"📍 PARA FINALIZAR EL PAGO (PIX):\n"
                               f"🔹 Llave: 24510861818\n"
                               f"🔹 Banco: Santander | Titular: Marina Baez\n\n"
                               f"⚠️ IMPORTANTE: Envía tu comprobante de pago ahora al número corporativo: 0991681191 para confirmar.")
                        
                        st.markdown(f'<a href="https://wa.me/{st.session_state.u_celular}?text={urllib.parse.quote(msg)}" class="btn-contact wa">📲 RECIBIR DATOS EN MI WHATSAPP</a>', unsafe_allow_html=True)

    with tabs[1]:
        # MAPA FIJO J&M ASOCIADOS
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234!2d-54.61!3d-25.51!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68f7f95f8f37d%3A0x936570e74f46f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

    with tabs[2]:
        if st.session_state.u_name == "admin":
            st.markdown("### PANEL DE CONTROL")
            conn = sqlite3.connect('jm_final_google_v7.db')
            df_r = pd.read_sql_query("SELECT * FROM reservas", conn); conn.close()
            
            if not df_r.empty:
                st.metric("Total Recaudado", f"R$ {df_r['total'].sum():,.2f}")
                st.plotly_chart(px.pie(df_r, values='total', names='auto', title="Ventas por Auto"))
                st.dataframe(df_r)
                
                pin = st.text_input("PIN Maestro", type="password")
                if st.button("LIMPIAR REGISTROS"):
                    if pin == "0000":
                        conn = sqlite3.connect('jm_final_google_v7.db'); conn.execute("DELETE FROM reservas"); conn.commit(); conn.close()
                        st.success("Borrado"); st.rerun()