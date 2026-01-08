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

# Aplicar estilos si el archivo existe
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("<style>body{background-color:#111; color:white;}</style>", unsafe_allow_html=True)

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
    
    # Datos iniciales si la flota está vacía
    c.execute("SELECT COUNT(*) FROM flota")
    if c.fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
            ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
            ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
        ]
        c.executemany("INSERT INTO flota VALUES (?,?,?,?,?,?)", autos)
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
    disp = c.fetchone()[0] == 0
    conn.close()
    return disp

# --- INTERFAZ ---
st.markdown("<h1 style='text-align:center;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

# --- TAB 1: RESERVAS ---
with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()
    
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto" style="border:1px solid #333; padding:15px; border-radius:15px; margin-bottom:10px;">
                    <h3 style="color:#D4AF37;">{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%" style="border-radius:10px;">
                    <p style="font-weight:bold; font-size:20px; margin-top:10px;">R$ {v["precio"]} / día</p>
                    <p style="color:#28a745;">Gs. {v["precio"]*COTIZACION_DIA:,.0f} / día</p>
                </div>
            ''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad y Alquilar"):
                # Calendario Airbnb Style
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses = [(date.today().month, date.today().year), 
                         ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]
                
                html_cal = '<div style="display:flex; gap:10px; overflow-x:auto;">'
                for m, a in meses:
                    nombre_m = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][m-1]
                    html_cal += f'<div style="min-width:180px;"><b style="font-size:14px;">{nombre_m} {a}</b><div style="display:grid; grid-template-columns:repeat(7,1fr); gap:2px; font-size:10px;">'
                    for d in ["L","M","X","J","V","S","D"]: html_cal += f'<div>{d}</div>'
                    for sem in calendar.monthcalendar(a, m):
                        for dia in sem:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                color = "color:#555;" if date(a, m, dia) in ocupadas else "color:white;"
                                raya = '<div style="width:100%; height:2px; background:#ff385c;"></div>' if date(a, m, dia) in ocupadas else ""
                                html_cal += f'<div style="text-align:center; position:relative; {color}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)
                st.divider()

                # Formulario
                c1, c2 = st.columns(2)
                d_i = c1.date_input("Inicio", key=f"start_{v['nombre']}")
                d_f = c2.date_input("Fin", key=f"end_{v['nombre']}")
                
                dt_i = datetime.combine(d_i, time(10, 0))
                dt_f = datetime.combine(d_f, time(12, 0))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    nombre = st.text_input("Nombre Completo", key=f"n_{v['nombre']}")
                    cedula = st.text_input("Documento (CI/RG/CPF)", key=f"c_{v['nombre']}")
                    celular = st.text_input("WhatsApp", key=f"w_{v['nombre']}")
                    
                    dias = max(1, (d_f - d_i).days)
                    total_r = dias * v['precio']
                    
                    if nombre and cedula and celular:
                        # Contrato Digital Profesional
                        texto_contrato = f"""CONTRATO DE LOCACIÓN - J&M ASOCIADOS
--------------------------------------------------
ARRENDATARIO: {nombre} | DOC: {cedula}
VEHÍCULO: {v['nombre']}
PERIODO: {d_i} al {d_f}
TOTAL: R$ {total_r} (Gs. {total_r*COTIZACION_DIA:,.0f})

CLÁUSULAS:
1. El cliente es responsable civil y penal del vehículo.
2. Límite: 200km/día. Excedente Gs. 100.000 x 10km.
3. Garantía de Gs. 5.000.000 por siniestro o daño.
--------------------------------------------------
ACEPTACIÓN DIGITAL: Yo, {nombre}, acepto los términos.
ID: JM-{cedula[-3:]}"""
                        st.text_area("Lea el contrato:", texto_contrato, height=150, disabled=True)
                        
                        st.info(f"PAGO PIX: R$ {total_r} (Llave: 24510861818)")
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"img_{v['nombre']}")
                        
                        if st.button("RESERVAR AHORA", key=f"btn_{v['nombre']}"):
                            img_data = foto.read() if foto else None
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute('INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)',
                                         (nombre, cedula, celular, v['nombre'], dt_i, dt_f, total_r, img_data))
                            conn.commit(); conn.close()
                            
                            # WhatsApp Link
                            wa_msg = urllib.parse.quote(f"Hola JM! Soy {nombre}, reservé el {v['nombre']}. Acepto contrato. Total: R$ {total_r}")
                            wa_url = f"https://wa.me/595991681191?text={wa_msg}"
                            st.markdown(f'<a href="{wa_url}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">✅ ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                            st.success("¡Reserva Confirmada!"); st.balloons()
                else:
                    st.error("⚠️ Vehículo no disponible o en taller para estas fechas.")

# --- TAB 2: UBICACIÓN ---
with t_ubi:
    st.markdown("<h3 style='text-align:center;'>Ciudad del Este, Paraguay</h3>", unsafe_allow_html=True)
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.447551408846!2d-54.6111!3d-25.51!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzM2LjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1625680000000!5m2!1ses!2spy" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

# --- TAB 3: ADMINISTRADOR ---
with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL")
        
        # Métricas
        c_m1, c_m2, c_m3 = st.columns(3)
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        c_m1.metric("INGRESOS", f"R$ {ing:,.2f}", f"Gs. {ing*COTIZACION_DIA:,.0f}")
        c_m2.metric("EGRESOS", f"R$ {egr:,.2f}", f"Gs. {egr*COTIZACION_DIA:,.0f}")
        c_m3.metric("UTILIDAD", f"R$ {ing-egr:,.2f}")

        # Gráfico
        if not res_df.empty:
            res_df['fecha_f'] = pd.to_datetime(res_df['inicio']).dt.date
            fig = px.bar(res_df.groupby('fecha_f')['total'].sum().reset_index(), x='fecha_f', y='total', title="Ventas por Día (R$)", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)

        # Gestión de Flota
        st.subheader("🚗 GESTIÓN DE FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2,1,1])
            ca1.write(f"**{f['nombre']}**")
            nv_p = ca2.number_input("Precio R$", value=float(f['precio']), key=f"p_{f['nombre']}")
            if nv_p != f['precio']:
                conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (nv_p, f['nombre']))
                conn.commit(); st.rerun()
            if ca3.button("EN TALLER / DISPONIBLE", key=f"st_{f['nombre']}"):
                nv_e = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nv_e, f['nombre']))
                conn.commit(); st.rerun()

        # Gastos
        st.subheader("💸 REGISTRAR GASTO")
        with st.form("g_form"):
            con_g = st.text_input("Concepto")
            mon_g = st.number_input("Monto R$")
            if st.form_submit_button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con_g, mon_g, date.today()))
                conn.commit(); st.rerun()

        # Visualizar Reservas
        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                st.write(f"**Auto:** {r['auto']} | **WhatsApp:** {r['celular']}")
                st.write(f"**Periodo:** {r['inicio']} a {r['fin']}")
                if r['comprobante']: st.image(r['comprobante'], caption="Comprobante de Pago", width=300)
                if st.button("Eliminar Reserva", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
