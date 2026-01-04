import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import time
import base64

# --- 1. CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #1a0404 0%, #000000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 4.5rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.5rem; margin-bottom: 40px; letter-spacing: 4px; font-weight: 300; }
        .card-auto { background-color: #ffffff; color: #1a1a1a; padding: 25px; border-radius: 20px; border-left: 8px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
        .btn-wa-confirm { background-color: #25D366; color: white !important; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
        .btn-social { display: inline-flex; align-items: center; justify-content: center; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; margin: 5px; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_2026.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, doc_tipo TEXT, doc_num TEXT, tel TEXT, direccion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, monto_egreso REAL, inicio TEXT, fin TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER)''')
    conn.commit()
    conn.close()

def verificar_bloqueo(auto, inicio, fin):
    conn = sqlite3.connect('jm_final_2026.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM reservas WHERE auto=? AND (inicio <= ? AND fin >= ?)''', (auto, fin.strftime("%Y-%m-%d"), inicio.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        opcion = st.radio("Portal de Acceso", ["Ingresar", "Registrarse"], horizontal=True)
        if opcion == "Ingresar":
            u = st.text_input("Email")
            p = st.text_input("Clave", type="password")
            if st.button("ACCEDER"):
                conn = sqlite3.connect('jm_final_2026.db')
                c = conn.cursor()
                c.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in, st.session_state.user_name = True, user[0]
                    st.rerun()
                else: st.error("❌ Datos incorrectos")
        else:
            with st.form("registro"):
                n = st.text_input("Nombre Completo")
                e = st.text_input("Correo")
                d_t = st.selectbox("Documento", ["C.I.", "CPF", "Pasaporte"])
                d_n = st.text_input("Nro Documento")
                t_f = st.text_input("Teléfono")
                p_f = st.text_input("Contraseña", type="password")
                if st.form_submit_button("REGISTRAR"):
                    conn = sqlite3.connect('jm_final_2026.db')
                    conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, doc_tipo, doc_num, tel) VALUES (?,?,?,?,?,?)", (n, e, p_f, d_t, d_n, t_f))
                    conn.commit()
                    st.success("Registrado correctamente")

# --- 5. PORTAL POST-LOGIN ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Bienvenido, {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Flota", "📅 Mis Reservas", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"])

    # --- PESTAÑA: FLOTA (CON NOTIFICACIÓN WHATSAPP) ---
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Inicio Alquiler", min_value=datetime.now().date())
        f_fin = c_f2.date_input("Fin Alquiler", min_value=f_ini + timedelta(days=1))
        dias = (f_fin - f_ini).days

        # FLOTA COMPLETA
        flota_full = [
            {"n": "Toyota Vitz Negro", "p": 195, "eg": 45, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson Blanco", "p": 260, "eg": 60, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy Gris", "p": 240, "eg": 55, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
        ]

        for car in flota_full:
            libre = verificar_bloqueo(car['n'], f_ini, f_fin)
            monto = car['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                ci, ct = st.columns([1, 2])
                ci.image(car['img'])
                with ct:
                    st.write(f"## {car['n']}")
                    if libre:
                        st.write(f"Total: **{monto} BRL**")
                        if st.button(f"Confirmar Reserva {car['n']}", key=car['n']):
                            conn = sqlite3.connect('jm_final_2026.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_ingreso, monto_egreso, inicio, fin, timestamp) VALUES (?,?,?,?,?,?,?)",
                                                 (st.session_state.user_name, car['n'], monto, car['eg']*dias, f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success("✅ ¡Reserva Guardada!")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=JM_PAY_{monto}")
                            
                            # GENERACIÓN DINÁMICA DE BOTÓN WHATSAPP
                            msg = f"Hola JM ASOCIADOS, soy {st.session_state.user_name}. Reservé el {car['n']} del {f_ini} al {f_fin}. Monto: {monto} BRL."
                            msg_encoded = urllib.parse.quote(msg)
                            wa_url = f"https://wa.me/595991681191?text={msg_encoded}"
                            st.markdown(f'<a href="{wa_url}" class="btn-wa-confirm">📲 NOTIFICAR PAGO POR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("🔴 Ocupado para estas fechas")
                st.markdown('</div>', unsafe_allow_html=True)

    # --- PESTAÑA: UBICACIÓN Y REDES ---
    with tabs[2]:
        st.subheader("📍 Contacto y Redes")
        col_c1, col_c2 = st.columns([1, 1.5])
        with col_c1:
            st.write("**Ubicación:** C/Farid Rahal Canan, Cd. del Este")
            st.write("📞 **Corporativo:** 0991 681191")
            st.markdown(f"""
                <a href="https://wa.me/595991681191" class="btn-social" style="background:#25D366">WhatsApp Oficial</a><br>
                <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-social" style="background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#bc1888)">Instagram JM</a>
            """, unsafe_allow_html=True)
        col_c2.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3600.9575825227284!2d-54.611158!3d-25.506456!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685fd04f8f4ed%3A0xd36570e647c7f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v17000000000004" width="100%" height="300" style="border-radius:15px;"></iframe>', unsafe_allow_html=True)

    # --- PESTAÑA: PANEL MASTER ---
    with tabs[4]:
        pin = st.text_input("Clave Maestro", type="password")
        if pin == "2026":
            st.success("Acceso Admin")
            conn = sqlite3.connect('jm_final_2026.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            if not df.empty:
                st.metric("Total Ingresos", f"{df['monto_ingreso'].sum()} BRL")
                st.bar_chart(df.groupby('auto')['monto_ingreso'].sum())
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Exportar para Cierre de Año", csv, "JM_Cierre_2026.csv")
                if st.button("🗑️ Resetear Reservas"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()

    # BOTÓN LOGOUT (ABAJO)
    st.markdown('<div style="text-align:center; margin-top:100px;">', unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
