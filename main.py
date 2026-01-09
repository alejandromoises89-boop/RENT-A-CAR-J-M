import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, date
import google.generativeai as genai

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM Alquiler | Premium Fleet", layout="wide", page_icon="🚗")

# --- DISEÑO VISUAL Y CSS (LUXURY AESTHETIC) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

    :root {
        --bordo: #600010;
        --gold: #D4AF37;
        --ivory: #FDFCFB;
    }

    .main { background-color: var(--ivory); font-family: 'Inter', sans-serif; }
    
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: var(--bordo); }

    /* Botones Personalizados */
    .stButton>button {
        border-radius: 1.5rem;
        background-color: var(--bordo);
        color: white;
        border: 1px solid var(--bordo);
        padding: 0.5rem 2rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: var(--gold);
        border-color: var(--gold);
        color: white;
        transform: translateY(-2px);
    }

    /* Cards de Vehículos */
    .car-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 3px solid var(--gold);
        margin-bottom: 20px;
        text-align: center;
    }

    /* Navbar */
    .nav-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        padding: 1rem;
        background: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (STATE MANAGEMENT) ---
if 'fleet' not in st.session_state:
    st.session_state.fleet = [
        {"id": "1", "nombre": "Hyundai Tucson 2012", "precio": 260.0, "img": "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "estado": "Disponible", "placa": "AAVI502", "motor": "2.0 CRDi", "transmision": "Automática"},
        {"id": "2", "nombre": "Toyota Vitz 2012", "precio": 195.0, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "estado": "Disponible", "placa": "AAVP719", "motor": "1.3 VVT-i", "transmision": "Automática"},
        {"id": "3", "nombre": "Toyota Vitz RS 2012", "precio": 210.0, "img": "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "estado": "Disponible", "placa": "AAOR725", "motor": "1.5 RS", "transmision": "Secuencial"},
        {"id": "4", "nombre": "Toyota Voxy 2011", "precio": 240.0, "img": "https://i.ibb.co/VpSpSJ9Q/voxy.png", "estado": "Disponible", "placa": "AAUG465", "motor": "2.0 Valvematic", "transmision": "Automática"}
    ]

if 'reservations' not in st.session_state: st.session_state.reservations = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- FUNCIONES DE UTILIDAD ---
def get_exchange_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/BRL")
        return response.json()['rates']['PYG']
    except:
        return 1450.0  # Fallback

EXCHANGE_RATE = get_exchange_rate()

def format_gs(amount_brl):
    return f"{amount_brl * EXCHANGE_RATE:,.0f} Gs".replace(",", ".")

# --- NAVEGACIÓN ---
tabs = ["Unidades", "Sede Central", "Admin Dashboard"]
selected_tab = st.selectbox("Navegación", tabs, label_visibility="collapsed")

# --- MÓDULO 1: UNIDADES ---
if selected_tab == "Unidades":
    st.markdown("<h1 style='text-align: center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Seleccione excelencia, conduzca distinción.</p>", unsafe_allow_html=True)
    
    cols = st.columns(2)
    for idx, car in enumerate(st.session_state.fleet):
        with cols[idx % 2]:
            st.markdown(f"""
                <div class="car-card">
                    <img src="{car['img']}" width="100%">
                    <h3>{car['nombre']}</h3>
                    <p style="color: var(--gold); font-weight: bold; font-size: 1.2rem;">
                        R$ {car['precio']} / <span style="font-size: 0.9rem;">{format_gs(car['precio'])}</span>
                    </p>
                    <p style="font-size: 0.8rem; color: #777;">{car['motor']} • {car['transmision']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Gestionar Reserva: {car['nombre']}"):
                d_start = st.date_input("Fecha Inicio", min_value=date.today(), key=f"start_{car['id']}")
                d_end = st.date_input("Fecha Fin", min_value=d_start, key=f"end_{car['id']}")
                
                days = (d_end - d_start).days
                if days == 0: days = 1
                total_brl = days * car['precio']
                
                st.write(f"**Total estadía:** {days} días")
                st.write(f"**Total a pagar:** R$ {total_brl} ({format_gs(total_brl)})")
                
                pay_method = st.radio("Método de Pago", ["PIX / QR", "Efectivo"], key=f"pay_{car['id']}")
                if "QR" in pay_method:
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=JM-ALQUILER-PIX", caption="Escanee para pagar")
                    st.file_uploader("Subir comprobante", type=['png', 'jpg', 'pdf'], key=f"file_{car['id']}")
                
                terms = st.checkbox("Acepto el contrato digital de alquiler", key=f"terms_{car['id']}")
                
                if st.button(f"Confirmar Reserva {car['nombre']}", use_container_width=True):
                    if terms:
                        new_res = {"car": car['nombre'], "total": total_brl, "date": str(d_start)}
                        st.session_state.reservations.append(new_res)
                        
                        msg = f"Hola JM Alquiler, quiero reservar el {car['nombre']} del {d_start} al {d_end}. Total: R$ {total_brl}."
                        wa_link = f"https://wa.me/595981000000?text={msg.replace(' ', '%20')}"
                        
                        st.success("¡Reserva procesada exitosamente!")
                        st.markdown(f"[Enviar confirmación por WhatsApp]({wa_link})")
                    else:
                        st.error("Debe aceptar los términos.")

# --- MÓDULO 2: SEDE CENTRAL ---
elif selected_tab == "Sede Central":
    st.header("Sede Central")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        ### Ubicación Premium
        Estamos ubicados en el corazón comercial de **Ciudad del Este**, Paraguay.
        
        **Dirección:** Av. Monseñor Rodriguez, Edificio Luxury, Oficina 4B.
        **Horario:** Lunes a Sábados: 08:00 - 18:00.
        **Contacto:** +595 981 123 456
        """)
    with col2:
        st.image("https://images.unsplash.com/photo-1577948000111-9c970dfe3743?auto=format&fit=crop&q=80&w=800", caption="CDE Premium Center")

# --- MÓDULO 3: ADMIN DASHBOARD ---
elif selected_tab == "Admin Dashboard":
    if st.text_input("Password", type="password") == "8899":
        st.title("Admin Dashboard")
        
        # KPIs
        total_rev = sum(r['total'] for r in st.session_state.reservations)
        total_exp = sum(e['amount'] for e in st.session_state.expenses)
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Ingresos Totales", f"R$ {total_rev}")
        kpi2.metric("Gastos Totales", f"R$ {total_exp}")
        kpi3.metric("Utilidad Neta", f"R$ {total_rev - total_exp}")
        
        # Gráficos
        st.subheader("Análisis Financiero")
        c1, c2 = st.columns(2)
        
        if st.session_state.reservations:
            df_res = pd.DataFrame(st.session_state.reservations)
            fig_pie = px.pie(df_res, values='total', names='car', title="Ingresos por Vehículo", color_discrete_sequence=['#600010', '#D4AF37', '#333'])
            c1.plotly_chart(fig_pie, use_container_width=True)
            
            fig_line = px.line(df_res, x='date', y='total', title="Tendencia de Reservas", markers=True)
            fig_line.update_traces(line_color='#600010')
            c2.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay datos de reservas para mostrar gráficos.")

        # Gastos
        with st.expander("Registrar Nuevo Gasto"):
            desc = st.text_input("Descripción")
            amt = st.number_input("Monto (BRL)", min_value=0.0)
            if st.button("Guardar Gasto"):
                st.session_state.expenses.append({"desc": desc, "amount": amt})
                st.rerun()

        # IA INTEGRATION
        st.divider()
        if st.button("✨ Analizar Negocio con IA Gemini"):
            try:
                # genai.configure(api_key="TU_API_KEY") # Configurar si se tiene
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Analiza este resumen financiero de alquiler de autos: Ingresos R${total_rev}, Gastos R${total_exp}. Flota activa. Dame 3 consejos estratégicos para aumentar rentabilidad en Ciudad del Este."
                # response = model.generate_content(prompt) # Comentado para evitar error sin API Key
                st.info("Simulación IA: Basado en tus ingresos de R$ {}, se recomienda aumentar la flota del Toyota Vitz por su alta rotación en CDE.".format(total_rev))
            except Exception as e:
                st.error("Error al conectar con Gemini AI. Verifique su API Key.")
    else:
        st.warning("Por favor, ingrese la contraseña de administrador.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #999;'>© 2025 JM Alquiler - Gestión de Flota Premium</p>", unsafe_allow_html=True)