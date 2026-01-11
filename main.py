import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, date, timedelta, time
import uuid
import json
import requests
import calendar
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM Alquiler | Executive Car Rental",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PALETA DE COLORES LUXURY ---
COLORS = {
    "bordo": "#4A0404",  # Deep Burgundy
    "gold": "#C5A059",   # Metallic Gold
    "ivory": "#F9F7F2",  # Cream White
    "dark": "#121212",   # Rich Black
    "gray": "#F0F0F0"
}

# --- ESTILOS CSS AVANZADOS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500&family=Inter:wght@300;400;600&display=swap');
    
    .stApp {{ background-color: {COLORS['ivory']}; font-family: 'Inter', sans-serif; }}
    
    /* Headers */
    .main-title {{
        font-family: 'Cinzel', serif;
        color: {COLORS['bordo']};
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 2px;
    }}
    
    /* Ficha de Auto Estilo Vertical */
    .car-card {{
        background: white;
        border-radius: 20px;
        padding: 0px;
        margin-bottom: 40px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid #EEE;
    }}
    
    .car-header {{
        background: {COLORS['dark']};
        color: white;
        padding: 20px;
        text-align: center;
    }}

    /* Airbnb Calendar */
    .cal-container {{
        background: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #DDD;
    }}
    .cal-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }}
    .cal-day {{ padding: 10px; font-size: 13px; color: #333; position: relative; }}
    .cal-booked {{ color: #CCC; }}
    .strike-red {{
        position: absolute; top: 50%; left: 0; width: 100%; height: 2px;
        background: #D32F2F; transform: rotate(-15deg);
    }}
    
    /* Stepper */
    .step-box {{
        background: white;
        padding: 30px;
        border-radius: 20px;
        border-top: 5px solid {COLORS['gold']};
    }}
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS Y LÓGICA ---
def init_db():
    conn = sqlite3.connect('jm_premium_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id TEXT PRIMARY KEY, cliente TEXT, doc TEXT, wa TEXT, auto TEXT, 
                  inicio TIMESTAMP, fin TIMESTAMP, total_rs REAL, total_gs REAL, status TEXT, contrato TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id TEXT PRIMARY KEY, concepto TEXT, monto_gs REAL, monto_rs REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio_rs REAL, img TEXT, estado TEXT, placa TEXT, specs TEXT)')
    
    autos = [
        ("Hyundai Tucson 2012", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", '{"trans": "Automática", "fuel": "Diesel", "pax": 5, "maletas": 3, "aire": "Dual Zone"}'),
        ("Toyota Vitz 2012", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", '{"trans": "Automática", "fuel": "Nafta", "pax": 5, "maletas": 2, "aire": "Manual"}')
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

def get_ocupadas(auto):
    conn = sqlite3.connect('jm_premium_v4.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    dias = set()
    for _, r in df.iterrows():
        s, e = pd.to_datetime(r['inicio']).date(), pd.to_datetime(r['fin']).date()
        for i in range((e - s).days + 1): dias.add(s + timedelta(days=i))
    return dias

# --- COMPONENTE CALENDARIO ---
def draw_calendar(auto_name):
    ocupadas = get_ocupadas(auto_name)
    today = date.today()
    
    cols = st.columns(2)
    for i, col in enumerate(cols):
        current_date = today + timedelta(days=i*30)
        m, y = current_date.month, current_date.year
        with col:
            st.write(f"**{calendar.month_name[m]} {y}**")
            st.markdown('<div class="cal-grid">', unsafe_allow_html=True)
            for d in ["L","M","M","J","V","S","D"]: st.markdown(f"<b>{d}</b>", unsafe_allow_html=True)
            for week in calendar.monthcalendar(y, m):
                for day in week:
                    if day == 0: st.write("")
                    else:
                        curr = date(y, m, day)
                        is_booked = curr in ocupadas
                        style = "cal-booked" if is_booked else ""
                        strike = '<div class="strike-red"></div>' if is_booked else ""
                        st.markdown(f'<div class="cal-day {style}">{day}{strike}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- INTERFAZ ---
init_db()
if 'view' not in st.session_state: st.session_state.view = 'HOME'
if 'cot' not in st.session_state: st.session_state.cot = 1480.0

st.markdown('<h1 class="main-title">JM LUXURY RENT</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#C5A059; letter-spacing:5px;">PREMIUM CAR RENTAL SERVICE</p>', unsafe_allow_html=True)

# --- NAVEGACIÓN ---
menu = st.tabs(["💎 FLOTA EXCLUSIVA", "📍 SEDE", "🔐 CORPORATIVO"])

# --- VISTA HOME ---
with menu[0]:
    conn = sqlite3.connect('jm_premium_v4.db')
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()

    for _, car in flota.iterrows():
        st.markdown(f'<div class="car-header"><h3>{car["nombre"]}</h3></div>', unsafe_allow_html=True)
        col_img, col_det = st.columns([1.5, 1])
        
        with col_img:
            st.image(car['img'], use_container_width=True)
        
        with col_det:
            st.markdown(f"### R$ {car['precio_rs']:.0f} / día")
            st.info(f"Aprox Gs. {car['precio_rs']*st.session_state.cot:,.0f}")
            
            with st.expander("🔍 VER FICHA TÉCNICA"):
                specs = json.loads(car['specs'])
                st.write(f"🪪 **Placa:** {car['placa']}")
                st.write(f"⚙️ **Transmisión:** {specs['trans']}")
                st.write(f"⛽ **Combustible:** {specs['fuel']}")
                st.write(f"👥 **Pasajeros:** {specs['pax']}")
                st.write(f"❄️ **Climatización:** {specs['aire']}")
            
            if st.button(f"RESERVAR {car['nombre']}", use_container_width=True):
                st.session_state.booking_car = car
                st.session_state.view = 'RESERVA'
                st.rerun()
        
        st.markdown("#### Disponibilidad")
        draw_calendar(car['nombre'])
        st.divider()

# --- WIZARD DE RESERVA ---
if st.session_state.view == 'RESERVA':
    car = st.session_state.booking_car
    st.markdown(f"## Proceso de Reserva: {car['nombre']}")
    
    step = st.radio("Pasos", ["1. Fecha y Hora", "2. Datos del Cliente", "3. Contrato", "4. Pago"], horizontal=True)
    
    if step == "1. Fecha y Hora":
        st.markdown('<div class="step-box">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Fecha Inicio", min_value=date.today())
        d_fin = c2.date_input("Fecha Fin", value=d_ini + timedelta(days=1))
        
        st.warning("🕒 Horario de oficina: Lunes a Viernes 08:00 a 17:00. Fines de semana según disponibilidad.")
        t_ini = c1.time_input("Hora Entrega", time(9, 0))
        t_fin = c2.time_input("Hora Devolución", time(16, 0))
        
        # Bloqueo lógico de horarios
        if d_ini.weekday() < 5: # LV
            if not (time(8,0) <= t_ini <= time(17,0)): st.error("Seleccione horario entre 08:00 y 17:00")
        
        dias = (d_fin - d_ini).days
        st.session_state.temp_total_rs = dias * car['precio_rs']
        st.write(f"**Total Estancia:** {dias} días")
        st.markdown('</div>', unsafe_allow_html=True)

    elif step == "2. Datos del Cliente":
        st.markdown('<div class="step-box">', unsafe_allow_html=True)
        st.text_input("Nombre Completo y Apellido")
        st.text_input("Documento de Identidad (CI / RG / Pasaporte)")
        st.text_input("Nacionalidad")
        st.text_input("WhatsApp de Contacto (con código de país)")
        st.text_input("Dirección de Residencia")
        st.markdown('</div>', unsafe_allow_html=True)

    elif step == "3. Contrato":
        st.markdown('<div class="step-box">', unsafe_allow_html=True)
        with st.container(height=300):
            st.markdown("""
            **CONTRATO DE ALQUILER JM LUXURY**
            1. El arrendatario se compromete a devolver el vehículo en las mismas condiciones...
            2. Queda prohibido el uso del vehículo para fines ilícitos...
            3. El seguro cubre daños a terceros según póliza vigente...
            4. El vehículo debe ser entregado con el mismo nivel de combustible...
            5. En caso de accidente, avisar inmediatamente a JM Alquiler...
            ... (Cláusulas 6 a 12) ...
            """)
        st.checkbox("He leído y acepto los términos del contrato de arrendamiento.")
        st.write("Firma Digital:")
        st_canvas(stroke_width=2, stroke_color="#000", background_color="#FFF", height=150, key="sig_reserva")
        st.markdown('</div>', unsafe_allow_html=True)

    elif step == "4. Pago":
        st.markdown('<div class="step-box">', unsafe_allow_html=True)
        total_gs = st.session_state.temp_total_rs * st.session_state.cot
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### Transferencia Paraguay (Gs)")
            st.write("Banco Ueno - Marina Baez")
            st.write("Alias: 1008110")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=UENO-MARINA-BAEZ-1008110")
        
        with c2:
            st.markdown("### PIX Brasil (Reales)")
            st.write("Banco Santander - Marina Baez")
            st.write("Chave: 24510861818")
            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX-SANTANDER-24510861818")
        
        st.divider()
        st.markdown("💳 **Pago con Tarjeta (Seguro)**")
        st.text_input("Número de Tarjeta")
        st.caption("🔒 JM Luxury no almacena los datos de su tarjeta. Transacción cifrada por SSL.")
        
        if st.button("CONFIRMAR Y ENVIAR COMPROBANTE"):
            st.success("¡Reserva Procesada!")
            # Botón interactivo de WhatsApp
            wa_text = f"Reserva JM Luxury: {car['nombre']} - Total: R$ {st.session_state.temp_total_rs}"
            st.markdown(f"""
                <a href="https://wa.me/595991681191?text={urllib.parse.quote(wa_text)}" target="_blank">
                    <button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%;">
                        ENVIAR WHATSAPP CORPORATIVO 💬
                    </button>
                </a>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- VISTA ADMIN ---
with menu[2]:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        st.title("Panel de Control Corporativo")
        
        # Dashboard Estadístico
        conn = sqlite3.connect('jm_premium_v4.db')
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        eg_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Ingresos Totales (Rs)", f"{res_df['total_rs'].sum():,.2f}")
        col2.metric("Egresos (Gs)", f"{eg_df['monto_gs'].sum():,.0f}")
        
        # Gráfico
        fig = px.bar(res_df, x='auto', y='total_rs', color='auto', title="Ventas por Vehículo", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        # Gestión de Gastos
        with st.expander("➕ Cargar Gasto/Egreso"):
            conc = st.text_input("Concepto")
            m_gs = st.number_input("Monto Gs", min_value=0)
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (id, concepto, monto_gs, fecha) VALUES (?,?,?,?)", 
                             (str(uuid.uuid4())[:5], conc, m_gs, date.today()))
                conn.commit()
                st.success("Gasto registrado")

        # Estado de Flota
        st.subheader("Estado de Flota")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        st.data_editor(flota_adm, key="flota_edit")
        if st.button("Actualizar Estados"):
            # Lógica para guardar cambios del data_editor
            pass
            
        conn.close()