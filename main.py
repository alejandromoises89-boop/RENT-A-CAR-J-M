import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
import json

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="JM System - Luxury Rental", layout="wide")

# Colores personalizados (Bordo, Gold, Ivory)
st.markdown(f"""
    <style>
    :root {{
        --bordo: #800020;
        --gold: #D4AF37;
        --ivory: #FFFFF0;
    }}
    .main {{ background-color: var(--ivory); }}
    .stButton>button {{ background-color: var(--bordo); color: white; border-radius: 5px; }}
    .vehicle-card {{ 
        border: 1px solid var(--gold); 
        padding: 20px; 
        border-radius: 15px; 
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES Y ESTADO INICIAL ---
CORPORATE_NUMBER = "595991681191"
DEFAULT_QUOTE = 1450.0  # 1 BRL a PYG

if 'fleet' not in st.session_state:
    st.session_state.fleet = [
        {"id": 1, "model": "Hyundai Tucson 2012", "type": "Diesel, Automática", "price_brl": 250, "status": "Disponible", "img": "https://via.placeholder.com/300x200?text=Tucson"},
        {"id": 2, "model": "Toyota Vitz 2012", "type": "Nafta, Automática", "price_brl": 150, "status": "Disponible", "img": "https://via.placeholder.com/300x200?text=Vitz"},
        {"id": 3, "model": "Toyota Vitz RS 2012", "type": "Deportivo, Secuencial", "price_brl": 180, "status": "Disponible", "img": "https://via.placeholder.com/300x200?text=Vitz+RS"},
        {"id": 4, "model": "Toyota Voxy 2011", "type": "Minivan 7 pasajeros", "price_brl": 300, "status": "En Taller", "img": "https://via.placeholder.com/300x200?text=Voxy"}
    ]

if 'reservations' not in st.session_state:
    st.session_state.reservations = []

# --- LÓGICA DE NEGOCIO ---
def get_quote():
    # Simulación de servicio de moneda
    return DEFAULT_QUOTE

# --- UI: BARRA SUPERIOR ---
col_logo, col_quote = st.columns([4, 1])
with col_quote:
    st.info(f"Cotización: 1 BRL = {get_quote()} PYG")

tab1, tab2, tab3 = st.tabs(["🚗 Unidades", "📍 Sede Central", "🔐 Admin"])

# --- PESTAÑA 1: UNIDADES (CATÁLOGO) ---
with tab1:
    st.title("Nuestra Flota Premium")
    cols = st.columns(2)
    for idx, car in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="vehicle-card">
                <h3>{car['model']}</h3>
                <p><b>Motor:</b> {car['type']}</p>
                <p><b>Precio:</b> R$ {car['price_brl']} / día</p>
                <span style="color: {'green' if car['status'] == 'Disponible' else 'red'}">● {car['status']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if car['status'] == "Disponible":
                if st.button(f"Reservar {car['model']}", key=f"btn_{car['id']}"):
                    st.session_state.selecting_car = car
                    st.session_state.show_wizard = True

# --- WIZARD DE RESERVA (MODAL SIMULADO) ---
if st.session_state.get('show_wizard'):
    with st.expander("🛠️ PROCESO DE RESERVA", expanded=True):
        car = st.session_state.selecting_car
        step = st.status("Progreso de Reserva")
        
        # Paso 1: Fechas
        d_start = st.date_input("Fecha de Retiro")
        d_end = st.date_input("Fecha de Devolución")
        days = (d_end - d_start).days
        total_brl = days * car['price_brl']
        
        # Paso 2: Datos
        name = st.text_input("Nombre Completo")
        doc = st.text_input("CI / Pasaporte")
        
        # Paso 3: Pago (Simulación Tarjeta 3D)
        st.subheader("Pago")
        pay_method = st.selectbox("Método", ["PIX", "Efectivo", "Tarjeta de Crédito"])
        if pay_method == "Tarjeta de Crédito":
            st.image("https://cdn-icons-png.flaticon.com/512/633/633611.png", width=100)
            st.text_input("Número de Tarjeta")
            st.text_input("CVV", type="password")
        
        # Paso 4: Contrato y Firma
        st.info(f"Contrato: Yo {name or '___'} acepto alquilar el {car['model']} por {days} días...")
        agree = st.checkbox("Acepto términos y condiciones")
        
        # Paso 5: Éxito
        if st.button("Finalizar Reserva"):
            if agree and name:
                new_res = {"id": str(uuid.uuid4()), "client": name, "car": car['model'], "total": total_brl}
                st.session_state.reservations.append(new_res)
                st.balloons()
                st.success("¡Reserva Exitosa!")
                
                # Botón WhatsApp
                msg = f"Reserva {new_res['id']}: {name} - {car['model']} - Total: R$ {total_brl}"
                wa_url = f"https://wa.me/{CORPORATE_NUMBER}?text={msg.replace(' ', '%20')}"
                st.markdown(f"[Enviar a WhatsApp]({wa_url})")
                
                if st.button("Cerrar"):
                    st.session_state.show_wizard = False
                    st.rerun()

# --- PESTAÑA 3: PANEL ADMINISTRATIVO ---
with tab3:
    st.subheader("Acceso Administrativo")
    password = st.text_input("Contraseña", type="password")
    
    if password == "8899":
        st.success("Acceso Concedido")
        
        # KPIs
        total_rev = sum(r['total'] for r in st.session_state.reservations)
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos Totales", f"R$ {total_rev}")
        c2.metric("Gastos", "R$ 0.00")
        c3.metric("Beneficio", f"R$ {total_rev}")
        
        # Gráficos Recharts (vía Plotly en Python)
        df_res = pd.DataFrame(st.session_state.reservations)
        if not df_res.empty:
            fig = px.area(df_res, y="total", title="Tendencia de Ingresos", color_discrete_sequence=['#800020'])
            st.plotly_chart(fig, use_container_width=True)
        
        # IA: Google Gemini (Simulación de análisis)
        if st.button("Generar Reporte IA (Gemini)"):
            st.markdown("""> **Análisis de Gemini:**
            > 1. El Hyundai Tucson es tu unidad más rentable este mes.
            > 2. Sugerencia: Aplicar descuento de 10% en Toyota Vitz los fines de semana.
            > 3. Alerta: El seguro de la Voxy vence en 5 días.""")

        # Gestión de Pánico
        if st.button("BORRAR TODO (PÁNICO)"):
            st.session_state.reservations = []
            st.warning("Datos eliminados")
    elif password != "":
        st.error("Clave Incorrecta")