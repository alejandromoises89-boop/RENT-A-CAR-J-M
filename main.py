import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTÉTICA ---
st.set_page_config(page_title="JM ALQUILER", layout="wide")

st.markdown("""
<style>
    .stApp { background: #1a1a1a; color: #D4AF37; }
    .card-auto { background: #262626; padding: 15px; border-radius: 10px; border: 1px solid #D4AF37; margin-bottom: 10px; text-align: center; }
    .btn-contact { display: block; width: 100%; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; margin: 5px 0; border: 1px solid #D4AF37; }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS (VERSION FINAL ESTABLE) ---
def init_db():
    conn = sqlite3.connect('jm_final_v10.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, tel_cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT)')
    
    # Datos de flota
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE BLOQUEO ---
def verificar_disponibilidad(auto, t_inicio, t_fin):
    conn = sqlite3.connect('jm_final_v10.db')
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# --- 4. CONTROL DE ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "login"
if 'u_data' not in st.session_state: st.session_state.u_data = {}

if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.title("🔑 JM ACCESO")
        correo = st.text_input("Correo electrónico")
        clave = st.text_input("Contraseña", type="password")
        
        if st.button("INGRESAR"):
            if correo == "admin@jm.com" and clave == "8899":
                st.session_state.logueado = True
                st.session_state.u_data = {"nombre": "Administrador", "celular": "0991681191"}
                st.rerun()
            else:
                conn = sqlite3.connect('jm_final_v10.db')
                user = conn.execute("SELECT nombre, celular FROM usuarios WHERE correo=? AND password=?", (correo, clave)).fetchone()
                conn.close()
                if user:
                    st.session_state.logueado = True
                    st.session_state.u_data = {"nombre": user[0], "celular": user[1]}
                    st.rerun()
                else: st.error("❌ Correo o contraseña incorrectos.")
        
        if st.button("No tengo cuenta (Registrarse)"):
            st.session_state.pagina = "registro"
            st.rerun()

    elif st.session_state.pagina == "registro":
        st.title("📝 REGISTRO DE USUARIO")
        with st.form("form_registro"):
            nuevo_nombre = st.text_input("Nombre Completo")
            nuevo_correo = st.text_input("Correo Electrónico")
            nueva_clave = st.text_input("Contraseña", type="password")
            nuevo_celular = st.text_input("Número de WhatsApp (con código de área)")
            enviar = st.form_submit_button("Guardar Usuario")
            
            if enviar:
                if nuevo_nombre and nuevo_correo and nueva_clave:
                    try:
                        conn = sqlite3.connect('jm_final_v10.db')
                        conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (nuevo_nombre, nuevo_correo, nueva_clave, nuevo_celular))
                        conn.commit()
                        conn.close()
                        st.success("✅ ¡Usuario guardado con éxito! Ya puedes iniciar sesión.")
                        st.session_state.pagina = "login"
                        # No hacemos rerun automático aquí para que el usuario vea el éxito
                    except sqlite3.IntegrityError:
                        st.error("❌ Este correo ya está registrado.")
                else:
                    st.warning("⚠️ Complete todos los campos.")
        
        if st.button("Volver al Login"):
            st.session_state.pagina = "login"
            st.rerun()

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    tab1, tab2 = st.tabs(["🚗 Vehículos y Reserva", "📍 Ubicación y Contacto"])

    with tab1:
        st.write(f"Bienvenido/a, **{st.session_state.u_data['nombre']}**")
        conn = sqlite3.connect('jm_final_v10.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, a in df.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{a["nombre"]}</h3><img src="{a["img"]}" width="250"></div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                f_i = c1.date_input("Fecha Entrega", key=f"fi_{a['nombre']}")
                h_i = c1.time_input("Hora Entrega", time(9, 0), key=f"hi_{a['nombre']}")
                f_d = c2.date_input("Fecha Devolución", key=f"fd_{a['nombre']}")
                h_d = c2.time_input("Hora Devolución", time(9, 0), key=f"hd_{a['nombre']}")
                
                dt_i = datetime.combine(f_i, h_i)
                dt_d = datetime.combine(f_d, h_d)

                if st.button(f"Confirmar Reserva: {a['nombre']}"):
                    if verificar_disponibilidad(a['nombre'], dt_i, dt_d):
                        total = max(1, (dt_d - dt_i).days) * a['precio']
                        conn = sqlite3.connect('jm_final_v10.db')
                        conn.execute("INSERT INTO reservas (cliente, tel_cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?,?)",
                                     (st.session_state.u_data['nombre'], st.session_state.u_data['celular'], a['nombre'], dt_i, dt_d, total))
                        conn.commit(); conn.close()
                        
                        st.success("✅ Reserva Bloqueada con Éxito.")
                        
                        # MENSAJE AL WHATSAPP DEL CLIENTE
                        msg = (f"*JM ALQUILER - RESERVA CONFIRMADA*\n\n"
                               f"🚗 Vehículo: {a['nombre']}\n"
                               f"📅 Recogida: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                               f"📅 Devolución: {dt_d.strftime('%d/%m/%Y %H:%M')}\n"
                               f"💰 Total: R$ {total}\n\n"
                               f"💳 PIX: 24510861818\n"
                               f"⚠️ Envíe comprobante al: 0991681191")
                        
                        num_dest = st.session_state.u_data['celular'].replace("+", "").replace(" ", "")
                        st.markdown(f'<a href="https://wa.me/{num_dest}?text={urllib.parse.quote(msg)}" class="btn-contact wa">📲 ENVIAR DATOS A MI WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Fechas u horarios no disponibles para este auto.")

    with tab2:
        st.subheader("Ubicación Exacta")
        # Iframe con la ubicación solicitada
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4019283734133!2d-54.6434446!3d-25.5083056!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68500e5f4ec0d%3A0x336570e74f87f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses-419!2spy!4v1715800000000" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">💬 WhatsApp Corporativo 0991681191</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)