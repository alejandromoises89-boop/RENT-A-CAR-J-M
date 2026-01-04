import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Intentar cargar Plotly para los gráficos
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 4.5rem; font-weight: bold; margin-bottom: 0px; text-shadow: 2px 2px 4px #000; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 40px; letter-spacing: 4px; font-weight: 300; }
        .card-auto { background-color: white; color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; }
        .btn-wa-confirm { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
        /* Logo estilo Instagram */
        .insta-logo {
            display: block; margin-left: auto; margin-right: auto; width: 120px;
            background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
            padding: 10px; border-radius: 30px; border: 4px solid white;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT, 
        tel TEXT, doc_tipo TEXT, doc_num TEXT, nacionalidad TEXT, direccion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto_ingreso REAL, 
        monto_egreso REAL, inicio TEXT, fin TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)''')
    conn.commit()
    conn.close()

def eliminar_reserva(id_reserva):
    conn = sqlite3.connect('jm_final_safe.db')
    conn.cursor().execute("DELETE FROM reservas WHERE id=?", (id_reserva,))
    conn.commit()
    conn.close()

init_db()

# --- 3. MANEJO DE SESIÓN Y LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Pantalla de Login con Logo solicitado
    st.markdown('<div class="insta-logo"><h1 style="color:white; text-align:center; margin:0; font-family:serif;">JM</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ASOCIADOS CONSULTORÍA</div>', unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        op = st.radio("Acceso", ["Ingresar", "Registrarse"], horizontal=True)
        if op == "Ingresar":
            u = st.text_input("Correo")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR AL SISTEMA"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user # Guardamos todos los datos del cliente
                    st.session_state.user_name = user[1]
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
        else:
            with st.form("registro"):
                st.write("### Registro de Cliente")
                n = st.text_input("Nombre Completo")
                e = st.text_input("Correo")
                cl = st.text_input("Contraseña", type="password")
                if st.form_submit_button("CREAR CUENTA"):
                    try:
                        conn = sqlite3.connect('jm_final_safe.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password) VALUES (?,?,?)", (n, e, cl))
                        conn.commit()
                        st.success("✅ Registrado. Ahora puedes ingresar.")
                    except: st.error("❌ El correo ya existe.")

# --- 4. PORTAL JM ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Bienvenido | {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Alquiler", "📅 Historial", "📍 Ubicación", "⚙️ Admin"])

    # --- PESTAÑA ALQUILER ---
    with tabs[0]:
        # Lógica de alquiler ya funcional...
        st.info("Seleccione fechas y vehículo para proceder.")
        # [Se mantiene tu lógica previa de alquiler y notificar aquí]

    # --- PESTAÑA HISTORIAL ---
    with tabs[1]:
        conn = sqlite3.connect('jm_final_safe.db')
        df_h = pd.read_sql_query(f"SELECT auto, inicio, fin, monto_ingreso FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        st.dataframe(df_h, use_container_width=True) if not df_h.empty else st.warning("No tienes reservas.")
        conn.close()

    # --- PESTAÑA UBICACIÓN ---
    with tabs[2]:
        # Mapa y links ya configurados...
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14401.769918731388!2d-54.6127113!3d-25.5236162!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f691fd94f874ed%3A0x336570e64fcf71b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v17154500000000" width="100%" height="400" style="border-radius:15px;"></iframe>', unsafe_allow_html=True)

    # --- PESTAÑA ADMIN (BORRAR Y EXPORTAR) ---
    with tabs[3]:
        if st.text_input("PIN Admin", type="password") == "2026":
            conn = sqlite3.connect('jm_final_safe.db')
            df_admin = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            st.write("### 🛠 Gestión de Reservas")
            
            # Botón de Exportación
            if not df_admin.empty:
                csv = df_admin.to_csv(index=False).encode('utf-8')
                st.download_button("📥 EXPORTAR DATOS A EXCEL (CSV)", data=csv, file_name=f"reservas_jm_{datetime.now().date()}.csv", mime="text/csv")
                
                # Tabla con opción de borrar
                for idx, row in df_admin.iterrows():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.write(f"**{row['auto']}** - {row['cliente']}")
                    c2.write(f"📅 {row['inicio']} al {row['fin']}")
                    c3.write(f"💰 {row['monto_ingreso']} BRL")
                    if c4.button("🗑️", key=f"del_{row['id']}"):
                        eliminar_reserva(row['id'])
                        st.rerun()
            else:
                st.write("No hay reservas activas.")
            conn.close()

    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
