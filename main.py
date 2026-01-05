import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="JM ALQUILER - SISTEMA CORPORATIVO", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
    .ig-btn { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS (NO CAMBIAR EL NOMBRE PARA NO PERDER USUARIOS) ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, descripcion TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE BLOQUEO DE FECHAS Y HORAS ---
def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verifica solapamiento exacto de fechas y horas
    query = """
    SELECT COUNT(*) FROM reservas 
    WHERE auto = ? 
    AND NOT (fin <= ? OR inicio >= ?)
    """
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    
    # También verificar si está en taller
    estado_actual = c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,)).fetchone()[0]
    conn.close()
    
    if estado_actual == "Taller": return False, "⚠️ VEHÍCULO EN MANTENIMIENTO (TALLER)"
    if ocupado > 0: return False, f"❌ NO DISPONIBLE: Ya reservado en este horario."
    return True, "✅ DISPONIBLE"

# --- 4. ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

if st.session_state.logueado:
    col_salida = st.columns([1, 8])
    if col_salida[0].button("🚪 Salir"):
        st.session_state.logueado = False
        st.rerun()

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ACCESO</h1>", unsafe_allow_html=True)
    c1, c2 = st.tabs(["Ingresar", "Registrarse"])
    with c1:
        corr = st.text_input("Correo")
        passw = st.text_input("Clave", type="password")
        if st.button("ENTRAR"):
            if corr == "admin@jm.com" and passw == "8899":
                st.session_state.logueado, st.session_state.u_nom = True, "admin"; st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                u = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (corr, passw)).fetchone()
                conn.close()
                if u: st.session_state.logueado, st.session_state.u_nom = True, u[0]; st.rerun()
                else: st.error("Credenciales incorrectas")
    with c2:
        with st.form("registro"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); cel = st.text_input("WhatsApp")
            if st.form_submit_button("Crear Cuenta"):
                conn = sqlite3.connect(DB_NAME)
                try:
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n,e,p,cel)); conn.commit()
                    st.success("¡Cuenta registrada con éxito!"); st.rerun()
                except: st.error("El correo ya existe.")
                conn.close()

# --- 5. APP PRINCIPAL ---
else:
    tab1, tab2, tab3 = st.tabs(["🚗 ALQUILER", "📍 CONTACTO", "🛡️ ADMINISTRACIÓN"])

    with tab1:
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="250"></div>', unsafe_allow_html=True)
                
                with st.expander(f"Seleccionar Fechas y Horas para {v['nombre']}"):
                    c1, c2 = st.columns(2)
                    dt1 = datetime.combine(c1.date_input("Entrega", key=f"f1{v['nombre']}"), c1.time_input("Hora ", time(9,0), key=f"h1{v['nombre']}"))
                    dt2 = datetime.combine(c2.date_input("Devolución", key=f"f2{v['nombre']}"), c2.time_input("Hora  ", time(10,0), key=f"h2{v['nombre']}"))
                    
                    disponible, mensaje = esta_disponible(v['nombre'], dt1, dt2)
                    
                    if disponible:
                        st.success(mensaje)
                        if st.button(f"Confirmar Alquiler {v['nombre']}"):
                            total = max(1, (dt2-dt1).days) * v['precio']
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)",
                                         (st.session_state.u_nom, v['nombre'], dt1, dt2, total))
                            conn.commit(); conn.close()
                            st.success("✅ RESERVA BLOQUEADA")
                            txt = f"*JM RESERVA*\nAuto: {v['nombre']}\nTotal: R$ {total}\nPIX: 24510861818"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(txt)}" class="wa-btn">📲 ENVIAR COMPROBANTE AL 0991681191</a>', unsafe_allow_html=True)
                    else:
                        st.error(mensaje)

    with tab2:
        st.subheader("Ubicación de J&M ASOCIADOS")
        # MAPA CORREGIDO (Embed Oficial)
        mapa_html = """
        <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.3787723226355!2d-54.61463132371424!3d-25.55906563816674!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f685f7e5f8f4ed%3A0x336570e74fc7f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1715634500000!5m2!1ses!2spy" 
        width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>
        """
        st.markdown(mapa_html, unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="ig-btn">📸 INSTAGRAM OFICIAL</a>', unsafe_allow_html=True)

    with tab3:
        if st.session_state.u_nom == "admin":
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.title("📊 ESTADÍSTICAS Y CONTROL")
            st.metric("INGRESOS TOTALES", f"R$ {res['total'].sum():,.2f}")
            
            st.subheader("📋 Gestión de Reservas y Borrado")
            for _, r in res.iterrows():
                col_i, col_d = st.columns([4, 1])
                col_i.write(f"ID: {r['id']} | {r['cliente']} | {r['auto']} | {r['inicio']} al {r['fin']}")
                if col_d.button("🗑️ Borrar", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
            
            st.subheader("⚙️ Mantenimiento (Bloquear Auto)")
            flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
            for _, f in flota_adm.iterrows():
                if st.button(f"Mover {f['nombre']} a {'Taller' if f['estado']=='Disponible' else 'Disponible'}"):
                    nuevo = 'Taller' if f['estado']=='Disponible' else 'Disponible'
                    conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                    conn.commit(); st.rerun()
            conn.close()