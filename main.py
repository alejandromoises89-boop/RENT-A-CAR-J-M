import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO PROFESIONAL JM ---
st.set_page_config(page_title="JM | Alquiler de Autos", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 5rem; font-family: 'Georgia', serif; font-weight: bold; margin-bottom: 0px; letter-spacing: 5px; }
        .sub-header { text-align: center; color: white; font-size: 1rem; margin-bottom: 40px; letter-spacing: 6px; font-weight: 300; text-transform: uppercase; }
        .card-auto { background-color: white; color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.4); }
        .btn-wa-confirm { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
        .logo-box { text-align: center; border: 2px solid #D4AF37; width: 150px; margin: 0 auto; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
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
    conn.commit()
    conn.close()

def eliminar_reserva(id_res):
    conn = sqlite3.connect('jm_final_safe.db')
    conn.cursor().execute("DELETE FROM reservas WHERE id=?", (id_res,))
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTIÓN DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. ACCESO (LOGIN/REGISTRO) ---
if not st.session_state.logged_in:
    st.markdown('<div class="logo-box"><h1 style="color:#D4AF37; margin:0; font-family:serif;">JM</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ASOCIADOS CONSULTORÍA</div>', unsafe_allow_html=True)
    
    col_login = st.columns([1, 1.5, 1])[1]
    with col_login:
        modo = st.radio("Acceso al Portal", ["Ingresar", "Registrarse"], horizontal=True)
        
        if modo == "Ingresar":
            u_mail = st.text_input("Correo Electrónico")
            u_pass = st.text_input("Contraseña", type="password")
            if st.button("ACCEDER AL PORTAL"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios WHERE correo=? AND password=?", (u_mail, u_pass))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user # GUARDAMOS DATOS DEL CLIENTE
                    st.session_state.user_name = user[1]
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
        else:
            with st.form("reg_kyc"):
                st.write("### 📋 Registro de Cliente (KYC)")
                c1, c2 = st.columns(2)
                with c1:
                    nom = st.text_input("Nombre Completo")
                    cor = st.text_input("Correo")
                    tel = st.text_input("WhatsApp")
                    pas = st.text_input("Contraseña", type="password")
                with c2:
                    dtp = st.selectbox("Documento", ["C.I.", "CPF", "Pasaporte"])
                    dnm = st.text_input("Número Doc.")
                    nac = st.text_input("Nacionalidad")
                    dir = st.text_input("Dirección/Hotel")
                if st.form_submit_button("REGISTRARME"):
                    try:
                        conn = sqlite3.connect('jm_final_safe.db')
                        conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, tel, doc_tipo, doc_num, nacionalidad, direccion) VALUES (?,?,?,?,?,?,?,?)", 
                                             (nom, cor, pas, tel, dtp, dnm, nac, dir))
                        conn.commit()
                        st.success("✅ Registro exitoso. Inicie sesión.")
                    except: st.error("❌ El correo ya existe.")

# --- 5. INTERFAZ PRINCIPAL ---
else:
    st.markdown(f'<h4 style="text-align:right; color:#D4AF37;">👤 {st.session_state.user_name}</h4>', unsafe_allow_html=True)
    tab_alq, tab_his, tab_ubi, tab_adm = st.tabs(["🚗 Alquiler", "📅 Historial", "📍 Ubicación", "⚙️ Admin"])

    # --- ALQUILER ---
    with tab_alq:
        # Lógica de fechas y flota...
        st.write("### Vehículos Disponibles")
        # [Tu lógica previa de alquiler y botón de WhatsApp aquí]

    # --- HISTORIAL CLIENTE ---
    with tab_his:
        st.write("### 📋 Mis Reservas")
        conn = sqlite3.connect('jm_final_safe.db')
        df_cli = pd.read_sql_query(f"SELECT auto, inicio, fin, monto_ingreso FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        st.dataframe(df_cli, use_container_width=True) if not df_cli.empty else st.info("No tienes reservas.")
        conn.close()

    # --- UBICACIÓN ---
    with tab_ubi:
        # Aquí va el mapa de Google Maps con la ubicación de Farid Rahal Canan
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14401.769918731388!2d-54.6127113!3d-25.5236162!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f691fd94f874ed%3A0x336570e64fcf71b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v17154500000001" width="100%" height="400" style="border-radius:15px; border:2px solid #D4AF37;"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<br><a href="https://www.instagram.com/jm_asociados_consultoria/" style="color:#D4AF37; text-decoration:none;">📸 Visítanos en Instagram</a>', unsafe_allow_html=True)

    # --- ADMIN (BORRAR Y EXPORTAR) ---
    with tab_adm:
        if st.text_input("PIN Maestro", type="password") == "2026":
            conn = sqlite3.connect('jm_final_safe.db')
            df_adm = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            st.write("### 🛠 Panel Administrativo")
            
            # Exportar datos
            if not df_adm.empty:
                csv = df_adm.to_csv(index=False).encode('utf-8')
                st.download_button("📥 DESCARGAR EXCEL (CSV)", data=csv, file_name="reservas_jm.csv", mime="text/csv")
                
                busqueda = st.text_input("🔍 Buscar cliente...")
                
                # Tabla de gestión con botón borrar
                for idx, r in df_adm.iterrows():
                    if busqueda.lower() in r['cliente'].lower() or busqueda == "":
                        with st.container():
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 0.5])
                            c1.write(f"**{r['cliente']}**")
                            c2.write(f"{r['auto']}")
                            c3.write(f"{r['inicio']} / {r['fin']}")
                            if c4.button("🗑️", key=f"btn_{r['id']}"):
                                eliminar_reserva(r['id'])
                                st.rerun()
            else:
                st.info("No hay datos para mostrar.")
            conn.close()

    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
