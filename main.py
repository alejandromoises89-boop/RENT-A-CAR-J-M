import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        html { scroll-behavior: smooth; }
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; margin-bottom: 5px; font-size: 3rem; font-weight: bold; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 20px; font-weight: 300; letter-spacing: 2px; }
        .cotizacion-texto { text-align: center; color: #D4AF37; font-weight: bold; border: 1px solid #D4AF37; padding: 10px; border-radius: 10px; background: rgba(255,255,255,0.05); margin-bottom: 15px; }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .btn-notif { display: flex; align-items: center; justify-content: center; padding: 12px; border-radius: 10px; text-decoration: none !important; font-weight: bold; margin-top: 8px; width: 100%; border: none; transition: 0.3s; }
        .btn-whatsapp { background-color: #25D366; color: white !important; }
        .btn-instagram { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white !important; }
        .btn-icon { margin-right: 10px; font-size: 22px; }
        .btn-notif:hover { transform: scale(1.02); opacity: 0.9; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL, fecha_registro TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    conn.commit()
    conn.close()

def obtener_cotizacion_brl():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450 

cotizacion_hoy = obtener_cotizacion_brl()
init_db()

# --- 3. FLOTA ---
flota = [
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">ACCESO PRIVADO</div>', unsafe_allow_html=True)
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("INGRESAR AL PORTAL"):
        if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
            st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
        else:
            st.session_state.role, st.session_state.user_name = "user", u
        st.session_state.logged_in = True
        st.rerun()
else:
    st.markdown('<div class="header-jm">J&M</div><div class="sub-header">Alquiler de Vehículos</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cotizacion-texto">1 Real = {cotizacion_hoy:,} PYG</div>', unsafe_allow_html=True)
    
    tabs_labels = ["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación & Redes", "⭐ Reseñas"]
    if st.session_state.role == "admin": tabs_labels.append("⚙️ Panel Master")
    tabs = st.tabs(tabs_labels)

    # --- TAB CATALOGO ---
    with tabs[0]:
        for idx, auto in enumerate(flota):
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            auto_id = f"veh_{idx}"
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1: st.image(auto['img'], use_container_width=True)
                with c2:
                    st.subheader(f"{auto['nombre']} {auto['color']}")
                    st.write(f"Tarifa: **{auto['precio_brl']} BRL** (Gs. {monto_pyg:,})")
                    if st.button("Confirmar Reserva", key=f"btn_{auto_id}"):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl, fecha_registro) VALUES (?,?,?,?,?,?,?)",
                                             (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", "Confirmado", "Activo", monto_pyg, auto['precio_brl'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("✅ Reserva registrada. Pague vía PIX y envíe el comprobante.")
                        st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818")
                st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB HISTORIAL ---
    with tabs[1]:
        st.subheader("Mis Alquileres")
        conn = sqlite3.connect('jm_asociados.db')
        df_mine = pd.read_sql_query(f"SELECT auto, monto_brl, fecha_registro FROM reservas WHERE cliente = '{st.session_state.user_name}'", conn)
        st.dataframe(df_mine, use_container_width=True)
        conn.close()

    # --- TAB UBICACIÓN ---
    with tabs[2]:
        col_m, col_t = st.columns([2, 1])
        with col_m:
            st.markdown("### 📍 Ubicación")
            st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.246747228815!2d-54.6133!3d-25.5133!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ3LjkiUyA1NMKwMzYnNDcuOSJX!5e0!3m2!1ses!2spy!4v1700000000000" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        with col_t:
            st.write("**Edificio Aramí** (Frente Edif. España)")
            st.write("Farid Rahal y Curupayty, CDE")
            st.markdown(f'''<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" class="btn-notif btn-instagram">Instagram</a>''', unsafe_allow_html=True)

    # --- TAB RESEÑAS ---
    with tabs[3]:
        st.subheader("⭐ Reseñas")
        with st.form("f_res"):
            com = st.text_area("Comentario")
            est = st.select_slider("Calificación", options=[1,2,3,4,5], value=5)
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_asociados.db')
                conn.cursor().execute("INSERT INTO resenas (cliente, comentario, estrellas, fecha) VALUES (?,?,?,?)", (st.session_state.user_name, com, est, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("¡Gracias!")

    # --- PANEL MASTER (FINANZAS Y ESTADÍSTICAS) ---
    if st.session_state.role == "admin":
        with tabs[4]:
            st.title("📊 Balance y Metas J&M")
            conn = sqlite3.connect('jm_asociados.db')
            df_all = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            if not df_all.empty:
                # 1. MÉTRICAS FINANCIERAS
                ingreso_total = df_all['monto_brl'].sum()
                egreso_simulado = ingreso_total * 0.30  # 30% estimado de gastos operativos
                utilidad = ingreso_total - egreso_simulado
                
                c1, c2, c3 = st.columns(3)
                c1.metric("INGRESOS TOTALES", f"{ingreso_total:,.2f} BRL", delta="Bruto")
                c2.metric("EGRESOS (EST.)", f"{egreso_simulado:,.2f} BRL", delta="-30%", delta_color="inverse")
                c3.metric("UTILIDAD NETA", f"{utilidad:,.2f} BRL", delta="Neto", delta_color="normal")
                
                st.divider()
                
                # 2. ESTADÍSTICAS PARA PRESENTACIÓN
                st.subheader("📈 Rendimiento por Modelo")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.write("Alquileres por Vehículo")
                    st.bar_chart(df_all['auto'].value_counts())
                
                with col_chart2:
                    st.write("Ingresos por Auto (BRL)")
                    ingresos_auto = df_all.groupby('auto')['monto_brl'].sum()
                    st.area_chart(ingresos_auto)
                
                st.divider()
                
                # 3. GESTIÓN DE RESERVAS
                st.subheader("📋 Auditoría de Reservas")
                st.dataframe(df_all[['id', 'cliente', 'auto', 'monto_brl', 'fecha_registro']], use_container_width=True)
                
                if st.button("🗑️ BORRAR TODAS LAS RESERVAS (LIMPIEZA DE PRUEBAS)"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.warning("Se han eliminado todos los registros para la nueva gestión.")
                    st.rerun()
            else:
                st.info("No hay datos financieros registrados aún.")
            
            conn.close()
