import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import base64

# --- 1. CONFIGURACIÓN Y ESTILO DEGRADADO PREMIUM ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { 
            background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); 
            color: white; 
        }
        .header-jm { text-align: center; color: #D4AF37; font-size: 4.5rem; font-weight: bold; margin-bottom: 0px; text-shadow: 2px 2px 4px #000; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 40px; letter-spacing: 4px; font-weight: 300; }
        .card-auto { 
            background-color: white; 
            color: #1a1a1a; 
            padding: 25px; 
            border-radius: 15px; 
            border: 2px solid #D4AF37; 
            margin-bottom: 20px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); 
        }
        .review-card {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #D4AF37;
            margin-bottom: 10px;
        }
        .btn-wa-confirm { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px; }
        .price-tag { color: #b02121; font-size: 1.4rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ACTUALIZADA ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, monto_egreso REAL, inicio TEXT, fin TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)''')
    conn.commit()
    conn.close()

def verificar_bloqueo(auto, inicio, fin):
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM reservas WHERE auto=? AND (inicio <= ? AND fin >= ?)''', (auto, fin.strftime("%Y-%m-%d"), inicio.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None

init_db()

# --- 3. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. ACCESO (LOGIN/REGISTRO) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        op = st.radio("Acceso al Portal", ["Ingresar", "Registrarse"], horizontal=True)
        if op == "Ingresar":
            u = st.text_input("Usuario (Email)")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in, st.session_state.user_name = True, user[0]
                    st.rerun()
                else: st.error("❌ Credenciales inválidas")
        else:
            with st.form("reg"):
                n = st.text_input("Nombre Completo")
                e = st.text_input("Correo")
                t = st.text_input("WhatsApp")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("REGISTRARSE"):
                    try:
                        conn = sqlite3.connect('jm_final_safe.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, tel) VALUES (?,?,?,?)", (n, e, p, t))
                        conn.commit()
                        st.success("¡Registro exitoso! Ya puede ingresar.")
                    except: st.error("El correo ya existe.")

# --- 5. PORTAL JM ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Bienvenido, {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Alquiler de Flota", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"])

    # --- PESTAÑA 1: ALQUILER ---
    with tabs[0]:
        st.subheader("Seleccione sus fechas de reserva")
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Desde", min_value=datetime.now().date())
        f_fin = c_f2.date_input("Hasta", min_value=f_ini + timedelta(days=1))
        dias = (f_fin - f_ini).days

        flota_oficial = [
            {"n": "Toyota Vitz Negro", "p": 195, "eg": 45, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson Blanco", "p": 260, "eg": 65, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Toyota Voxy Gris", "p": 240, "eg": 55, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
            {"n": "Toyota IST Azul", "p": 200, "eg": 45, "img": "https://i.ibb.co/v6m80C2/ist-blue.png"},
            {"n": "Toyota Auris Plata", "p": 210, "eg": 50, "img": "https://i.ibb.co/YyY2X8P/auris.png"}
        ]

        for car in flota_oficial:
            libre = verificar_bloqueo(car['n'], f_ini, f_fin)
            total_reserva = car['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                col1.image(car['img'])
                with col2:
                    st.write(f"### {car['n']}")
                    if libre:
                        st.markdown(f'<p class="price-tag">Precio: {car["p"]} BRL / día</p>', unsafe_allow_html=True)
                        st.write(f"Total por {dias} días: **{total_reserva} BRL**")
                        if st.button(f"Confirmar Reserva: {car['n']}", key=car['n']):
                            conn = sqlite3.connect('jm_final_safe.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_ingreso, monto_egreso, inicio, fin) VALUES (?,?,?,?,?,?)",
                                                 (st.session_state.user_name, car['n'], total_reserva, car['eg']*dias, f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success("¡Reserva guardada!")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=PAY_JM_{total_reserva}")
                            
                            msg = f"Hola JM, soy {st.session_state.user_name}. Reservé el {car['n']} del {f_ini} al {f_fin}. Pago: {total_reserva} BRL."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-wa-confirm">📲 NOTIFICAR POR WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("🔴 VEHÍCULO NO DISPONIBLE")
                st.markdown('</div>', unsafe_allow_html=True)

    # --- PESTAÑA 2: MI HISTORIAL ---
    with tabs[1]:
        st.subheader("Tus alquileres registrados")
        conn = sqlite3.connect('jm_final_safe.db')
        df_h = pd.read_sql_query(f"SELECT auto, inicio, fin FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        if not df_h.empty:
            st.table(df_h)
        else:
            st.info("Aún no tienes reservas.")
        conn.close()

    # --- PESTAÑA 3: UBICACIÓN ---
    with tabs[2]:
        st.subheader("📍 Contacto Oficial")
        st.write("📞 WhatsApp Corporativo: 0991 681191")
        st.markdown(f"""
            <a href="https://wa.me/595991681191" style="color:#25D366; font-weight:bold; text-decoration:none;">📲 Enviar Mensaje Directo</a><br><br>
            <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" style="color:#e1306c; font-weight:bold; text-decoration:none;">📸 Visitar Instagram</a>
        """, unsafe_allow_html=True)
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.627727142!2d-54.611111!3d-25.511111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1620000000000!5m2!1ses!2spy2" width="100%" height="300" style="border-radius:15px; margin-top:10px;"></iframe>', unsafe_allow_html=True)

    # --- PESTAÑA 4: RESEÑAS EN TIEMPO REAL ---
    with tabs[3]:
        st.subheader("Comentarios de la Comunidad")
        
        # Formulario para publicar
        with st.expander("✍️ Dejar una Reseña"):
            with st.form("form_review"):
                estrellas = st.select_slider("Calificación", options=[1,2,3,4,5], value=5)
                coment = st.text_area("Cuéntanos tu experiencia")
                if st.form_submit_button("Publicar Comentario"):
                    conn = sqlite3.connect('jm_final_safe.db')
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                    conn.cursor().execute("INSERT INTO feedback (cliente, comentario, estrellas, fecha) VALUES (?,?,?,?)", 
                                         (st.session_state.user_name, coment, estrellas, fecha_hoy))
                    conn.commit()
                    conn.close()
                    st.success("¡Gracias por tu opinión!")
                    st.rerun()

        # Mostrar reseñas
        conn = sqlite3.connect('jm_final_safe.db')
        df_f = pd.read_sql_query("SELECT * FROM feedback ORDER BY id DESC", conn)
        for _, row in df_f.iterrows():
            st.markdown(f"""
                <div class="review-card">
                    <strong style="color:#D4AF37;">{row['cliente']}</strong> <small style="color:#ccc;">({row['fecha']})</small><br>
                    <span style="color:#FFD700;">{"★" * row['estrellas']}</span><br>
                    {row['comentario']}
                </div>
            """, unsafe_allow_html=True)
        conn.close()

    # --- PESTAÑA 5: PANEL MASTER ---
    with tabs[4]:
        pin = st.text_input("PIN Admin", type="password")
        if pin == "2026":
            st.success("Modo Administrador Activo")
            conn = sqlite3.connect('jm_final_safe.db')
            df_r = pd.read_sql_query("SELECT * FROM reservas", conn)
            if not df_r.empty:
                st.metric("Balance de Utilidad", f"{df_r['monto_ingreso'].sum() - df_r['monto_egreso'].sum()} BRL")
                st.write("### Listado Maestro de Reservas")
                st.dataframe(df_r)
                if st.button("🗑️ Resetear Reservas"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()
            conn.close()

    # BOTÓN DE LOGOUT
    st.markdown('<div style="text-align:center; margin-top:50px; padding-bottom:50px;">', unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
