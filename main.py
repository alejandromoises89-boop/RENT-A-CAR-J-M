import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JM ASOCIADOS | ALQUILER DE VEHICULOS", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 3.5rem; font-weight: bold; font-family: 'Times New Roman', serif; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .spec-label { background: #f0f0f0; padding: 4px 8px; border-radius: 5px; font-size: 0.85rem; font-weight: bold; border-left: 3px solid #4e0b0b; }
        .btn-wa { background-color: #25D366; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS MEJORADA ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    # Tabla de Reservas
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, monto_brl REAL, estado TEXT)''')
    # Tabla de Reseñas
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    # Tabla de Gastos (Egresos)
    c.execute('''CREATE TABLE IF NOT EXISTS egresos 
                (id INTEGER PRIMARY KEY, tipo TEXT, monto REAL, fecha DATE, descripcion TEXT)''')
    conn.commit()
    conn.close()

def check_disponibilidad(auto, f_inicio, f_fin):
    conn = sqlite3.connect('jm_asociados.db')
    query = "SELECT * FROM reservas WHERE auto = ? AND NOT (fin < ? OR inicio > ?)"
    df = pd.read_sql_query(query, conn, params=(auto, f_inicio, f_fin))
    conn.close()
    return df.empty

def obtener_cotizacion_brl():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        return round(r.json()['rates']['PYG'])
    except: return 1450 

init_db()
cotizacion_hoy = obtener_cotizacion_brl()

# --- 3. FLOTA DETALLADA ---
flota = [
    {"nombre": "Toyota Vitz 2012", "precio": 195, "specs": "Automático | Nafta | ABS | Carta Verde", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
    {"nombre": "Hyundai Tucson 2012", "precio": 260, "specs": "Automático | Diesel | Cuero | Carta Verde", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Voxy 2009", "precio": 240, "specs": "Secuencial | 7 Pasajeros | Cámara | Carta Verde", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"}
    {"nombre": "Toyota Vitz 2012", "precio": 195, "Automático | Nafta | ABS | Carta Verde", "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"}

# --- 4. LÓGICA DE ACCESO ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM ASOCIADOS</div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name, st.session_state.logged_in = "admin", "ADMIN_MASTER", True
            else:
                st.session_state.role, st.session_state.user_name, st.session_state.logged_in = "user", u, True
            st.rerun()
else:
    # --- INTERFAZ POST-LOGIN ---
    st.markdown('<div class="header-jm">JM ASOCIADOS</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Reservas", "📍 Ubicación", "⭐ Reseñas", "⚙️ Panel Master"])

    # --- TAB 1: CATALOGO (ESTILO REVISTA) ---
    with tabs[0]:
        st.write(f"💸 Cotización: 1 BRL = {cotizacion_hoy} PYG")
        for auto in flota:
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                        <img src="{auto['img']}" width="300" style="border-radius:10px">
                        <div style="flex: 1; min-width: 300px;">
                            <h2 style="margin:0; color:#4e0b0b">{auto['nombre']}</h2>
                            <p class="spec-label">{auto['specs']}</p>
                            <p style="font-size: 1.5rem; font-weight:bold; color: #D4AF37;">R$ {auto['precio']} / día</p>
                        </div>
                    </div>
                </div>''', unsafe_allow_html=True)
                
                with st.expander(f"Agendar {auto['nombre']}"):
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Inicio", min_value=date.today(), key=f"i_{auto['nombre']}")
                    f_f = c2.date_input("Fin", min_value=f_i, key=f"f_{auto['nombre']}")
                    
                    if st.button(f"Verificar Disponibilidad", key=f"v_{auto['nombre']}"):
                        if check_disponibilidad(auto['nombre'], f_i, f_f):
                            dias = (f_f - f_i).days + 1
                            total = dias * auto['precio']
                            st.success(f"✅ Disponible por {dias} días. Total: R$ {total}")
                            
                            st.info("🏦 PIX: 24510861818 | Marina Baez | Banco Santander")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=24510861818")
                            
                            wa_msg = f"Hola JM Asociados, soy {st.session_state.user_name}. Envío comprobante de pago por {auto['nombre']} (R$ {total}) del {f_i} al {f_f}."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={wa_msg}" target="_blank" class="btn-wa">NOTIFICAR PAGO AQUÍ</a>', unsafe_allow_html=True)
                            
                            # Guardar en DB
                            conn = sqlite3.connect('jm_asociados.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, auto['nombre'], f_i, f_f, total, "Confirmado"))
                            conn.commit()
                            conn.close()
                        else:
                            st.error("❌ El vehículo ya está reservado en esas fechas.")

    # --- TAB 2: MI HISTORIAL ---
    with tabs[1]:
        conn = sqlite3.connect('jm_asociados.db')
        df = pd.read_sql_query(f"SELECT * FROM reservas WHERE cliente = '{st.session_state.user_name}'", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

    # --- TAB 3: UBICACIÓN ---
    with tabs[2]:
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.247290501!2d-54.6112!3d-25.5134!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ4LjIiUyA1NMKwMzYnNDAuMyJX!5e0!3m2!1ses!2spy!4v1625678901234!5m2!1ses!2spy" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://instagram.com/jm_asociados_consultoria" target="_blank">📸 Instagram Oficial</a>', unsafe_allow_html=True)

    # --- TAB 5: PANEL MASTER (ADMIN) ---
    with tabs[4]:
        pin = st.text_input("PIN de Seguridad", type="password")
        if pin == "2026":
            st.title("📊 Análisis Financiero y Control")
            conn = sqlite3.connect('jm_asociados.db')
            
            # Formulario de Egresos
            with st.expander("➕ Registrar Egreso (Lavado, Seguro, etc)"):
                t_eg = st.selectbox("Tipo", ["Lavado", "Seguro", "Mantenimiento", "Impuestos"])
                m_eg = st.number_input("Monto (BRL)")
                d_eg = st.text_input("Descripción")
                if st.button("Guardar Gasto"):
                    conn.cursor().execute("INSERT INTO egresos (tipo, monto, fecha, descripcion) VALUES (?,?,?,?)", (t_eg, m_eg, date.today(), d_eg))
                    conn.commit()
                    st.success("Gasto registrado.")

            # Métricas
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_eg = pd.read_sql_query("SELECT * FROM egresos", conn)
            
            c1, c2, c3 = st.columns(3)
            ingresos = df_res['monto_brl'].sum()
            egresos = df_eg['monto'].sum()
            c1.metric("Ingresos Totales", f"R$ {ingresos}")
            c2.metric("Egresos Totales", f"R$ {egresos}")
            c3.metric("Utilidad Neta", f"R$ {ingresos - egresos}")

            # Gráfico de Torta
            st.subheader("Balance Activos vs Pasivos")
            fig = px.pie(values=[ingresos, egresos], names=['Ingresos', 'Egresos'], color_discrete_sequence=['#D4AF37', '#4e0b0b'])
            st.plotly_chart(fig)

            # Gestión de Datos
            if st.button("🗑️ LIMPIAR RESERVAS DE PRUEBA"):
                conn.cursor().execute("DELETE FROM reservas")
                conn.commit()
                st.rerun()
            
            st.download_button("📥 Descargar Reporte Completo", df_res.to_csv().encode('utf-8'), "reporte_jm.csv")
            conn.close()

    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
