import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

# Intentar aplicar los estilos premium si el archivo existe
try:
    import styles
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()
DB_NAME = 'jm_corporativo_permanente.db'

# --- ESTILOS CSS (CALENDARIO AIRBNB + SELECCIÓN BORDO) ---
st.markdown("""
    <style>
    .cal-header { font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0 5px 0; color: #333; text-transform: capitalize; }
    .cal-grid-fijo { 
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 0px; 
        max-width: 320px; margin: 0 auto; border: 0.2px solid #eee;
    }
    .cal-box-fijo { 
        aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; 
        font-size: 12px; position: relative; background: white; color: #222; border: 0.1px solid #f7f7f7;
    }
    .cal-day-name-fijo { text-align: center; font-size: 10px; color: #717171; font-weight: bold; padding-bottom: 5px; }
    .ocupado { color: #ccc !important; background-color: #fafafa; }
    .raya-roja-h { position: absolute; width: 80%; height: 1.5px; background-color: #ff385c; z-index: 1; top: 50%; }
    
    /* Estilo de Tarjeta y Selección Bordo */
    .card-auto { 
        border: 1px solid #ddd; padding: 15px; border-radius: 15px; 
        background: white; transition: 0.3s; text-align: center;
    }
    .stExpander { border: none !important; }
    
    /* Cuando el expander está abierto (simulando selección), el fondo cambia a bordo */
    [data-embedded-multi-theme="true"] .stExpander:has(input:checked) {
        background-color: #800020 !important;
        color: white !important;
    }
    
    .pix-box { background-color: #f8f9fa; border: 2px dashed #D4AF37; padding: 15px; border-radius: 10px; margin-top: 10px; color: #333; }
    .card-auto img { filter: drop-shadow(0px 8px 8px rgba(0,0,0,0.25)); }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE VALIDACIÓN ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res_estado = c.fetchone()
    if res_estado and res_estado[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close(); return disponible

# --- INTERFAZ JM ASOCIADOS ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / Gs. {precio_gs:,.0f}</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad y Reservar"):
                # CALENDARIO DE GRID FIJO
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                hoy = date.today()
                meses = [(hoy.month, hoy.year), ((hoy.month % 12) + 1, hoy.year if hoy.month < 12 else hoy.year + 1)]
                
                c_m1, c_m2 = st.columns(2)
                for idx, (m, a) in enumerate(meses):
                    with [c_m1, c_m2][idx]:
                        st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                        dias_header = "".join([f'<div class="cal-day-name-fijo">{d}</div>' for d in ["L","M","M","J","V","S","D"]])
                        cal_data = calendar.monthcalendar(a, m)
                        dias_body = ""
                        for sem in cal_data:
                            for d in sem:
                                if d == 0: dias_body += '<div class="cal-box-fijo" style="background:transparent; border:none;"></div>'
                                else:
                                    f_act = date(a, m, d)
                                    es_o = f_act in ocupadas
                                    raya = '<div class="raya-roja-h"></div>' if es_o else ""
                                    dias_body += f'<div class="cal-box-fijo {"ocupado" if es_o else ""}">{d}{raya}</div>'
                        st.markdown(f'<div class="cal-grid-fijo">{dias_header}{dias_body}</div>', unsafe_allow_html=True)

                st.divider()
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    dias = max(1, (dt_f - dt_i).days); total_r = dias * v['precio']
                    
                    if c_n and c_d and c_w:
                        st.markdown(f'<div style="background-color:#2b0606; color:#f1f1f1; padding:20px; border:1px solid #D4AF37; border-radius:10px; height:200px; overflow-y:scroll; font-size:13px;"><b>CONTRATO JM ASOCIADOS</b><br>Vehículo: {v["nombre"]}<br>Total: R$ {total_r}<br><br>Usted acepta los términos de uso y responsabilidad civil/penal.</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Subir Comprobante", key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read())); conn.commit(); conn.close()
                            st.success("Reserva Guardada!"); st.rerun()
                else: st.error("Fechas no disponibles.")

with t_ubi:
    st.markdown("### 📍 Ubicación")
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.3787754904!2d-54.6111!3d-25.5134!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ4LjIiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1625612345678!5m2!1ses!2spy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        i_t, e_t = (res_df['total'].sum() if not res_df.empty else 0), (egr_df['monto'].sum() if not egr_df.empty else 0)
        c1, c2, c3 = st.columns(3)
        c1.metric("INGRESOS", f"R$ {i_t:,.2f}"); c2.metric("GASTOS", f"R$ {e_t:,.2f}"); c3.metric("UTILIDAD", f"R$ {i_t-e_t:,.2f}")

        cg1, cg2 = st.columns(2)
        if not res_df.empty:
            with cg1: st.plotly_chart(px.pie(res_df, values='total', names='auto', hole=0.4, title="Ventas por Auto"))
            with cg2: st.plotly_chart(px.bar(res_df, x='inicio', y='total', title="Evolución"))

        with st.expander("💸 REGISTRAR GASTO"):
            with st.form("g"):
                con = st.text_input("Concepto"); mon = st.number_input("Monto R$")
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, date.today())); conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2,1,1])
            ca1.write(f"**{f['nombre']}** ({f['placa']})")
            ca2.write("🟢 Disponible" if f['estado'] == "Disponible" else "🔴 Taller")
            if ca3.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre'])); conn.commit(); st.rerun()

        st.subheader("📑 RESERVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | {r['inicio']} a {r['fin']}")
                if r['comprobante']: st.image(r['comprobante'], width=200)
                if st.button("BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()