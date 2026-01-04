import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS - GESTIÓN", layout="wide")

# --- 2. INICIALIZACIÓN DE BASE DE DATOS (Sesión persistente) ---
if 'reservas_db' not in st.session_state:
    st.session_state.reservas_db = pd.DataFrame(columns=[
        "ID", "Cliente", "Auto", "Inicio", "Fin", "Total", "Estado"
    ])

# --- 3. ESTILOS APP PRINCIPAL (Limpio y Profesional) ---
def cargar_estilos_app():
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        .header-app { background-color: #4A0404; padding: 20px; color: #D4AF37; text-align: center; font-family: 'Times New Roman', serif; border-bottom: 5px solid #D4AF37; }
        .car-card { border: 1px solid #DDD; padding: 20px; border-radius: 10px; background: #FFF; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); text-align: center; height: 100%; }
        .stTabs [data-baseweb="tab-list"] { gap: 30px; }
        .stTabs [data-baseweb="tab"] { font-size: 18px; color: #4A0404; font-family: 'Times New Roman', serif; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCIONES DE VALIDACIÓN DE FECHAS ---
def verificar_disponibilidad(auto, inicio, fin):
    df = st.session_state.reservas_db
    # Filtrar por el mismo auto
    conflictos = df[df['Auto'] == auto]
    for _, reserva in conflictos.iterrows():
        # Lógica de solapamiento de fechas
        if not (fin < reserva['Inicio'] or inicio > reserva['Fin']):
            return False
    return True

# --- 5. EJECUCIÓN DE LA INTERFAZ ---
cargar_estilos_app()
st.markdown('<div class="header-app"><h1>JM ASOCIADOS - PANEL DE GESTIÓN</h1></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🚗 CATÁLOGO Y RESERVAS", "📜 MI HISTORIAL", "📍 UBICACIÓN Y CONTACTO", "🛡️ ADMIN FINANZAS"])

# --- TAB 1: CATÁLOGO E INTELIGENCIA DE RESERVAS ---
with tab1:
    st.subheader("Seleccione su Vehículo y Fechas")
    
    # Datos de la flota
    autos_info = {
        "Toyota Vitz 2012": {"precio": 195, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
        "Hyundai Tucson 2012": {"precio": 260, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"}
    }

    col_car1, col_car2 = st.columns(2)
    cols = [col_car1, col_car2]

    for i, (nombre, info) in enumerate(autos_info.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="car-card">
                <img src="{info['img']}" width="280">
                <h3 style="color:#4A0404;">{nombre}</h3>
                <p>✅ Carta Verde | ✅ ABS | ✅ KM Libre (PY/BR/AR)</p>
                <h4 style="color:#D4AF37;">R$ {info['precio']} / día</h4>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Agendar {nombre}"):
                c1, c2 = st.columns(2)
                f_inicio = c1.date_input("Desde", min_value=datetime.date.today(), key=f"start_{nombre}")
                f_fin = c2.date_input("Hasta", min_value=f_inicio, key=f"end_{nombre}")
                cliente_nom = st.text_input("Nombre completo del titular", key=f"nom_{nombre}")

                if st.button(f"Verificar y Pagar {nombre}", key=f"btn_{nombre}"):
                    if not cliente_nom:
                        st.error("Por favor, ingrese su nombre.")
                    elif verificar_disponibilidad(nombre, f_inicio, f_fin):
                        dias = (f_fin - f_inicio).days + 1
                        total_pago = dias * info['precio']
                        
                        st.success(f"¡Vehículo disponible por {dias} días!")
                        st.markdown(f"### Total: R$ {total_pago}")
                        
                        # Datos PIX y QR
                        st.info("🏦 Pago via PIX: Llave 24510861818 - Marina Baez (Santander)")
                        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_MARINA_BAEZ_24510861818_TOTAL_{total_pago}")
                        
                        # Guardar en Base de Datos
                        nueva_reserva = {
                            "ID": len(st.session_state.reservas_db) + 1,
                            "Cliente": cliente_nom,
                            "Auto": nombre,
                            "Inicio": f_inicio,
                            "Fin": f_fin,
                            "Total": total_pago,
                            "Estado": "Pendiente de Comprobante"
                        }
                        st.session_state.reservas_db = pd.concat([st.session_state.reservas_db, pd.DataFrame([nueva_reserva])], ignore_index=True)
                        
                        # Botón WhatsApp con mensaje automático
                        msg = f"Hola JM Asociados, soy {cliente_nom}. Confirmo el pago de R$ {total_pago} por el alquiler de {nombre} desde {f_inicio} hasta {f_fin}."
                        wa_url = f"https://wa.me/595991681191?text={msg.replace(' ', '%20')}"
                        st.markdown(f'''<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; width:100%; font-weight:bold;">📲 NOTIFICAR PAGO AQUÍ (WhatsApp)</button></a>''', unsafe_allow_html=True)
                    else:
                        st.error("Lo sentimos, este vehículo ya está reservado en las fechas seleccionadas.")

# --- TAB 2: HISTORIAL ---
with tab2:
    st.subheader("Registros de Alquiler")
    if not st.session_state.reservas_db.empty:
        st.dataframe(st.session_state.reservas_db, use_container_width=True)
    else:
        st.info("Aún no hay reservas registradas.")

# --- TAB 3: UBICACIÓN E INSTAGRAM ---
with tab3:
    st.subheader("📍 Encuéntranos")
    st.markdown("""
    **JM ASOCIADOS - CONSULTORÍA & ALQUILER** Ciudad del Este, Paraguay.  
    """)
    # Instagram Link
    st.markdown(f'[📸 Síguenos en Instagram](https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo)')
    
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.370213197175!2d-54.6133036!3d-25.525203!2m3!1f0!2f0!3f0!3m2!1i1024!2i748!4m5!3s!4e1!5m2!1sen!2spy" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

# --- TAB 4: ADMIN FINANZAS (Protección por PIN) ---
with tab4:
    st.subheader("🔐 Área Restringida - Administración")
    pin_ingresado = st.text_input("Ingrese PIN de Administrador", type="password")
    
    if pin_ingresado == "1234": # PIN de ejemplo, cámbialo por el tuyo
        st.success("Acceso Autorizado")
        df_admin = st.session_state.reservas_db
        
        if not df_admin.empty:
            c1, c2 = st.columns(2)
            total_ingresos = df_admin["Total"].sum()
            c1.metric("Ingresos Totales", f"R$ {total_ingresos}")
            c2.metric("Reservas Activas", len(df_admin))

            # Gráfico de finanzas
            fig = px.bar(df_admin, x="Auto", y="Total", color="Auto", title="Ingresos por Vehículo", color_discrete_sequence=['#4A0404', '#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)

            # Acciones de Admin
            st.divider()
            col_ex, col_del = st.columns(2)
            
            # Exportar
            csv = df_admin.to_csv(index=False).encode('utf-8')
            col_ex.download_button("📊 EXPORTAR FINANZAS (CSV)", csv, "finanzas_jm.csv", "text/csv")
            
            # Borrar Reservas
            if col_del.button("⚠️ BORRAR TODAS LAS RESERVAS"):
                st.session_state.reservas_db = pd.DataFrame(columns=["ID", "Cliente", "Auto", "Inicio", "Fin", "Total", "Estado"])
                st.warning("Base de datos limpiada.")
                st.rerun()
        else:
            st.info("No hay datos financieros disponibles.")
    elif pin_ingresado != "":
        st.error("PIN Incorrecto.")

# --- SIDEBAR ---
if st.sidebar.button("CERRAR SESIÓN"):
    st.session_state.autenticado = False
    st.rerun()
