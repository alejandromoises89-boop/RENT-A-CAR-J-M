import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import locale
import styles

# --- CONFIGURACIÓN ---
try:
    locale.setlocale(locale.LC_ALL, 'es_PY.UTF-8')
except:
    pass

st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

DB_NAME = 'jm_corporativo_permanente.db'

def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES AUXILIARES ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        start = pd.to_datetime(row['inicio']).date()
        end = pd.to_datetime(row['fin']).date()
        for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disp = c.fetchone()[0] == 0
    conn.close()
    return disp

# --- INTERFAZ PÚBLICA ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / día</p></div>''', unsafe_allow_html=True)
            with st.expander("Ver Disponibilidad y Reservar"):
                # Calendario (Simplificado para estabilidad)
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                st.write(f"Fechas ocupadas: {len(ocupadas)} días registrados.")
                
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"i{v['nombre']}"), time(10,0))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"f{v['nombre']}"), time(12,0))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre", key=f"n{v['nombre']}")
                    c_d = st.text_input("Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    foto = st.file_uploader("Comprobante PIX", key=f"pic{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    
                    if st.button("Confirmar Reserva", key=f"btn{v['nombre']}"):
                        if c_n and c_d:
                            img_b = foto.read() if foto else None
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute('INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)',
                                         (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, img_b))
                            conn.commit(); conn.close()
                            
                            wa_txt = urllib.parse.quote(f"Hola JM, reserve el {v['nombre']} por R$ {total_r}. Soy {c_n}.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={wa_txt}" target="_blank" style="background-color:#25D366; color:white; padding:10px; border-radius:5px; display:block; text-align:center; text-decoration:none;">ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                            st.success("Reserva Exitosa"); st.balloons()
                else:
                    st.error("No disponible en estas fechas o está en taller.")

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.write("Ciudad del Este, Paraguay.")

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # 1. MÉTRICAS
        st.title("📊 PANEL ESTRATÉGICO")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("INGRESOS", f"R$ {ing:,.2f}", f"Gs. {ing*COTIZACION_DIA:,.0f}")
        c_m2.metric("GASTOS", f"R$ {egr:,.2f}", f"Gs. {egr*COTIZACION_DIA:,.0f}")
        c_m3.metric("UTILIDAD", f"R$ {ing-egr:,.2f}")

        # 2. GRÁFICOS
        if not res_df.empty:
            st.subheader("📈 VENTAS")
            res_df['fecha'] = pd.to_datetime(res_df['inicio']).dt.date
            fig = px.line(res_df.groupby('fecha')['total'].sum().reset_index(), x='fecha', y='total', title="Ventas Diarias (R$)")
            st.plotly_chart(fig, use_container_width=True)

        # 3. GESTIÓN DE FLOTA Y PRECIOS
        st.subheader("💰 CONFIGURACIÓN DE AUTOS")
        for _, f in flota_adm.iterrows():
            col1, col2, col3 = st.columns([2,1,1])
            with col1: st.write(f"**{f['nombre']}** ({f['estado']})")
            with col2: 
                nv_p = st.number_input(f"Precio R$", value=float(f['precio']), key=f"pr_{f['nombre']}")
                if nv_p != f['precio']:
                    conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (nv_p, f['nombre']))
                    conn.commit(); st.rerun()
            with col3:
                if st.button("TALLER/DISP", key=f"st_{f['nombre']}"):
                    nv_e = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                    conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nv_e, f['nombre']))
                    conn.commit(); st.rerun()

        # 4. GASTOS
        st.subheader("💸 CARGAR GASTO")
        with st.form("gastos"):
            con_g = st.text_input("Concepto")
            mon_g = st.number_input("Monto R$")
            if st.form_submit_button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con_g, mon_g, date.today()))
                conn.commit(); st.rerun()

        # 5. RESERVAS Y CONTRATOS
        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                contrato = f"CONTRATO J&M\nVehiculo: {r['auto']}\nCliente: {r['cliente']}\nDoc: {r['ci']}\nTotal: R$ {r['total']}\nFirmado Digitalmente."
                st.code(contrato)
                st.download_button("Descargar Contrato", contrato, f"Contrato_{r['id']}.txt", key=f"dl_{r['id']}")
                if r['comprobante']: st.image(r['comprobante'], width=300)
                if st.button("Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
