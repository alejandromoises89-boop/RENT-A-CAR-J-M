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
        .header-jm { text-align: center; color: #D4AF37; margin-bottom: 10px; }
        .cotizacion-texto { text-align: center; color: #D4AF37; font-weight: bold; font-size: 1.1rem; margin-bottom: 20px; border: 1px solid #D4AF37; padding: 10px; border-radius: 10px; background: rgba(255,255,255,0.05); }
        .card-auto { background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #D4AF37; }
        .btn-notif { display: flex; align-items: center; justify-content: center; padding: 15px; border-radius: 12px; text-decoration: none !important; font-weight: bold; font-size: 16px; margin-top: 10px; width: 100%; transition: 0.3s ease; border: none; }
        .btn-whatsapp { background-color: #25D366; color: white !important; box-shadow: 0 4px #128C7E; }
        .btn-email { background-color: #D4AF37; color: black !important; box-shadow: 0 4px #b08d2c; }
        .btn-icon { margin-right: 12px; font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS MEJORADA ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    # Tabla de Reservas
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto_pyg REAL, monto_brl REAL, fecha_registro TEXT)''')
    # Tabla de Mantenimiento
    c.execute('''CREATE TABLE IF NOT EXISTS mantenimiento 
                 (id INTEGER PRIMARY KEY, auto TEXT, servicio TEXT, costo_brl REAL, fecha TEXT)''')
    conn.commit()
    conn.close()

def obtener_cotizacion_brl():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/BRL"
        r = requests.get(url)
        return round(r.json()['rates']['PYG'])
    except: return 1450 

cotizacion_hoy = obtener_cotizacion_brl()
init_db()

# --- 3. FLOTA (ORDEN SOLICITADO) ---
flota = [
    {"nombre": "Toyota Vitz", "color": "Negro", "precio_brl": 195, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio_brl": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio_brl": 240, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio_brl": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. INTERFAZ ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M ASOCIADOS</h1></div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div id="inicio"></div><div class="header-jm"><h1>J&M ASOCIADOS</h1></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cotizacion-texto">📊 Cotización Real hoy: 1 BRL = {cotizacion_hoy:,} PYG</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "⚙️ Panel Master"])

    with tabs[0]:
        for idx, auto in enumerate(flota):
            monto_pyg = auto['precio_brl'] * cotizacion_hoy
            auto_id = f"veh_{idx}"
            with st.container():
                st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1: st.image(auto['img'], use_container_width=True)
                with c2:
                    st.subheader(f"{auto['nombre']} - {auto['color']}")
                    st.write(f"Tarifa: {auto['precio_brl']} BRL / Gs. {monto_pyg:,}")
                    f_i = st.date_input("Inicio", key=f"i_{auto_id}")
                    f_f = st.date_input("Fin", key=f"f_{auto_id}")
                    if st.button("Alquilar", key=f"btn_{auto_id}"):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_pyg, monto_brl, fecha_registro) VALUES (?,?,?,?,?,?,?)",
                                             (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", str(f_i), str(f_f), monto_pyg, auto['precio_brl'], datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.markdown(f'''<div id="conf_{auto_id}" style="background:rgba(212,175,55,0.1); padding:15px; border-radius:10px; border:1px solid #D4AF37; text-align:center;">
                            <h3 style="color:#D4AF37;">✅ Reserva Registrada</h3>
                            <a href="https://wa.me/595991681191" class="btn-notif btn-whatsapp"><i class="fa-brands fa-whatsapp btn-icon"></i> WhatsApp</a>
                            <script>document.getElementById("conf_{auto_id}").scrollIntoView({{behavior: "smooth"}});</script>
                        </div>''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[1]:
            st.title("📊 Dashboard de Metas 2026")
            conn = sqlite3.connect('jm_asociados.db')
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_mante = pd.read_sql_query("SELECT * FROM mantenimiento", conn)
            
            # --- SECCIÓN FINANCIERA ---
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Ingresos Totales (BRL)", f"{df_res['monto_brl'].sum():,} R$")
            col_m2.metric("Ingresos Totales (PYG)", f"{df_res['monto_pyg'].sum():,} Gs.")
            col_m3.metric("Reservas Totales", len(df_res))

            # --- GRÁFICOS ---
            st.subheader("📈 Rendimiento por Vehículo")
            if not df_res.empty:
                chart_data = df_res['auto'].value_counts()
                st.bar_chart(chart_data)

            # --- MANTENIMIENTO ---
            st.subheader("🔧 Registro de Mantenimiento")
            with st.expander("Añadir Gasto de Mantenimiento"):
                m_auto = st.selectbox("Vehículo", [f"{a['nombre']} {a['color']}" for a in flota])
                m_serv = st.text_input("Descripción (Aceite, Cubiertas, etc.)")
                m_cost = st.number_input("Costo en BRL", min_value=0.0)
                if st.button("Guardar Mantenimiento"):
                    conn.cursor().execute("INSERT INTO mantenimiento (auto, servicio, costo_brl, fecha) VALUES (?,?,?,?)",
                                         (m_auto, m_serv, m_cost, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Gasto registrado")

            # --- EXPORTACIÓN ---
            st.subheader("📥 Exportar Datos para Exposición")
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Reporte de Reservas (Excel/CSV)", csv, "reporte_jm_2026.csv", "text/csv")
            
            st.write("Detalle de Reservas:")
            st.dataframe(df_res)
            conn.close()
