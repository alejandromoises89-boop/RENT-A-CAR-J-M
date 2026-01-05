import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime, date, timedelta
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA DE ALQUILER", layout="wide")

if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'role' not in st.session_state: st.session_state.role = "user"
if 'auto_sel' not in st.session_state: st.session_state.auto_sel = None

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, whatsapp TEXT, auto TEXT, inicio DATE, fin DATE, monto_brl REAL, estado TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha DATE)')
    conn.commit()
    conn.close()

def check_disponibilidad(auto, f_i, f_f):
    conn = sqlite3.connect('jm_asociados.db')
    query = "SELECT * FROM reservas WHERE auto = ? AND NOT (fin < ? OR inicio > ?)"
    df = pd.read_sql_query(query, conn, params=(auto, str(f_i), str(f_f)))
    conn.close()
    return df.empty

init_db()

# --- 3. DATOS DE FLOTA ---
AUTOS = {
    "Toyota Vitz 2012 (Negro)": {"precio": 195, "specs": "Automático | Nafta", "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    "Hyundai Tucson 2012": {"precio": 260, "specs": "4x2 | Diesel", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    "Toyota Voxy 2009": {"precio": 240, "specs": "7 Pasajeros", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    "Toyota Vitz 2012 (Blanco)": {"precio": 195, "specs": "Automático | Full", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
}

# --- 4. ESTILOS ---
st.markdown("""<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 10px; }
    .btn-social { display: block; padding: 15px; margin: 10px 0; border-radius: 10px; text-decoration: none; text-align: center; font-weight: bold; color: white !important; }
    .btn-instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
    .btn-whatsapp { background-color: #25D366; }
    .header-app { background-color: #300000; padding: 20px; color: #D4AF37; text-align: center; border-bottom: 5px solid #D4AF37; }
</style>""", unsafe_allow_html=True)

# --- 5. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("USUARIO / TELÉFONO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "2026": st.session_state.role = "admin"
            st.session_state.autenticado = True
            st.session_state.user_name = u
            st.rerun()
else:
    st.markdown('<div class="header-app"><h1>SISTEMA DE GESTIÓN JM</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Ubicación", "⭐ Reseñas", "🛡️ Panel Master"])

    with tabs[0]:
        st.subheader("Seleccione su Vehículo")
        for nombre, info in AUTOS.items():
            with st.container():
                st.markdown(f'''<div class="card-auto"><div style="display: flex; align-items: center; gap: 20px;">
                    <img src="{info['img']}" width="180"><div>
                    <h3 style="color:#4A0404; margin:0;">{nombre}</h3>
                    <p>{info['specs']}</p><h4 style="color:#D4AF37;">R$ {info['precio']} / día</h4>
                    </div></div></div>''', unsafe_allow_html=True)
                if st.button(f"Alquilar {nombre}", key=f"btn_{nombre}"):
                    st.session_state.auto_sel = nombre

        if st.session_state.auto_sel:
            st.divider()
            with st.form("form_pago"):
                st.markdown(f"### 🧾 Confirmar Reserva: {st.session_state.auto_sel}")
                c1, c2 = st.columns(2)
                nombre_c = c1.text_input("Nombre Completo", value=st.session_state.user_name)
                tel_c = c2.text_input("WhatsApp para comprobante (Ej: 595991...)")
                f_ini = c1.date_input("Fecha Inicio", date.today())
                dias = c2.number_input("Cantidad de Días", 1, 30)
                total = dias * AUTOS[st.session_state.auto_sel]['precio']
                
                st.info(f"💰 **Total a Pagar: R$ {total}**")
                st.warning("🔑 **DATOS DE PAGO PIX:** \n\n Chave PIX: **tu-llave-pix-aqui** \n\n Banco: JM ASOCIADOS")
                
                if st.form_submit_button("✅ CONFIRMAR Y ENVIAR COMPROBANTE"):
                    if check_disponibilidad(st.session_state.auto_sel, f_ini, f_ini + timedelta(days=dias)):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, whatsapp, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?,?)",
                                     (nombre_c, tel_c, st.session_state.auto_sel, f_ini, f_ini + timedelta(days=dias), total, "Pendiente"))
                        conn.commit()
                        conn.close()
                        
                        # Crear enlace de WhatsApp con
