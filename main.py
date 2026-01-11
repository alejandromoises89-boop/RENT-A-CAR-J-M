import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, date, timedelta, time
import uuid
import json
import calendar
import urllib.parse

# --- CONFIGURACIÓN Y ESTILO LUXURY ---
st.set_page_config(page_title="JM Alquiler | Premium", layout="wide")

COLORS = {
    "bordo": "#4A0404",
    "gold": "#C5A059",
    "ivory": "#F9F7F2",
    "dark": "#121212"
}

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Inter:wght@300;400;600&display=swap');
    .stApp {{ background-color: {COLORS['ivory']}; font-family: 'Inter', sans-serif; }}
    
    /* Contenedor Vertical del Auto */
    .car-vertical-card {{
        background: white;
        border-radius: 25px;
        padding: 0px;
        margin-bottom: 50px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.05);
        border: 1px solid #EEE;
        text-align: center;
    }}
    
    .price-badge {{
        background: {COLORS['dark']};
        color: {COLORS['gold']};
        padding: 10px 20px;
        border-radius: 50px;
        display: inline-block;
        font-weight: bold;
        margin: 15px 0;
    }}

    /* CALENDARIO HORIZONTAL AIRBNB */
    .scroll-container {{
        display: flex;
        overflow-x: auto;
        gap: 20px;
        padding: 20px;
        background: white;
        border-radius: 15px;
        margin: 20px 0;
        scrollbar-width: thin;
    }}
    .month-card {{
        min-width: 280px;
        background: #fff;
        border: 1px solid #eee;
        padding: 15px;
        border-radius: 12px;
    }}
    .cal-grid {{ 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 5px; 
        text-align: center; 
        font-size: 0.85rem;
    }}
    .day-cell {{ 
        padding: 8px 0; 
        position: relative; 
        color: #333;
    }}
    .day-booked {{ 
        color: #D3D3D3; 
    }}
    .strike-line {{
        position: absolute;
        width: 100%;
        height: 1.5px;
        background: #FF385C;
        top: 50%;
        left: 0;
        transform: rotate(-15deg);
    }}
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE BASE DE DATOS (Simplificada para el ejemplo) ---
def get_fechas_bloqueadas(auto_nombre):
    # Aquí conectarías con tu DB. Simulación de fechas:
    return [date.today() + timedelta(days=i) for i in range(3, 7)]

# --- RENDERIZADO DE CALENDARIO HORIZONTAL ---
def render_horizontal_calendar(auto_nombre):
    bloqueadas = get_fechas_bloqueadas(auto_nombre)
    today = date.today()
    
    html_calendar = '<div class="scroll-container">'
    
    # Generar próximos 4 meses
    for m_offset in range(4):
        target_date = today + timedelta(days=30 * m_offset)
        year, month = target_date.year, target_date.month
        month_name = calendar.month_name[month].upper()
        
        html_calendar += f'<div class="month-card"><b>{month_name} {year}</b><hr><div class="cal-grid">'
        for d in ["L","M","M","J","V","S","D"]: 
            html_calendar += f'<div style="color:#717171; font-size:10px;">{d}</div>'
            
        for week in calendar.monthcalendar(year, month):
            for day in week:
                if day == 0:
                    html_calendar += '<div></div>'
                else:
                    curr_date = date(year, month, day)
                    is_booked = curr_date in bloqueadas
                    class_name = "day-cell day-booked" if is_booked else "day-cell"
                    strike = '<div class="strike-line"></div>' if is_booked else ""
                    html_calendar += f'<div class="{class_name}">{day}{strike}</div>'
        html_calendar += '</div></div>'
    
    html_calendar += '</div>'
    st.markdown(html_calendar, unsafe_allow_html=True)

# --- CUERPO DE LA APP ---
st.markdown(f'<h1 style="text-align:center; font-family:Cinzel; color:{COLORS["bordo"]};">JM LUXURY SELECTION</h1>', unsafe_allow_html=True)

