import streamlit as st
import sqlite3
import pd
from datetime import datetime, timedelta
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
        .historial-card { background-color: #262626; padding: 15px; border-radius: 15px; border: 1px solid #444; margin-bottom: 10px; }
        .btn-interactivo { display: inline-flex; align-items: center; justify-content: center; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin: 5px; color: white !important; }
        .btn-wa { background-color: #25D366; }
        .btn-ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #bc1888); }
        .logout-box { text-align: center; margin-top: 80px; padding-bottom: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA DE BLOQUEO ---
def init_db():
    conn = sqlite3.connect('jm_master_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, 
        doc_tipo TEXT, doc_num TEXT, tel TEXT, direccion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, monto_egreso REAL,
        inicio TEXT, fin TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER)''')
    conn.commit()
    conn.close()

def verificar_bloqueo(auto, inicio, fin):
    conn = sqlite3.connect('jm_master_final.db')
    c = conn.cursor()
    # Lógica de solapamiento: (InicioA <= FinB) AND (FinA >= InicioB)
    c.execute('''SELECT * FROM reservas WHERE auto=? AND (inicio <= ? AND fin >= ?)''', 
              (auto, fin.strftime("%Y-%m-%d"), inicio.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None

init_db()

# --- 3. GESTIÓN DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN Y REGISTRO KYC ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        opcion = st.radio("Acceso al Portal", ["Ingresar", "Registrarse como Nuevo Cliente"], horizontal=True)
        
        if opcion == "Ingresar":
            u = st.text_input("Correo Electrónico")
            p = st.text_input("Contraseña", type="password")
            if st.button("ACCEDER"):
                conn = sqlite3.connect('jm_master_final.db')
                c = conn.cursor()
                c.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in, st.session_state.user_name = True, user[0]
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
                conn.close()
        else:
            with st.form("reg_full"):
                st.write("📋 Formulario de Registro")
                c1, c2 = st.columns(2)
                n_f = c1.text_input("Nombre Completo")
                e_f = c2.text_input("Correo")
                d_t = c1.selectbox("Documento", ["C.I.", "CPF", "RG", "Pasaporte"])
                d_n = c2.text_input("Número")
                t_f = c1.text_input("Teléfono/WA")
                d_f = c2.text_input("Dirección")
                p_f = st.text_input("Clave", type="password")
                if st.form_submit_button("FINALIZAR REGISTRO"):
                    try:
                        conn = sqlite3.connect('jm_master_final.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, doc_tipo, doc_num, tel, direccion) VALUES (?,?,?,?,?,?,?)",
                                             (n_f, e_f, p_f, d_t, d_n, t_f, d_f))
                        conn.commit()
                        st.success("✅ Cuenta creada. Ingrese ahora.")
                        conn.close()
                    except Exception as e: st.error(f"Error: {e}")

# --- 5. INTERFAZ PRINCIPAL (POST-LOGIN) ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Panel de {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Alquiler", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"])

    # 🚗 PESTAÑA ALQUILER
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Fecha Inicio", min_value=datetime.now().date())
        f_fin = c_f2.date_input("Fecha Fin", min_value=f_ini + timedelta(days=1))
        dias = (f_fin - f_ini).days

        flota = [
            {"n": "Toyota Vitz", "p": 195, "eg": 40, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson", "p": 260, "eg": 65, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"}
        ]

        for car in flota:
            disponible = verificar_bloqueo(car['n'], f_ini, f_fin)
            total = car['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                ci, ct = st.columns([1, 2])
                ci.image(car['img'])
                with ct:
                    st.write(f"## {car['n']}")
                    if disponible:
                        st.write(f"Monto total por {dias} días: **{total} BRL**")
                        if st.button(f"Confirmar Reserva: {car['n']}", key=car['n']):
                            conn = sqlite3.connect('jm_master_final.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_ingreso, monto_egreso, inicio, fin, timestamp) VALUES (?,?,?,?,?,?,?)",
                                                 (st.session_state.user_name, car['n'], total, car['eg']*dias, f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success("✅ ¡Reserva Exitosa!")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_JM_{total}")
                            conn.close()
                    else:
                        st.error(f"🔴 No disponible del {f_ini} al {f_fin}")
                st.markdown('</div>', unsafe_allow_html=True)

    # 📅 PESTAÑA MI HISTORIAL
    with tabs[1]:
        st.subheader("Tus reservas anteriores")
        conn = sqlite3.connect('jm_master_final.db')
        df_h = pd.read_sql_query(f"SELECT auto, inicio, fin FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        for _, row in df_h.iterrows():
            st.markdown(f'<div class="historial-card">🚗 {row["auto"]} | Periodo: {row["inicio"]} a {row["fin"]}</div>', unsafe_allow_html=True)
            if st.button(f"Repetir Alquiler: {row['auto']}", key=f"re_{_}"):
                st.info("🔄 Seleccione nuevas fechas en la pestaña 'Alquiler'.")
        conn.close()

    # 📍 PESTAÑA UBICACIÓN
    with tabs[2]:
        st.subheader("Ubicación de JM ASOCIADOS")
        c_u1, c_u2 = st.columns([1, 1.5])
        with c_u1:
            st.write("📍 C/Farid Rahal Canan, Cd. del Este")
            st.write("📞 Teléfono: 0983 787810")
            st.markdown(f"""
                <a href="https://wa.me/595983787810" class="btn-interactivo btn-wa">WhatsApp</a>
                <a href="https://instagram.com/jymasociados" class="btn-interactivo btn-ig">Instagram</a>
            """, unsafe_allow_html=True)
        c_u2.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.9!2d-54.6!3d-25.5" width="100%" height="300" style="border-radius:15px;"></iframe>', unsafe_allow_html=True)

    # ⭐ PESTAÑA RESEÑAS
    with tabs[3]:
        with st.form("feedback"):
            star = st.select_slider("Califica tu experiencia", options=[1,2,3,4,5], value=5)
            com = st.text_area("Comentario")
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_master_final.db')
                conn.cursor().execute("INSERT INTO feedback (cliente, comentario, estrellas) VALUES (?,?,?)", (st.session_state.user_name, com, star))
                conn.commit()
                st.success("¡Gracias por tu reseña!")

    # ⚙️ PANEL MASTER (PIN: 2026)
    with tabs[4]:
        pin = st.text_input("PIN de Administrador", type="password")
        if pin == "2026":
            st.success("Acceso Maestro Autorizado")
            conn = sqlite3.connect('jm_master_final.db')
            df_m = pd.read_sql_query("SELECT * FROM reservas", conn)
            if not df_m.empty:
                st.write("### 📊 Balance Financiero")
                ing = df_m['monto_ingreso'].sum()
