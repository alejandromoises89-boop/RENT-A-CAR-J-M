import streamlit as st
import sqlite3
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER DE VEHICULOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- FUNCIONES GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Aquí es donde busca la clave que te daba error
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("LISTA ALQUILERES DE VEHICULOS-")
        return spreadsheet
    except Exception as e:
        return None

def obtener_datos_cloud():
    try:
        sh = conectar_google_sheets()
        if not sh: return pd.DataFrame()
        worksheet = sh.worksheet("reservas")
        df = pd.DataFrame(worksheet.get_all_records())
        if not df.empty:
            df.columns = [str(c).strip().upper() for c in df.columns]
            # Mapeo flexible de columnas
            c_sal = next((c for c in [' SALIDA', 'SALIDA', 'INICIO'] if c in df.columns), df.columns[5] if len(df.columns)>5 else None)
            c_ent = next((c for c in [' ENTREGA', 'ENTREGA', 'FIN'] if c in df.columns), df.columns[6] if len(df.columns)>6 else None)
            c_aut = next((c for c in ['AUTO', 'VEHICULO'] if c in df.columns), df.columns[4] if len(df.columns)>4 else None)
            
            df['inicio'] = pd.to_datetime(df[c_sal], errors='coerce')
            df['fin'] = pd.to_datetime(df[c_ent], errors='coerce')
            df['auto_excel'] = df[c_aut].str.upper().str.strip()
            if 'TOTAL' in df.columns:
                df['TOTAL_NUM'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# --- BASE DE DATOS LOCAL ---
DB_NAME = 'jm_sistema_integral_v4.db' # Nueva versión para evitar conflictos de columnas

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
                nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, 
                placa TEXT, color TEXT, km_actual INTEGER, km_cambio INTEGER, 
                venc_seguro DATE, cuota_venc DATE)''')

    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", 0, 5000, "2026-12-31", "2026-02-10"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris", 0, 5000, "2026-12-31", "2026-02-10")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE NEGOCIO ---
def obtener_cotizacion():
    try: return round(requests.get("https://open.er-api.com/v6/latest/BRL").json()['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion()

def obtener_fechas_ocupadas(nombre_auto_app):
    df = obtener_datos_cloud()
    bloqueadas = set()
    if df.empty: return bloqueadas
    busqueda = nombre_auto_app.upper()
    # Mapeo para coincidir con Excel
    if "VOXY" in busqueda: busqueda = "VOXY GRIS"
    elif "VITZ NEGRO" in busqueda: busqueda = "VITZ NEGRO"
    elif "VITZ BLANCO" in busqueda: busqueda = "VITZ BLANCO"
    elif "TUCSON" in busqueda: busqueda = "HYUNDAI TUCSON BLANCO"
    
    if 'auto_excel' in df.columns:
        df_auto = df[df['auto_excel'] == busqueda]
        for _, row in df_auto.iterrows():
            if pd.notnull(row['inicio']) and pd.notnull(row['fin']):
                dias = (row['fin'].date() - row['inicio'].date()).days + 1
                for i in range(dias):
                    bloqueadas.add(row['inicio'].date() + timedelta(days=i))
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    # Verificación local
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    if (res := c.fetchone()) and res[0] == "En Taller": return False
    # Verificación en Nube
    ocupadas = obtener_fechas_ocupadas(auto)
    for i in range((t_fin.date() - t_ini.date()).days + 1):
        if (t_ini.date() + timedelta(days=i)) in ocupadas: return False
    return True

# --- INTERFAZ DE USUARIO ---
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>JM ALQUILER DE VEHICULOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div style="border:1px solid #D4AF37; padding:15px; border-radius:15px; margin-bottom:20px; text-align:center;">
                <h3>{v["nombre"]}</h3>
                <img src="{v["img"]}" width="100%" style="max-height:200px; object-fit:contain;">
                <p style="font-size:20px; color:#D4AF37;">R$ {v["precio"]} / Gs. {v["precio"]*COTIZACION_DIA:,.0f} por día</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander("📅 VER DISPONIBILIDAD Y RESERVAR"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                # Calendario Visual (Simplificado para estabilidad)
                hoy = date.today()
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Inicio", hoy, key=f"f1{v['nombre']}")
                f_fin = c2.date_input("Fin", hoy + timedelta(days=1), key=f"f2{v['nombre']}")
                
                if esta_disponible(v['nombre'], datetime.combine(f_ini, time(8,0)), datetime.combine(f_fin, time(17,0))):
                    nombre = st.text_input("Nombre Completo", key=f"nom{v['nombre']}")
                    doc = st.text_input("Documento (CI/RG)", key=f"doc{v['nombre']}")
                    whatsapp = st.text_input("WhatsApp", key=f"wa{v['nombre']}")
                    
                    if nombre and doc and whatsapp:
                        dias = max(1, (f_fin - f_ini).days)
                        total_r = dias * v['precio']
                        st.success(f"Disponible! Total: R$ {total_r}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            # Guardar en Nube
                            sh = conectar_google_sheets()
                            if sh:
                                sh.worksheet("reservas").append_row([datetime.now().strftime("%d/%m/%Y"), nombre, doc, whatsapp, v['nombre'], f_ini.strftime("%d/%m/%Y"), f_fin.strftime("%d/%m/%Y"), total_r])
                                st.balloons()
                                st.success("Registrado en Excel y Base de Datos!")
                else:
                    st.error("Vehículo no disponible en estas fechas.")

with t_ubi:
    st.markdown("### Nuestra Ubicación en Ciudad del Este")
    # Mapa real
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.373950636833!2d-54.6111!3d-25.5133!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ3LjkiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1620000000000!5m2!1ses!2spy" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Maestra", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = obtener_datos_cloud()
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # 1. Buscador y Gestión de Excel
        st.subheader("🔍 Buscador de Clientes (Excel)")
        busq = st.text_input("Escriba nombre del cliente...")
        if not res_df.empty:
            if busq: res_df = res_df[res_df['NOMBRE'].str.contains(busq, case=False, na=False)]
            st.dataframe(res_df, use_container_width=True)
        
        # 2. Métricas
        st.divider()
        ing_total = res_df['TOTAL_NUM'].sum() if 'TOTAL_NUM' in res_df.columns else 0
        st.metric("INGRESOS TOTALES (R$)", f"{ing_total:,.2f}")

        # 3. Gestión de Flota, Mantenimiento y Precios
        st.subheader("🛠️ Control de Flota y Alertas")
        for idx, row in flota_adm.iterrows():
            with st.expander(f"🚗 {row['nombre']} ({row['placa']})"):
                c1, c2, c3 = st.columns(3)
                # Editar Básicos
                new_p = c1.number_input("Precio Día (R$)", value=float(row['precio']), key=f"p{idx}")
                new_est = c2.selectbox("Estado", ["Disponible", "En Taller"], index=0 if row['estado']=="Disponible" else 1, key=f"e{idx}")
                new_km_a = c3.number_input("KM Actual", value=int(row['km_actual']), key=f"kma{idx}")
                
                # Mantenimiento y Seguros
                new_km_c = c1.number_input("Próx. Cambio Aceite", value=int(row['km_cambio']), key=f"kmc{idx}")
                new_seg = c2.date_input("Venc. Seguro", value=pd.to_datetime(row['venc_seguro']).date(), key=f"vs{idx}")
                new_cuo = c3.date_input("Venc. Cuota/Seguro", value=pd.to_datetime(row['cuota_venc']).date(), key=f"vc{idx}")
                
                # Alertas Logias
                if new_km_a >= new_km_c: st.error(f"🚨 CAMBIO DE ACEITE URGENTE (Faltan {new_km_c - new_km_a} km)")
                if (new_seg - date.today()).days < 10: st.warning(f"⚠️ SEGURO VENCE EN {(new_seg - date.today()).days} DÍAS")
                
                if st.button("GUARDAR CAMBIOS", key=f"sav{idx}"):
                    conn.execute("""UPDATE flota SET precio=?, estado=?, km_actual=?, km_cambio=?, venc_seguro=?, cuota_venc=? 
                                 WHERE nombre=?""", (new_p, new_est, new_km_a, new_km_c, new_seg, new_cuo, row['nombre']))
                    conn.commit()
                    st.success("Actualizado correctamente")
                    st.rerun()

        # 4. Gastos
        st.divider()
        st.subheader("💸 Registro de Gastos")
        with st.form("gastos"):
            conc = st.text_input("Concepto")
            mont = st.number_input("Monto R$")
            if st.form_submit_button("Registrar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (conc, mont, date.today()))
                conn.commit(); st.rerun()
        
        conn.close()
