import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta, time
import calendar

# --- CONFIGURACIÓN DE ESTILO Y PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png"
)

# Estética original: Negro, Dorado y Blanco
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #D4AF37 !fo; text-align: center; font-family: 'Arial'; }
    .stButton>button { background-color: #D4AF37; color: black; border-radius: 10px; width: 100%; font-weight: bold; }
    .card-auto { 
        border: 2px solid #D4AF37; padding: 15px; border-radius: 20px; 
        background-color: #1c1f26; text-align: center; margin-bottom: 20px;
    }
    /* Estilo Calendario Airbnb */
    .airbnb-container { display: flex; gap: 20px; overflow-x: auto; padding: 10px; }
    .airbnb-month { min-width: 250px; background: #262730; padding: 10px; border-radius: 10px; }
    .airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
    .airbnb-cell { position: relative; height: 35px; display: flex; align-items: center; justify-content: center; font-size: 13px; }
    .occupied { background-color: #ff4b4b; border-radius: 50%; width: 25px; height: 25px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN GOOGLE SHEETS (CORREGIDA) ---
def conectar_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("LISTA ALQUILERES DE VEHICULOS-")
    except Exception as e:
        st.sidebar.error(f"Error conexión: {e}")
        return None

def obtener_datos_cloud():
    try:
        sh = conectar_google_sheets()
        if not sh: return pd.DataFrame()
        worksheet = sh.worksheet("reservas")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            # Limpiar nombres de columnas para evitar errores de espacios
            df.columns = [str(c).strip().upper() for c in df.columns]
            # Mapear columnas dinámicamente
            col_salida = next((c for c in df.columns if 'SALIDA' in c), None)
            col_entrega = next((c for c in df.columns if 'ENTREGA' in c), None)
            col_auto = next((c for c in df.columns if 'AUTO' in c), None)
            
            df['DT_INICIO'] = pd.to_datetime(df[col_salida], dayfirst=True, errors='coerce')
            df['DT_FIN'] = pd.to_datetime(df[col_entrega], dayfirst=True, errors='coerce')
            df['AUTO_CLEAN'] = df[col_auto].str.upper().str.strip()
        return df
    except:
        return pd.DataFrame()

# --- BASE DE DATOS LOCAL INTEGRADA ---
DB_NAME = 'jm_master_v5.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, placa TEXT, 
                color TEXT, km_actual INTEGER, km_cambio INTEGER, 
                venc_seguro DATE, cuota_venc DATE, estado TEXT)''')
    
    autos_iniciales = [
        ("HYUNDAI TUCSON BLANCO", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "AAVI502", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ BLANCO", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "AAVP719", "Blanco", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VITZ NEGRO", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "AAOR725", "Negro", 0, 5000, "2026-12-31", "2026-02-10", "Disponible"),
        ("TOYOTA VOXY GRIS", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "AAUG465", "Gris", 0, 5000, "2026-12-31", "2026-02-10", "Disponible")
    ]
    for a in autos_iniciales:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE COTIZACIÓN ---
def get_pyg():
    try: return requests.get("https://open.er-api.com/v6/latest/BRL").json()['rates']['PYG']
    except: return 1450.0

GS_BRL = get_pyg()

# --- INTERFAZ PRINCIPAL ---
st.image("https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png", width=200)
st.markdown("<h1>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)

tabs = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

# --- PESTAÑA 1: RESERVAS ---
with tabs[0]:
    df_cloud = obtener_datos_cloud()
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    
    col1, col2 = st.columns(2)
    for i, (_, car) in enumerate(flota.iterrows()):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
                <div class="card-auto">
                    <h2 style="color:#D4AF37;">{car['nombre']}</h2>
                    <img src="{car['img']}" width="100%">
                    <p style="font-size:22px;">R$ {car['precio']} / Gs. {car['precio']*GS_BRL:,.0f}</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📅 VER DISPONIBILIDAD Y RESERVAR"):
                # Calendario Estilo Airbnb
                ocupadas = set()
                if not df_cloud.empty:
                    df_res = df_cloud[df_cloud['AUTO_CLEAN'] == car['nombre'].upper()]
                    for _, r in df_res.iterrows():
                        if pd.notnull(r['DT_INICIO']):
                            dias = (r['DT_FIN'].date() - r['DT_INICIO'].date()).days + 1
                            for d in range(dias): ocupadas.add(r['DT_INICIO'].date() + timedelta(days=d))
                
                # Mostrar 2 meses
                cal_cols = st.columns(2)
                for m_idx, m_offset in enumerate([0, 1]):
                    curr_date = date.today() + timedelta(days=30*m_offset)
                    with cal_cols[m_idx]:
                        st.write(f"**{calendar.month_name[curr_date.month]} {curr_date.year}**")
                        month_cal = calendar.monthcalendar(curr_date.year, curr_date.month)
                        for week in month_cal:
                            w_cols = st.columns(7)
                            for d_idx, day in enumerate(week):
                                if day != 0:
                                    f_cal = date(curr_date.year, curr_date.month, day)
                                    if f_cal in ocupadas: w_cols[d_idx].markdown(f'<div class="occupied">{day}</div>', unsafe_allow_html=True)
                                    else: w_cols[d_idx].write(day)

                st.divider()
                f_ini = st.date_input("Fecha Retiro", key=f"ini{car['nombre']}")
                f_fin = st.date_input("Fecha Entrega", key=f"fin{car['nombre']}")
                
                if st.button("SOLICITAR POR WHATSAPP", key=f"wa{car['nombre']}"):
                    msg = f"Hola JM! Quiero reservar el {car['nombre']} del {f_ini} al {f_fin}."
                    url = f"https://wa.me/595983515320?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank">Click aquí para abrir WhatsApp</a>', unsafe_allow_html=True)

# --- PESTAÑA 2: UBICACIÓN ---
with tabs[1]:
    st.markdown("### 📍 Nuestra Oficina")
    st.markdown("""
        <div style="border:2px solid #D4AF37; border-radius:15px; overflow:hidden;">
            <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.503460838936!2d-54.613!3d-25.513!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ2LjgiUyA1NMKwMzYnNDYuOCJX!5e0!3m2!1ses!2spy!4v1620000000000" 
            width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
        </div>
    """, unsafe_allow_html=True)

# --- PESTAÑA 3: ADMINISTRADOR ---
with tabs[2]:
    pwd = st.text_input("Clave de Acceso", type="password")
    if pwd == "8899":
        conn = sqlite3.connect(DB_NAME)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # 1. BUSCADOR DE CLIENTES (EXCEL)
        st.subheader("🔍 BUSCADOR DE CONTRATOS")
        df_adm = obtener_datos_cloud()
        busq = st.text_input("Nombre del cliente o auto...")
        if not df_adm.empty:
            if busq:
                df_adm = df_adm[df_adm.apply(lambda row: busq.upper() in str(row.values).upper(), axis=1)]
            st.dataframe(df_adm, use_container_width=True)
        else: st.warning("No se detectan datos en el Excel.")

        # 2. GESTIÓN DE FLOTA Y MANTENIMIENTO
        st.divider()
        st.subheader("⚙️ GESTIÓN DE FLOTA")
        for idx, row in flota_adm.iterrows():
            with st.expander(f"🚗 {row['nombre']} - {row['placa']}"):
                c1, c2, c3 = st.columns(3)
                # Edición de datos básicos
                n_precio = c1.number_input("Precio Día", value=float(row['precio']), key=f"p{idx}")
                n_km_a = c2.number_input("KM Actual", value=int(row['km_actual']), key=f"k{idx}")
                n_km_c = c3.number_input("Próx. Cambio Aceite", value=int(row['km_cambio']), key=f"kc{idx}")
                
                n_seg = c1.date_input("Venc. Seguro", value=pd.to_datetime(row['venc_seguro']).date(), key=f"s{idx}")
                n_cuo = c2.date_input("Venc. Cuota", value=pd.to_datetime(row['cuota_venc']).date(), key=f"cu{idx}")
                n_est = c3.selectbox("Estado", ["Disponible", "En Taller"], index=0 if row['estado']=="Disponible" else 1, key=f"es{idx}")
                
                # ALERTAS
                if n_km_a >= n_km_c: st.error("🚨 REQUIERE CAMBIO DE ACEITE")
                if (n_seg - date.today()).days < 10: st.warning(f"⚠️ SEGURO VENCE EN {(n_seg - date.today()).days} DÍAS")

                if st.button("GUARDAR CAMBIOS", key=f"btn{idx}"):
                    conn.execute("""UPDATE flota SET precio=?, km_actual=?, km_cambio=?, venc_seguro=?, cuota_venc=?, estado=? 
                                 WHERE nombre=?""", (n_precio, n_km_a, n_km_c, n_seg, n_cuo, n_est, row['nombre']))
                    conn.commit(); st.rerun()

        # 3. EGRESOS
        st.divider()
        st.subheader("💸 REGISTRO DE GASTOS")
        with st.form("gasto_nuevo"):
            c1, c2 = st.columns(2)
            conc = c1.text_input("Concepto")
            mont = c2.number_input("Monto R$")
            if st.form_submit_button("REGISTRAR GASTO"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (conc, mont, date.today()))
                conn.commit(); st.success("Gasto guardado"); st.rerun()
        
        conn.close()
