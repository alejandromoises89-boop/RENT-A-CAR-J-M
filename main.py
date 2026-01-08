import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("<style>body{background-color:#0e1117; color:white;}</style>", unsafe_allow_html=True)

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

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/cK92Y5Hf/tucson-Photoroom.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
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
            for i in range((end - start).days + 1): 
                bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p><p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses_display = [(date.today().month, date.today().year), 
                                 ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]

                html_cal = '<div style="display: flex; flex-direction: row; gap: 20px; overflow-x: auto; padding: 10px 0;">'
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div style="min-width: 200px;"><div style="font-weight: 600; color: white; text-transform: capitalize; margin-bottom:12px;">{nombre_mes} {a}</div><div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center;">'
                    for d_nom in ["L","M","M","J","V","S","D"]: html_cal += f'<div style="font-size: 11px; color: #888;">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia)
                                es_ocu = f_act in ocupadas
                                color = "color: #555;" if es_ocu else "color: white;"
                                raya = '<div style="position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; left:0;"></div>' if es_ocu else ""
                                html_cal += f'<div style="position: relative; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; {color}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)
                st.divider()

                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(10,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(12,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    c_pais = st.text_input("País / Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f"""<div style="background-color: #f9f9f9; color: #333; padding: 25px; border-radius: 10px; height: 300px; overflow-y: scroll; font-family: monospace; border: 2px solid #D4AF37;">
                            <center><b>CONTRATO DE ALQUILER - JM ASOCIADOS</b></center><br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}<br><b>DOC:</b> {c_d.upper()}<br><b>AUTO:</b> {v['nombre'].upper()}<br>
                            <b>DURACIÓN:</b> {dias} días ({dt_i.strftime('%d/%m')} al {dt_f.strftime('%d/%m')})<br>
                            <b>TOTAL: Gs. {total_gs:,.0f} (R$ {total_r})</b><br><br>
                            <b>CLÁUSULAS:</b> El arrendatario es responsable penal y civilmente. Se incluye cobertura MERCOSUR. Límite de 200km diarios.
                        </div>""", unsafe_allow_html=True)
                        acepto = st.checkbox("He leído y acepto los términos", key=f"chk{v['nombre']}")
                        st.info(f"PAGO PIX: R$ {total_r} | Llave: 24510861818")
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}", disabled=not acepto):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                txt_wa = f"Hola JM, soy {c_n}. Reservé {v['nombre']} por R$ {total_r}. Acepto el contrato."
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(txt_wa)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; display:block; text-decoration:none; font-weight:bold;">✅ ENVIAR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva Guardada!")
                else:
                    st.error("Vehículo no disponible en estas fechas.")

with t_ubi:
    st.markdown("<h3 style='text-align: center;'>UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        ing_r = res_df['total'].sum() if not res_df.empty else 0
        egr_r = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("INGRESOS", f"R$ {ing_r:,.2f}", f"Gs. {ing_r*COTIZACION_DIA:,.0f}")
        c_m2.metric("GASTOS", f"R$ {egr_r:,.2f}", f"Gs. {egr_r*COTIZACION_DIA:,.0f}")
        c_m3.metric("UTILIDAD", f"R$ {ing_r-egr_r:,.2f}")

        if not res_df.empty:
            st.subheader("📈 GRÁFICO DE VENTAS")
            res_df['inicio_dt'] = pd.to_datetime(res_df['inicio'])
            fig = px.line(res_df.sort_values('inicio_dt'), x='inicio_dt', y='total', markers=True, title="Evolución de Ingresos (R$)")
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("📥 Descargar Reporte CSV", res_df.to_csv(index=False), "reporte_jm.csv")

        st.subheader("💰 AJUSTAR PRECIOS")
        for _, f in flota_adm.iterrows():
            cp1, cp2 = st.columns([3, 1])
            cp1.write(f"{f['nombre']} ({f['placa']})")
            n_p = cp2.number_input("R$/día", value=float(f['precio']), key=f"pr_{f['nombre']}")
            if n_p != f['precio']:
                conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (n_p, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE TALLER")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2, 1, 1])
            ca1.write(f['nombre'])
            ca2.write("🟢 Disponible" if f['estado'] == "Disponible" else "🔴 Taller")
            if ca3.button("CAMBIAR", key=f"st_{f['nombre']}"):
                nv_e = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nv_e, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("💸 REGISTRAR GASTO")
        with st.form("g_form"):
            det_g = st.text_input("Concepto")
            mon_g = st.number_input("Monto R$")
            if st.form_submit_button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (det_g, mon_g, date.today()))
                conn.commit(); st.rerun()

        st.subheader("📅 BLOQUEO MANUAL")
        with st.form("m_form"):
            cli_m = st.text_input("Nombre Cliente")
            aut_m = st.selectbox("Vehículo", flota_adm['nombre'].tolist())
            ini_m = st.date_input("Inicio")
            fin_m = st.date_input("Fin")
            if st.form_submit_button("Bloquear Fecha"):
                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total) VALUES (?,?,?,?,?,?,?)",
                             (f"[M] {cli_m}", "MANUAL", "000", aut_m, ini_m, fin_m, 0.0))
                conn.commit(); st.rerun()

        st.subheader("📑 LISTADO DE RESERVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | Total: R$ {r['total']}")
                st.download_button(f"📥 Contrato {r['id']}", f"CONTRATO JM\nCliente: {r['cliente']}\nVehículo: {r['auto']}", f"Contrato_{r['id']}.txt")
                if r['comprobante']: st.image(r['comprobante'], width=300)
                if st.button("🗑️ Borrar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
