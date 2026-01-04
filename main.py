import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

import streamlit as st
import pandas as pd

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="J&M ASOCIADOS - Login", layout="centered")

# --- 2. LÓGICA DE SESIÓN (EL BLINDAJE) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 3. ESTILO CSS "ESTUDIO PRESTIGE" ---
st.markdown("""
<style>
    /* Fondo Degradado Bordó a Negro */
    .stApp {
        background: radial-gradient(circle, #600000 0%, #1a0000 100%);
    }

    /* Contenedor del Login */
    .login-box {
        text-align: center;
        padding: 40px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 20px;
    }

    /* Logo J&M Estilo Serigrafía Cursiva */
    .logo-jm {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 70px;
        color: #D4AF37;
        text-shadow: 0px 0px 15px rgba(212, 175, 55, 0.6);
        margin-bottom: 0px;
    }

    .slogan {
        color: #D4AF37;
        font-family: 'Garamond', serif;
        letter-spacing: 4px;
        font-size: 14px;
        margin-top: -10px;
        text-transform: uppercase;
    }

    /* Candado Dorado */
    .lock-icon {
        font-size: 40px;
        color: #D4AF37;
        margin: 20px 0;
    }

    /* Inputs Traslúcidos con Borde Dorado Fino */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #D4AF37 !important;
        color: #D4AF37 !important;
        border-radius: 5px !important;
        text-align: center;
    }

    /* Botón ENTRAR Bordó Intenso */
    .stButton>button {
        background-color: #400000 !important;
        color: #D4AF37 !important;
        border: 2px solid #D4AF37 !important;
        font-weight: bold !important;
        font-size: 18px !important;
        width: 100%;
        height: 50px;
        border-radius: 5px !important;
        margin-top: 20px;
    }
    
    .stButton>button:hover {
        background-color: #600000 !important;
        box-shadow: 0px 0px 15px rgba(212, 175, 55, 0.4);
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# --- 4. CUERPO DEL LOGIN ---
def pantalla_login():
    with st.container():
        # Encabezado
        st.markdown('<h1 class="logo-jm">J&M</h1>', unsafe_allow_html=True)
        st.markdown('<p class="slogan">Asociados - Alquiler de Vehículos</p>', unsafe_allow_html=True)
        
        # Imagen de autos (opcional, si tienes una URL de imagen real puedes ponerla aquí)
        # st.image("URL_DE_TU_IMAGEN_AUTOS", use_column_width=True)
        
        # Icono de Seguridad
        st.markdown('<div class="lock-icon">🔒</div>', unsafe_allow_html=True)

        # Formulario Blindado
        with st.form("login_form"):
            usuario = st.text_input("USUARIO / TELÉFONO", placeholder="Ej: 0991681191")
            clave = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            
            submit = st.form_submit_button("ENTRAR")
            
            if submit:
                # AQUÍ defines tu usuario y clave maestros
                if usuario == "admin" and clave == "2026":
                    st.session_state.autenticado = True
                    st.success("Acceso concedido. Cargando sistema...")
                    st.rerun()
                elif usuario == "" or clave == "":
                    st.warning("Por favor, complete todos los campos.")
                else:
                    st.error("Credenciales incorrectas. Intente de nuevo.")

# --- 5. CONTROL DE FLUJO ---
if not st.session_state.autenticado:
    pantalla_login()
else:
    # Una vez que entra, aquí va el resto de tu App
    st.markdown('<h2 style="color:#D4AF37;">Bienvenido al Panel de Control J&M</h2>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 3. BASE DE DATOS Y ESTADO ---
if 'db_reservas' not in st.session_state:
    st.session_state.db_reservas = pd.DataFrame(columns=[
        "ID", "Fecha", "Cliente", "Auto", "Ingreso", "Egreso", "Estado"
    ])

VEHICULOS = {
    "Toyota Vitz 2012": {
        "precio": 220, "color": "Negro", "trans": "Automático", "motor": "1.3L",
        "img": "https://a0.anyrgb.com/pngimg/1498/1242/toyota-vitz.png"
    },
    "Hyundai Tucson 2012": {
        "precio": 260, "color": "Blanco", "trans": "Automático", "motor": "2.0L",
        "img": "https://www.iihs.org/api/ratings/model-year-images/2098/"
    },
    "Toyota Voxy 2011": {
        "precio": 240, "color": "Gris", "trans": "Secuencial", "motor": "2.0L",
        "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"
    }
}

# --- 4. ESTRUCTURA DE PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["🏠 ALQUILAR", "📋 MI HISTORIAL", "⚙️ ADMIN J&M"])

with tab1:
    st.subheader("Seleccione su Vehículo")
    cols = st.columns(3)
    
    for i, (nombre, info) in enumerate(VEHICULOS.items()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="car-card">
                <img src="{info['img']}" style="width:100%; height:120px; object-fit:contain;">
                <h4 style="color:#4A0404; margin-bottom:5px;">{nombre}</h4>
                <div class="spec-text">
                    <b>🎨 Color:</b> {info['color']}<br>
                    <b>⚙️ Motor:</b> {info['motor']}<br>
                    <b>🕹️ Transmisión:</b> {info['trans']}
                </div>
                <hr>
                <p class="price-tag">R$ {info['precio']} <small>/ día</small></p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Reservar {nombre}", key=f"res_{i}"):
                st.session_state.seleccionado = nombre

    if 'seleccionado' in st.session_state:
        st.divider()
        with st.form("registro_alquiler"):
            st.markdown(f"### Completar Reserva: **{st.session_state.seleccionado}**")
            c1, c2 = st.columns(2)
            nombre_cli = c1.text_input("Nombre Completo")
            dias = c2.number_input("Días de Alquiler", min_value=1, value=1)
            
            if st.form_submit_button("Confirmar y Pago PIX"):
                total = dias * VEHICULOS[st.session_state.seleccionado]['precio']
                egreso_estimado = total * 0.20 # 20% para mantenimiento
                nueva_reserva = {
                    "ID": len(st.session_state.db_reservas) + 1,
                    "Fecha": datetime.date.today(),
                    "Cliente": nombre_cli,
                    "Auto": st.session_state.seleccionado,
                    "Ingreso": total,
                    "Egreso": egreso_estimado,
                    "Estado": "Pagado"
                }
                st.session_state.db_reservas = pd.concat([st.session_state.db_reservas, pd.DataFrame([nueva_reserva])], ignore_index=True)
                st.success(f"✅ ¡Reserva Exitosa para {nombre_cli}!")

with tab2:
    st.subheader("Historial de Alquileres")
    st.dataframe(st.session_state.db_reservas, use_container_width=True)

with tab3:
    st.header("📊 Auditoría y Finanzas")
    df = st.session_state.db_reservas
    
    if not df.empty:
        c1, c2 = st.columns(2)
        
        # Gráfico de Torta (Ganancias vs Pérdidas/Gastos)
        with c1:
            total_ing = df['Ingreso'].sum()
            total_egr = df['Egreso'].sum()
            fig_pie = px.pie(
                values=[total_ing, total_egr], 
                names=['Ganancia Neta', 'Gastos Mantenimiento'],
                color_discrete_sequence=['#28A745', '#DC3545'],
                hole=0.4, title="Distribución Financiera (BRL)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Gráfico de Barras por Auto
        with c2:
            fig_bar = px.bar(df, x='Auto', y='Ingreso', color='Auto', title="Ingresos por Vehículo")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Botón de Exportación para Auditoría
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte para Auditoría (CSV)",
            data=csv,
            file_name=f"Auditoria_JM_{datetime.date.today()}.csv",
            mime='text/csv',
        )
    else:
        st.info("No hay datos financieros para reportar.")
