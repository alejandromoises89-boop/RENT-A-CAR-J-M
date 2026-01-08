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

# Intentar aplicar los estilos premium
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

# --- ESTILOS CSS ---
st.markdown(f"""
    <style>
    .cal-header {{ font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0 5px 0; color: #333; text-transform: capitalize; }}
    .cal-grid-fijo {{ 
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 0px; 
        max-width: 320px; margin: 0 auto; border: 0.2px solid #eee;
    }}
    .cal-box-fijo {{ 
        aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; 
        font-size: 12px; position: relative; background: white; color: #222; border: 0.1px solid #f7f7f7;
    }}
    .cal-day-name-fijo {{ text-align: center; font-size: 10px; color: #717171; font-weight: bold; padding-bottom: 5px; }}
    .ocupado {{ color: #ccc !important; background-color: #fafafa; }}
    .raya-roja-h {{ position: absolute; width: 80%; height: 1.5px; background-color: #ff385c; z-index: 1; top: 50%; }}
    .card-auto {{ border: 1px solid #ddd; padding: 15px; border-radius: 15px; background: white; text-align: center; }}
    .pix-box {{ background-color: #f8f9fa; border: 2px dashed #D4AF37; padding: 15px; border-radius: 10px; margin-top: 10px; color: #333; }}
    .btn-whatsapp {{
        background-color: #25D366; color: white !important; padding: 12px 20px; 
        border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 10px;
    }}
    .contrato-container {{
        background-color: #1a1a1a; color: #f1f1f1; padding: 20px; border-radius: 10px; 
        font-size: 12px; border: 1px solid #D4AF37; height: 350px; overflow-y: scroll; 
        line-height: 1.6; text-align: justify;
    }}
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    conn.commit(); conn.close()

init_db()

# --- FUNCIONES ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close(); bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,)); res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    ok = c.fetchone()[0] == 0; conn.close(); return ok

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        p_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:18px; color:#D4AF37;">R$ {v["precio"]} / Gs. {p_gs:,.0f}</p></div>''', unsafe_allow_html=True)
            with st.expander("Ver Disponibilidad"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                c_iz, c_de = st.columns(2)
                for idx, (m, a) in enumerate([(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]):
                    with [c_iz, c_de][idx]:
                        st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                        d_h = "".join([f'<div class="cal-day-name-fijo">{d}</div>' for d in ["L","M","M","J","V","S","D"]])
                        
                        # Corrección del error de sintaxis en el loop del calendario
                        d_b = ""
                        for sem in calendar.monthcalendar(a, m):
                            for d in sem:
                                if d == 0:
                                    d_b += '<div class="cal-box-fijo" style="background:transparent; border:none;"></div>'
                                else:
                                    f_act = date(a, m, d)
                                    es_o = f_act in ocupadas
                                    clase = "cal-box-fijo ocupado" if es_o else "cal-box-fijo"
                                    raya = '<div class="raya-roja-h"></div>' if es_o else ""
                                    d_b += f'<div class="{clase}">{d}{raya}</div>'
                        
                        st.markdown(f'<div class="cal-grid-fijo">{d_h}{d_b}</div>', unsafe_allow_html=True)
                
                st.divider()
                c1, c2 = st.columns(2)
                fi = c1.date_input("Inicio", key=f"fi{v['nombre']}")
                ff = c2.date_input("Fin", key=f"ff{v['nombre']}")
                
                if esta_disponible(v['nombre'], datetime.combine(fi, time(9,0)), datetime.combine(ff, time(10,0))):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("CI / Documento", key=f"ci{v['nombre']}")
                    c_wa = st.text_input("WhatsApp", key=f"wa{v['nombre']}")
                    dias = max(1, (ff - fi).days); total_r = dias * v['precio']
                    
                    if c_n and c_ci and c_wa:
                        st.markdown(f"""
                        <div class="contrato-container">
                            <center><b>CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR</b></center><br>
                            Entre:<br>
                            <b>ARRENDADOR:</b> J&M ASOCIADOS. RUC: 1.702.076-0. Domicilio: Curupaytu esq. Farid Rahal. Tel: +595983635573.<br><br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}. CI/RG: {c_ci}.<br><br>
                            <b>PRIMERA - Objeto:</b> El arrendador otorga en alquiler el vehículo {v['nombre']}. El arrendatario confirma recepción en buen estado.<br><br>
                            <b>SEGUNDA - Duración:</b> Desde {fi} hasta {ff}.<br><br>
                            <b>TERCERA - Precio:</b> R$ {v['precio']} diarios. Total: R$ {total_r}.<br><br>
                            <b>CUARTA - Siniestros:</b> El arrendatario pagará Gs. 5.000.000 en caso de accidente para cubrir daños.<br><br>
                            <b>QUINTA - Uso:</b> Fines personales. El arrendatario es responsable PENAL y CIVIL de lo ocurrido en el vehículo.<br><br>
                            <b>SEXTA - Kilometraje:</b> Límite de 200km/día. Exceso: Gs. 100.000 adicional.<br><br>
                            <b>SÉPTIMA - Seguro:</b> Cubre Responsabilidad Civil y rastreo satelital. Negligencia es cargo del arrendatario.<br><br>
                            <b>OCTAVA - Mantenimiento:</b> Arrendatario cuida agua, combustible y limpieza.<br><br>
                            <b>NOVENA - Devolución:</b> En mismas condiciones. Retraso genera penalización diaria.<br><br>
                            <b>DÉCIMA - Incumplimiento:</b> Rescisión inmediata y reclamo de daños.<br><br>
                            <b>UNDÉCIMA - Jurisdicción:</b> Tribunales del Alto Paraná, Paraguay.<br><br>
                            <b>DÉCIMA SEGUNDA - Firma:</b> Se acepta mediante confirmación digital.<br><br>
                            <i>EL ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR.</i>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="pix-box"><b>PIX: R$ {total_r}</b><br>Llave: 24510861818</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante/Documento", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"b{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_ci, c_wa, v['nombre'], fi, ff, total_r, foto.read())); conn.commit(); conn.close()
                            msg = f"Hola JM, soy {c_n}. He leído el contrato y acepto los términos.\n🚗 Vehículo: {v['nombre']}\n🗓️ Periodo: {fi} al {ff}\n💰 Total: R$ {total_r}\nAdjunto mi comprobante de pago y documento."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-whatsapp">ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME); res_df = pd.read_sql_query("SELECT * FROM reservas", conn); egr_df = pd.read_sql_query("SELECT * FROM egresos", conn); conn.close()
        i_r = res_df['total'].sum() if not res_df.empty else 0
        e_r = egr_df['monto'].sum() if not egr_df.empty else 0
        
        st.title("📊 BALANCE GENERAL (Cotización: 1 R$ = " + str(COTIZACION_DIA) + " Gs.)")
        c1, c2, c3 = st.columns(3)
        c1.metric("INGRESOS", f"R$ {i_r:,.2f}", f"Gs. {i_r*COTIZACION_DIA:,.0f}")
        c2.metric("EGRESOS", f"R$ {e_r:,.2f}", f"Gs. {e_r*COTIZACION_DIA:,.0f}")
        c3.metric("UTILIDAD", f"R$ {i_r-e_r:,.2f}", f"Gs. {(i_r-e_r)*COTIZACION_DIA:,.0f}")
        
        if not res_df.empty:
            st.plotly_chart(px.pie(res_df, values='total', names='auto', title="Ingresos por Vehículo"))

        with st.expander("💸 CARGAR GASTO"):
            with st.form("g"):
                con = st.text_input("Concepto"); mon = st.number_input("Monto en R$")
                if st.form_submit_button("Guardar"):
                    conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, date.today())); conn.commit(); conn.close(); st.rerun()

        st.subheader("📑 REGISTRO DE CLIENTES")
        for _, r in res_df.iterrows():
            with st.expander(f"{r['cliente']} - {r['auto']}"):
                st.write(f"CI: {r['ci']} | WA: {r['celular']} | Total: R$ {r['total']} (Gs. {r['total']*COTIZACION_DIA:,.0f})")
                if r['comprobante']: st.image(r['comprobante'], width=300)