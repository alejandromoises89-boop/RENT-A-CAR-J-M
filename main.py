import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO JM (BORDEAUX & DORADO) ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    .ig-btn { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    input { background-color: rgba(0,0,0,0.7) !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE BASE DE DATOS ---
DB_NAME = 'jm_final_v15.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES DE LÓGICA ---
def comprobar_disponibilidad(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Bloqueo por Taller
    est = c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,)).fetchone()[0]
    if est == "Taller":
        conn.close(); return False, "⚠️ EN TALLER"
    # Bloqueo por Reservas existentes (solapamiento)
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    if ocupado > 0:
        return False, "❌ NO DISPONIBLE EN ESTAS FECHAS"
    return True, "✅ DISPONIBLE"

# --- 4. SISTEMA DE ACCESO (LOGIN Y REGISTRO) ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_nom' not in st.session_state: st.session_state.u_nom = ""
if 'pagina' not in st.session_state: st.session_state.pagina = "login"

if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.markdown("<h1 style='text-align:center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
        correo = st.text_input("Correo electrónico")
        clave = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if correo == "admin@jm.com" and clave == "8899":
                st.session_state.logueado, st.session_state.u_nom = True, "admin"; st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                u = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (correo, clave)).fetchone()
                conn.close()
                if u:
                    st.session_state.logueado, st.session_state.u_nom = True, u[0]; st.rerun()
                else: st.error("Usuario o contraseña incorrectos")
        if st.button("¿No tienes cuenta? Regístrate aquí"):
            st.session_state.pagina = "registro"; st.rerun()

    elif st.session_state.pagina == "registro":
        st.markdown("<h2>Crear nueva cuenta</h2>", unsafe_allow_html=True)
        with st.form("registro_form"):
            n_nom = st.text_input("Nombre Completo")
            n_cor = st.text_input("Correo Electrónico")
            n_cla = st.text_input("Contraseña", type="password")
            n_cel = st.text_input("WhatsApp")
            if st.form_submit_button("Guardar y Registrar"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n_nom, n_cor, n_cla, n_cel))
                    conn.commit(); conn.close()
                    st.success("¡Cuenta guardada! Regresa al inicio para entrar."); st.session_state.pagina = "login"
                except: st.error("Ese correo ya está registrado.")
        if st.button("Volver al Login"): st.session_state.pagina = "login"; st.rerun()

# --- 5. APLICACIÓN PRINCIPAL (POST-LOGIN) ---
else:
    tab1, tab2, tab3 = st.tabs(["🚗 ALQUILAR", "📍 UBICACIÓN", "⚙️ PANEL ADMIN"])

    with tab1:
        st.write(f"Sesión: **{st.session_state.u_nom}**")
        conn = sqlite3.connect(DB_NAME)
        autos = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, a in autos.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{a["nombre"]}</h3><img src="{a["img"]}" width="200"></div>', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                d_en = c1.date_input("Fecha Entrega", key=f"de_{a['nombre']}")
                h_en = c1.time_input("Hora Entrega", time(9,0), key=f"he_{a['nombre']}")
                d_de = c2.date_input("Fecha Devolución", key=f"dd_{a['nombre']}")
                h_de = c2.time_input("Hora Devolución", time(10,0), key=f"hd_{a['nombre']}")
                
                dt_inicio = datetime.combine(d_en, h_en)
                dt_fin = datetime.combine(d_de, h_de)
                
                disponible, msg_status = comprobar_disponibilidad(a['nombre'], dt_inicio, dt_fin)
                
                if disponible:
                    st.success(msg_status)
                    if st.button(f"Confirmar Reserva: {a['nombre']}"):
                        total = max(1, (dt_fin - dt_inicio).days) * a['precio']
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)",
                                     (st.session_state.u_nom, a['nombre'], dt_inicio, dt_fin, total))
                        conn.commit(); conn.close()
                        
                        # WHATSAPP EMPRESARIAL 0991681191
                        msg_wa = (f"*JM ASOCIADOS - RESERVA CONFIRMADA*\n\n"
                                  f"Hola {st.session_state.u_nom}, su reserva del {a['nombre']} ha sido bloqueada.\n"
                                  f"Desde: {dt_inicio.strftime('%d/%m %H:%M')}\n"
                                  f"Hasta: {dt_fin.strftime('%d/%m %H:%M')}\n"
                                  f"Total: R$ {total}\n\n"
                                  f"🔑 *PIX:* 24510861818\n\n"
                                  f"Adjunte su comprobante aquí para finalizar.")
                        
                        st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg_wa)}" class="wa-btn">📲 ENVIAR COMPROBANTE AL 0991681191</a>', unsafe_allow_html=True)
                else:
                    st.error(msg_status)

    with tab2:
        st.subheader("Nuestra Ubicación Exacta")
        # El iframe debe ser el de EMBED para que funcione siempre
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.913615206085!2d-54.614830125272314!3d-25.50791483592176!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68ff7e5f8f4ed%3A0x536570e74fc7f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1704481000000!5m2!1ses!2spy" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="ig-btn">📸 Síguenos en Instagram Oficial</a>', unsafe_allow_html=True)

    with tab3:
        if st.session_state.u_nom == "admin":
            st.title("🛡️ CONTROL MÁSTER")
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.metric("INGRESOS TOTALES", f"R$ {res['total'].sum():,.2f}")
            st.dataframe(res)
            
            st.subheader("🔧 Mantenimiento de Flota")
            flota_data = pd.read_sql_query("SELECT * FROM flota", conn)
            for _, f in flota_data.iterrows():
                if st.button(f"Mover {f['nombre']} a {'Taller' if f['estado']=='Disponible' else 'Disponible'}"):
                    nuevo = 'Taller' if f['estado']=='Disponible' else 'Disponible'
                    conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                    conn.commit(); st.rerun()
            conn.close()
        else:
            st.warning("Área restringida para el administrador.")