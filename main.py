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

# Intentar aplicar estilos externos
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

# --- NUEVO CSS PARA CALENDARIO FIJO (RESPONSIVO Y ALINEADO) ---
st.markdown("""
    <style>
    .cal-header { 
        font-size: 16px; font-weight: bold; text-align: center; 
        margin: 15px 0 5px 0; color: #333; text-transform: capitalize;
    }
    .cal-grid-fijo { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 0px; 
        max-width: 320px; 
        margin: 0 auto; 
        border: 0.2px solid #eee;
    }
    .cal-box-fijo { 
        aspect-ratio: 1/1; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 12px; 
        position: relative; 
        background: white; 
        color: #222;
        border: 0.1px solid #f7f7f7;
    }
    .cal-day-name-fijo {
        text-align: center;
        font-size: 10px;
        color: #717171;
        font-weight: bold;
        padding-bottom: 5px;
    }
    .ocupado { color: #ccc !important; background-color: #fafafa; }
    .raya-roja-h { 
        position: absolute; width: 80%; height: 1.5px; 
        background-color: #ff385c; z-index: 1; top: 50%;
    }
    .card-auto { border: 1px solid #ddd; padding: 15px; border-radius: 15px; background: white; text-align: center; }
    .pix-box { background-color: #f8f9fa; border: 2px dashed #D4AF37; padding: 15px; border-radius: 10px; margin-top: 10px; text-align: center; }
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

# --- FUNCIONES DE APOYO ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    if c.fetchone()[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    res = c.fetchone()[0] == 0
    conn.close(); return res

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37;">R$ {v["precio"]} / Gs. {precio_gs:,.0f}</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                hoy = date.today()
                meses = [(hoy.month, hoy.year), ((hoy.month % 12) + 1, hoy.year if hoy.month < 12 else hoy.year + 1)]
                
                col_izq, col_der = st.columns(2)
                for idx, (m, a) in enumerate(meses):
                    target_col = col_izq if idx == 0 else col_der
                    with target_col:
                        st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                        dias_html = "".join([f'<div class="cal-day-name-fijo">{d}</div>' for d in ["L","M","M","J","V","S","D"]])
                        cal_data = calendar.monthcalendar(a, m)
                        dias_grid_html = ""
                        for semana in cal_data:
                            for dia in semana:
                                if dia == 0:
                                    dias_grid_html += '<div class="cal-box-fijo" style="background:transparent; border:none;"></div>'
                                else:
                                    f_act = date(a, m, dia)
                                    es_ocu = f_act in ocupadas
                                    clase = "cal-box-fijo ocupado" if es_ocu else "cal-box-fijo"
                                    raya = '<div class="raya-roja-h"></div>' if es_ocu else ""
                                    dias_grid_html += f'<div class="{clase}">{dia}{raya}</div>'
                        st.markdown(f'<div class="cal-grid-fijo">{dias_html}{dias_grid_html}</div>', unsafe_allow_html=True)

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
                        st.markdown(f'<div style="background-color:#2b0606; color:#f1f1f1; padding:20px; border:1px solid #D4AF37; border-radius:10px; height:200px; overflow-y:scroll; font-size:13px;"><b>CONTRATO JM ASOCIADOS</b><br>Arrendatario: {c_n.upper()}<br>Vehículo: {v["nombre"]}<br>Monto: R$ {total_r}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read())); conn.commit(); conn.close()
                            st.success("¡Reserva Guardada!"); st.rerun()
                else: st.error("No disponible en esas fechas.")

with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        st.title("📊 PANEL DE CONTROL")
        ing, egr = res_df['total'].sum() if not res_df.empty else 0, egr_df['monto'].sum() if not egr_df.empty else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("INGRESOS", f"R$ {ing:,.2f}"); c2.metric("GASTOS", f"R$ {egr:,.2f}"); c3.metric("UTILIDAD", f"R$ {ing-egr:,.2f}")

        col_g1, col_g2 = st.columns(2)
        if not res_df.empty:
            with col_g1: st.plotly_chart(px.pie(res_df, values='total', names='auto', hole=0.4, title="Ingresos por Auto"))
            with col_g2: st.plotly_chart(px.bar(x=["Ingresos", "Gastos"], y=[ing, egr], title="Balance Mensual"))

        with st.expander("💸 CARGAR GASTO"):
            with st.form("g"):
                con = st.text_input("Concepto"); mon = st.number_input("Monto R$")
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, date.today())); conn.commit(); st.rerun()

        st.subheader("📑 RESERVAS REGISTRADAS")
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                st.write(f"CI: {r['ci']} | Cel: {r['celular']} | Total: R$ {r['total']}")
                if r['comprobante']: st.image(r['comprobante'], width=200)
                if st.button("BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
