import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, date

# --- 1. CONFIGURACIÓN INICIAL (DEBE SER LA PRIMERA LÍNEA) ---
st.set_page_config(page_title="JM ASOCIADOS | ALQUILER DE VEHICULOS", layout="wide")

# --- 2. GESTIÓN DE ESTADOS DE SESIÓN (EL CEREBRO DEL SISTEMA) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'vista_login' not in st.session_state:
    st.session_state.vista_login = "inicio"
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"

# --- 3. FUNCIONES DE BASE DE DATOS Y API ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, monto_brl REAL, estado TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
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

# --- 4. DISEÑOS CSS (SEPARADOS POR VISTA) ---
def aplicar_estilo_login():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle, #4A0404 0%, #1A0000 100%); color: white; }
        .title-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 50px; font-weight: bold; text-align: center; letter-spacing: 5px; margin-bottom:0px; }
        .subtitle-jm { font-family: 'Times New Roman', serif; color: #D4AF37; font-size: 18px; text-align: center; text-transform: uppercase; letter-spacing: 3px; }
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05)!important; border: 1px solid #D4AF37!important; color: #D4AF37!important; }
        .stButton>button { background-color: #600000!important; color: #D4AF37!important; border: 1px solid #D4AF37!important; font-family: 'Times New Roman', serif; font-weight: bold; width: 100%; border-radius: 5px; height: 3em; }
        .stButton>button:hover { background-color: #800000!important; border: 1px solid #FFF!important; color: white!important; }
    </style>
    """, unsafe_allow_html=True)

def aplicar_estilo_app():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #333; }
        .header-app { background-color: #4A0404; padding: 25px; color: #D4AF37; text-align: center; border-bottom: 5px solid #D4AF37; margin-bottom: 30px; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .spec-label { background: #f8f9fa; padding: 5px 10px; border-radius: 5px; font-size: 0.9rem; font-weight: bold; border-left: 4px solid #4A0404; color: #444; }
        .btn-wa { background-color: #25D366; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 15px; font-size: 1.1rem; }
        .stTabs [data-baseweb="tab-list"] { background-color: #f1f1f1; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { font-size: 18px; color: #4A0404; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. CONTROL DE FLUJO (LO QUE EL USUARIO VE) ---

if not st.session_state.autenticado:
    # --- VISTA: LOGIN ---
    aplicar_estilo_login()
    st.markdown('<p class="title-jm">ACCESO A JM</p><p class="subtitle-jm">ALQUILER DE VEHÍCULOS</p>', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; margin-bottom: 30px;'>🔒</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.session_state.vista_login == "inicio":
            u = st.text_input("USUARIO / TELÉFONO")
            p = st.text_input("CONTRASEÑA", type="password")
            if st.button("INGRESAR AL SISTEMA"):
                if u == "admin" and p == "2026":
                    st.session_state.autenticado = True
                    st.session_state.role = "admin"
                    st.session_state.user_name = "ADMIN_MASTER"
                    st.rerun()
                elif u != "" and p != "":
                    st.session_state.autenticado = True
                    st.session_state.user_name = u
                    st.rerun()
                else:
                    st.error("Por favor, complete sus datos")
            
            st.divider()
            c1, c2 = st.columns(2)
            if c1.button("CREAR CUENTA"):
                st.session_state.vista_login = "registro"
                st.rerun()
            if c2.button("RECUPERAR"):
                st.session_state.vista_login = "recuperar"
                st.rerun()

        elif st.session_state.vista_login == "registro":
            st.markdown("<h3 style='color:#D4AF37; text-align:center;'>NUEVO REGISTRO</h3>", unsafe_allow_html=True)
            st.text_input("Nombre Completo")
            st.text_input("DNI / Documento")
            if st.button("GUARDAR DATOS"):
                st.success("¡Registro completado!")
                st.session_state.vista_login = "inicio"
                st.rerun()
            if st.button("⬅ VOLVER"):
                st.session_state.vista_login = "inicio"
                st.rerun()

else:
    # --- VISTA: APLICACIÓN PRINCIPAL ---
    aplicar_estilo_app()
    st.markdown('<div class="header-app"><h1>JM ASOCIADOS - GESTIÓN DE FLOTA</h1></div>', unsafe_allow_html=True)
    
    # Menú lateral para cerrar sesión
    st.sidebar.title(f"Bienvenido, {st.session_state.user_name}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Localización", "⭐ Reseñas", "🛡️ Panel Master"])

    # --- TAB 1: CATALOGO ---
    with tabs[0]:
        st.info(f"💰 Cotización del Real hoy: {cotizacion_hoy:,} PYG")
        flota = [
            {"nombre": "Toyota Vitz 2012 (Negro)", "precio": 195, "specs": "Automático | Nafta | Económico", "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
            {"nombre": "Hyundai Tucson 2012", "precio": 260, "specs": "4x2 | Diesel | Confort", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"nombre": "Toyota Voxy 2009", "precio": 240, "specs": "Familiar | 7 Pasajeros | Amplio", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
            {"nombre": "Toyota Vitz 2012 (Blanco)", "precio": 195, "specs": "Automático | Aire Full | Carta Verde", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
        ]

        for auto in flota:
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                        <img src="{auto['img']}" width="280" style="border-radius:10px;">
                        <div style="flex: 1;">
                            <h2 style="margin:0; color:#4A0404;">{auto['nombre']}</h2>
                            <p class="spec-label">{auto['specs']}</p>
                            <h3 style="color: #D4AF37;">Tarifa: R$ {auto['precio']} / día</h3>
                        </div>
                    </div>
                </div>''', unsafe_allow_html=True)
                
                with st.expander(f"Agendar {auto['nombre']}"):
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Recogida", min_value=date.today(), key=f"i_{auto['nombre']}")
                    f_f = c2.date_input("Devolución", min_value=f_i, key=f"f_{auto['nombre']}")
                    
                    if st.button(f"Validar Disponibilidad", key=f"btn_{auto['nombre']}"):
                        if check_disponibilidad(auto['nombre'], f_i, f_f):
                            dias = (f_f - f_i).days + 1
                            total_brl = dias * auto['precio']
                            st.success(f"✅ ¡Disponible! Total por {dias} días: R$ {total_brl}")
                            st.markdown(f"**🏦 PIX: 24510861818 | Marina Baez | Banco Santander**")
                            
                            mensaje_wa = f"Reserva JM: {st.session_state.user_name} - {auto['nombre']} del {f_i} al {f_f}. Total: R$ {total_brl}"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={mensaje_wa.replace(" ","%20")}" target="_blank" class="btn-wa">ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)
                            
                            # Guardar en DB
                            conn = sqlite3.connect('jm_asociados.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, auto['nombre'], f_i, f_f, total_brl, "Pendiente"))
                            conn.commit()
                            conn.close()
                        else:
                            st.error("❌ El auto ya está ocupado en esas fechas.")

    # --- TAB 5: PANEL MASTER (ADMIN) ---
    with tabs[4]:
        pin = st.text_input("Ingrese PIN Maestro para ver finanzas", type="password")
        if pin == "2026":
            st.title("📊 Evaluación de Rendimiento")
            conn = sqlite3.connect('jm_asociados.db')
            
            # Gestión de Egresos
            with st.expander("💸 Registrar Gasto (Lavado, Mecánico, Seguro)"):
                tipo = st.selectbox("Concepto", ["Lavado", "Mantenimiento", "Seguro", "Otros"])
                monto = st.number_input("Costo R$", min_value=0.0)
                if st.button("Guardar Gasto"):
                    conn.cursor().execute("INSERT INTO egresos (tipo, monto, fecha, descripcion) VALUES (?,?,?,?)", (tipo, monto, date.today(), tipo))
                    conn.commit()
                    st.success("Gasto registrado")

            # Estadísticas
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_eg = pd.read_sql_query("SELECT * FROM egresos", conn)
            
            col_in, col_eg, col_ut = st.columns(3)
            ing_t = df_res['monto_brl'].sum()
            egr_t = df_eg['monto'].sum()
            
            col_in.metric("INGRESOS ACTIVOS", f"R$ {ing_t}")
            col_eg.metric("EGRESOS PASIVOS", f"R$ {egr_t}")
            col_ut.metric("UTILIDAD NETA", f"R$ {ing_t - egr_t}")

            st.plotly_chart(px.pie(values=[ing_t, egr_t], names=['Ingresos', 'Gastos'], color_discrete_sequence=['#D4AF37', '#4A0404'], title="Balance Financiero"))
            
            if st.button("🗑 BORRAR TODO (PRUEBAS)"):
                conn.cursor().execute("DELETE FROM reservas")
                conn.cursor().execute("DELETE FROM egresos")
                conn.commit()
                st.rerun()
            
            conn.close()
