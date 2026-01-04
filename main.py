import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import plotly.express as px

# --- 1. CONFIGURACIÓN Y ESTILO JM PREMIUM ---
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

def verificar_disponibilidad(auto, inicio, fin):
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM reservas WHERE auto=? AND (inicio < ? AND fin > ?)''', 
              (auto, fin.strftime("%Y-%m-%d"), inicio.strftime("%Y-%m-%d")))
    resultado = c.fetchone()
    conn.close()
    return resultado is None

init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        op = st.radio("Acceso al Portal", ["Ingresar", "Registrarse"], horizontal=True)
        if op == "Ingresar":
            u = st.text_input("Usuario (Email)")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR AL SISTEMA"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u, p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in, st.session_state.user_name = True, user[0]
                    st.rerun()
                else: st.error("❌ Credenciales inválidas")
                conn.close()
        else:
            with st.form("reg_completo"):
                st.markdown("### 📋 Registro de Nuevo Cliente")
                c1, c2 = st.columns(2)
                with c1:
                    n_f = st.text_input("Nombre Completo")
                    e_f = st.text_input("Correo Electrónico")
                    t_f = st.text_input("WhatsApp")
                    p_f = st.text_input("Crear Contraseña", type="password")
                with c2:
                    d_t = st.selectbox("Tipo de Documento", ["C.I.", "CPF", "RG", "Pasaporte"])
                    d_n = st.text_input("Nro. de Documento")
                    nac = st.text_input("Nacionalidad")
                    dir_c = st.text_input("Dirección / Hotel")
                if st.form_submit_button("FINALIZAR REGISTRO"):
                    if n_f and e_f and p_f and d_n:
                        try:
                            conn = sqlite3.connect('jm_final_safe.db')
                            conn.cursor().execute("""INSERT INTO usuarios 
                                (nombre, correo, password, tel, doc_tipo, doc_num, nacionalidad, direccion) 
                                VALUES (?,?,?,?,?,?,?,?)""", (n_f, e_f, p_f, t_f, d_t, d_n, nac, dir_c))
                            conn.commit()
                            conn.close()
                            st.success("✅ Cuenta creada.")
                        except: st.error("❌ Error o correo duplicado.")

# --- 4. PORTAL JM ---
else:
    st.markdown(f'<h3 style="text-align:center; color:#D4AF37;">Bienvenido | {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Alquiler", "📅 Mi Historial", "📍 Ubicación", "⭐ Reseñas", "⚙️ Admin"])

    # --- PESTAÑA ALQUILER ---
    with tabs[0]:
        c_f1, c_f2 = st.columns(2)
        f_ini = c_f1.date_input("Fecha Entrega", min_value=datetime.now().date())
        f_fin = c_f2.date_input("Fecha Devolución", min_value=f_ini + timedelta(days=1))
        dias = (f_fin - f_ini).days

        flota = [
            {"n": "Toyota Vitz Negro", "p": 195, "eg": 45, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
            {"n": "Tucson Blanco", "p": 260, "eg": 65, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"n": "Voxy Gris", "p": 240, "eg": 55, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
            {"n": "Toyota Vitz Blanco", "p": 195, "eg": 45, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
        ]

        for car in flota:
            disponible = verificar_disponibilidad(car['n'], f_ini, f_fin)
            total = car['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                col1.image(car['img'])
                with col2:
                    st.write(f"### {car['n']}")
                    if disponible:
                        st.markdown(f'<p class="price-tag">{car["p"]} Reales / día</p>', unsafe_allow_html=True)
                        if st.button(f"Confirmar Reserva: {car['n']}", key=car['n']):
                            conn = sqlite3.connect('jm_final_safe.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto_ingreso, monto_egreso, inicio, fin) VALUES (?,?,?,?,?,?)",
                                                 (st.session_state.user_name, car['n'], total, car['eg']*dias, f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d")))
                            conn.commit()
                            st.success("✅ Registrado.")
                            msg = urllib.parse.quote(f"Hola JM, soy {st.session_state.user_name}. Quiero alquilar el {car['n']} del {f_ini} al {f_fin}. Total: {total} Reales.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={msg}" class="btn-wa-confirm">ALQUILAR Y NOTIFICAR</a>', unsafe_allow_html=True)
                    else:
                        st.markdown('<h4 style="color:#b02121;">🔴 NO DISPONIBLE</h4>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- PESTAÑA MI HISTORIAL (CORREGIDO) ---
    with tabs[1]:
        st.subheader("📋 Mi Historial")
        conn = sqlite3.connect('jm_final_safe.db')
        df_h = pd.read_sql_query(f"SELECT auto as Vehículo, inicio as Entrega, fin as Devolución, monto_ingreso as Total FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        conn.close()
        
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True)
        else:
            st.info("Sin reservas.")

    # --- PESTAÑA UBICACIÓN (MAPA EXACTO Y REDES) ---
    with tabs[2]:
        st.subheader("📍 JM ASOCIADOS - Ubicación Exacta")
        c_u1, c_u2 = st.columns([1, 2])
        with c_u1:
            st.write("**Dirección:** C/ Farid Rahal Canan, Ciudad del Este.")
            st.write("📞 **Corporativo:** 0991 681191")
            st.markdown('<a href="https://wa.me/595991681191" class="btn-wa-confirm">📲 WhatsApp Directo</a>', unsafe_allow_html=True)
            st.markdown('<br><a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" style="text-decoration:none; color:#E1306C; font-weight:bold; font-size:1.2rem;">📸 Instagram Oficial</a>', unsafe_allow_html=True)
        with c_u2:
            # Embebiendo Google Maps con la ubicación de Ciudad del Este basada en el link compartido
            st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14401.554316947665!2d-54.611181!3d-25.525434!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f691bc227a6f2b%3A0xc3f6d744b7f4337!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1715000000000!5m2!1ses!2spy" width="100%" height="400" style="border-radius:15px; border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    # --- PESTAÑA RESEÑAS ---
    with tabs[3]:
        with st.form("feedback_new"):
            est = st.select_slider("Estrellas", options=[1,2,3,4,5], value=5)
            com = st.text_area("Comentario")
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_final_safe.db')
                conn.cursor().execute("INSERT INTO feedback (cliente, comentario, estrellas, fecha) VALUES (?,?,?,?)", (st.session_state.user_name, com, est, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
                st.rerun()
        conn = sqlite3.connect('jm_final_safe.db')
        for _, r in pd.read_sql_query("SELECT * FROM feedback ORDER BY id DESC", conn).iterrows():
            st.markdown(f'<div class="review-card"><strong>{r["cliente"]}</strong> (★{r["estrellas"]})<br>{r["comentario"]}</div>', unsafe_allow_html=True)
        conn.close()

    # --- PESTAÑA ADMIN (GRÁFICOS Y ESTADÍSTICAS) ---
    with tabs[4]:
        if st.text_input("PIN Admin", type="password") == "2026":
            conn = sqlite3.connect('jm_final_safe.db')
            df_m = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            if not df_m.empty:
                st.write("### 📊 Estadísticas Financieras")
                total_ingresos = df_m['monto_ingreso'].sum()
                total_gastos = df_m['monto_egreso'].sum()
                utilidad = total_ingresos - total_gastos
                
                c_a1, c_a2, c_a3 = st.columns(3)
                c_a1.metric("Ingresos Totales", f"{total_ingresos} BRL")
                c_a2.metric("Gastos Totales", f"{total_gastos} BRL")
                c_a3.metric("Utilidad Neta", f"{utilidad} BRL")
                
                # Gráfico de Tortas
                st.write("#### Balance General (Ventas vs Gastos)")
                df_pie = pd.DataFrame({
                    "Concepto": ["Ventas (Ingresos)", "Gastos"],
                    "Monto": [total_ingresos, total_gastos]
                })
                fig = px.pie(df_pie, values='Monto', names='Concepto', color='Concepto',
                             color_discrete_map={'Ventas (Ingresos)':'#25D366', 'Gastos':'#b02121'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("#### Detalle de Reservas")
                st.dataframe(df_m, use_container_width=True)
            
            st.write("### 👥 Clientes Registrados")
            st.dataframe(pd.read_sql_query("SELECT nombre, correo, tel, doc_num FROM usuarios", conn), use_container_width=True)
            conn.close()

    if st.button("🚪 SALIR"):
        st.session_state.logged_in = False
        st.rerun()
