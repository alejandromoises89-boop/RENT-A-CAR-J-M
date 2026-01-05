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
    .btn-contact { display: block; width: 100%; padding: 12px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; border: 1px solid #D4AF37; }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS E INICIALIZACIÓN ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "login"
if 'u_name' not in st.session_state: st.session_state.u_name = ""

def init_db():
    conn = sqlite3.connect('jm_final_v8.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, total REAL, contrato_blob BLOB)')
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

# --- 3. LÓGICA DE BLOQUEO DE FECHAS ---
def verificar_disponibilidad(auto, f_inicio, f_fin):
    conn = sqlite3.connect('jm_final_v8.db')
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, f_inicio, f_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. SISTEMA DE ACCESO (USUARIO/CONTRASEÑA) ---
if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.markdown("<h2 style='text-align:center;'>JM ACCESO</h2>", unsafe_allow_html=True)
        correo = st.text_input("Correo Electrónico")
        clave = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if correo == "admin@jm.com" and clave == "8899":
                st.session_state.logueado = True; st.session_state.u_name = "admin"; st.rerun()
            else:
                conn = sqlite3.connect('jm_final_v8.db')
                user = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (correo, clave)).fetchone()
                conn.close()
                if user:
                    st.session_state.logueado = True; st.session_state.u_name = user[0]; st.rerun()
                else: st.error("Usuario o contraseña incorrectos")
        
        col1, col2 = st.columns(2)
        if col1.button("Crear Cuenta"): st.session_state.pagina = "registro"; st.rerun()
        if col2.button("Olvidé mi contraseña"): st.info("Contacte al 0991681191 para resetear"); st.rerun()

    elif st.session_state.pagina == "registro":
        st.markdown("### Registro de Usuario")
        with st.form("reg"):
            nom = st.text_input("Nombre Completo"); em = st.text_input("Correo"); ps = st.text_input("Contraseña", type="password"); cel = st.text_input("WhatsApp")
            if st.form_submit_button("Registrarse"):
                conn = sqlite3.connect('jm_final_v8.db')
                conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (nom, em, ps, cel))
                conn.commit(); conn.close()
                st.success("Cuenta creada"); st.session_state.pagina = "login"; st.rerun()
        if st.button("Volver"): st.session_state.pagina = "login"; st.rerun()

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    tabs = st.tabs(["🚗 Flota", "📍 Ubicación", "🛡️ Admin Máster"])

    with tabs[0]:
        conn = sqlite3.connect('jm_final_v8.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:300px; border-radius:10px;">
                    <h3>{a['nombre']}</h3>
                    <p>{a['color']} | {a['año']} | R$ {a['precio']} / día</p>
                </div>''', unsafe_allow_html=True)
                
                with st.expander("RESERVAR VEHÍCULO"):
                    d_i = st.date_input("Recogida", date.today(), key=f"i_{a['nombre']}")
                    d_f = st.date_input("Devolución", d_i + timedelta(days=1), key=f"f_{a['nombre']}")
                    
                    if st.button("CONFIRMAR RESERVA", key=f"b_{a['nombre']}"):
                        if verificar_disponibilidad(a['nombre'], d_i, d_f):
                            total = (d_f - d_i).days * a['precio']
                            conn = sqlite3.connect('jm_final_v8.db')
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)",
                                         (st.session_state.u_name, a['nombre'], d_i, d_f, total))
                            conn.commit(); conn.close()
                            
                            st.success("✅ ¡Reserva Exitosa! Fechas bloqueadas.")
                            msg = (f"Reserva JM: {a['nombre']}\nTotal: R$ {total}\n"
                                   f"PIX: 24510861818 (Santander - Marina Baez)\n"
                                   f"Enviar comprobante al corporativo 0991681191.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-contact wa">📤 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)
                        else:
                            st.error("❌ El vehículo ya está reservado en estas fechas.")

    with tabs[1]:
        st.markdown("### Nuestra Ubicación")
        # Previsualización del mapa (Responsive)
        st.markdown('<iframe src="googleusercontent.com/maps.google.com/65" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        
        # Botones de contacto oficiales solicitados
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">💬 WhatsApp Corporativo 0991681191</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)

    with tabs[2]:
        if st.session_state.u_name == "admin":
            st.markdown("### PANEL FINANCIERO")
            conn = sqlite3.connect('jm_final_v8.db')
            df_r = pd.read_sql_query("SELECT * FROM reservas", conn); conn.close()
            if not df_r.empty:
                st.metric("Total Ingresos", f"R$ {df_r['total'].sum():,.2f}")
                st.plotly_chart(px.bar(df_r, x='auto', y='total', color='auto', title="Ventas por Vehículo"))
                st.dataframe(df_r)
                if st.text_input("PIN", type="password") == "0000":
                    if st.button("LIMPIAR BASE DE DATOS"):
                        conn = sqlite3.connect('jm_final_v8.db'); conn.execute("DELETE FROM reservas"); conn.commit(); conn.close(); st.rerun()