# Lista de Autos (Simulada para este diseño)
autos = [
    {"nombre": "Hyundai Tucson 2012", "precio": 260, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "placa": "AAVI502"},
    {"nombre": "Toyota Vitz RS", "precio": 195, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "placa": "AAOR725"}
]

for car in autos:
    with st.container():
        # --- BLOQUE VERTICAL DEL AUTO ---
        st.markdown(f"""
            <div class="car-vertical-card">
                <div style="background:{COLORS['dark']}; padding:10px; border-radius:25px 25px 0 0;">
                    <h2 style="color:white; margin:0;">{car['nombre']}</h2>
                </div>
                <img src="{car['img']}" style="width:60%; margin:20px 0;">
                <div class="price-badge">R$ {car['precio']} / DÍA</div>
                <p style="color:gray;">Placa: {car['placa']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # --- FICHA TÉCNICA DESPLEGABLE ---
        with st.expander("💎 VER DETALLES Y FICHA TÉCNICA"):
            c1, c2, c3 = st.columns(3)
            c1.markdown("⚙️ **Transmisión**\n\nAutomática")
            c2.markdown("⛽ **Combustible**\n\nDiesel Premium")
            c3.markdown("👥 **Capacidad**\n\n5 Pasajeros")
            st.divider()
            st.markdown("❄️ Aire Acondicionado bi-zona | 🧳 Maletero amplio | 💿 Bluetooth Audio")

        # --- CALENDARIO HORIZONTAL (Airbnb Style) ---
        st.write("📅 **Disponibilidad del Vehículo**")
        render_horizontal_calendar(car['nombre'])
        
        # --- BOTÓN DE ACCIÓN ---
        if st.button(f"RESERVAR {car['nombre']}", key=f"btn_{car['nombre']}", use_container_width=True):
            st.session_state.selected_car = car
            st.session_state.step = 1
            st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)

# --- LÓGICA DE RESERVA POR PASOS (Simplificada) ---
if 'step' in st.session_state:
    st.divider()
    st.header(f"Confirmando Reserva: {st.session_state.selected_car['nombre']}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🕒 FECHAS", "👤 CLIENTE", "📜 CONTRATO", "💳 PAGO", "✅ FINALIZAR"])
    
    with tab1:
        st.subheader("Paso 1: Definir Periodo")
        col_a, col_b = st.columns(2)
        ini = col_a.date_input("Recogida", min_value=date.today())
        fin = col_b.date_input("Devolución", value=ini + timedelta(days=1))
        st.info("Horario fijo de entrega: 08:00 a 17:00 hs (Lunes a Viernes)")

    with tab2:
        st.subheader("Paso 2: Información Personal")
        st.text_input("Nombre Completo")
        st.text_input("CI / Documento")
        st.text_input("WhatsApp")

    with tab3:
        st.subheader("Paso 3: Contrato Legal")
        st.text_area("Términos del Servicio", "1. El vehículo debe...\n2. El seguro cubre...\n[...]", height=200)
        st.checkbox("Acepto las 12 cláusulas del contrato.")
        st.write("Firma Digital:")
        st_canvas(stroke_width=2, stroke_color="#000", background_color="#FFF", height=100, key="signature")

    with tab4:
        st.subheader("Paso 4: Detalles de Pago")
        st.markdown("""
        **Transferencia Paraguay (Ueno Bank)**: Marina Baez - Alias: 1008110  
        **PIX Brasil (Santander)**: 24510861818
        """)
        st.file_uploader("Subir Comprobante")

    with tab5:
        if st.button("CONFIRMAR RESERVA FINAL"):
            st.balloons()
            st.success("Reserva enviada con éxito.")
            # Link WhatsApp
            st.markdown("[ENVIAR WHATSAPP CORPORATIVO](https://wa.me/595991681191)")