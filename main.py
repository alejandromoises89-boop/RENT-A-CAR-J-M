import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime, date, timedelta # Corregido: añadido timedelta
from fpdf import FPDF
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS | ALQUILER", layout="wide")

if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'vista_login' not in st.session_state: st.session_state.vista_login = "inicio"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'role' not in st.session_state: st.session_state.role = "user"

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, monto_brl REAL, estado TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha TEXT)')
    conn.commit()
    conn.close()

def check_disponibilidad(auto, f_i, f_f):
    conn = sqlite3.connect('jm_asociados.db')
    query = "SELECT * FROM reservas WHERE auto = ? AND NOT (fin < ? OR inicio > ?)"
    df = pd.read_sql_query(query, conn, params=(auto, str(f_i), str(f_f)))
    conn.close()
    return df.empty

init_db()

# --- 3. ESTILOS ---
def aplicar_estilo_login():
    st.markdown("""<style>
        .stApp { background: radial-gradient(circle, #4A0404 0%, #1A0000 100%); color: white; }
        .title-jm { font-family: 'Times New Roman'; color: #D4AF37; font-size: 45px; text-align: center; font-weight: bold; }
        .stButton>button { background-color: #600000!important; color: #D4AF37!important; border: 1px solid #D4AF37!important; width: 100%; }
    </style>""", unsafe_allow_html=True)

def aplicar_estilo_app():
    st.markdown("""<style>
        .stApp { background-color: #4A0404; color: white; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 10px; }
        .spec-label { background: #f0f0f0; padding: 3px 8px; border-radius: 5px; font-weight: bold; color: #4A0404; }
    </style>""", unsafe_allow_html=True)

# --- 4. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    aplicar_estilo_login()
    st.markdown('<p class="title-jm">JM ASOCIADOS</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.session_state.vista_login == "inicio":
            u = st.text_input("USUARIO")
            p = st.text_input("CONTRASEÑA", type="password")
            if st.button("INGRESAR"):
                if u == "admin" and p == "2026": st.session_state.role = "admin"
                st.session_state.autenticado = True
                st.session_state.user_name = u
                st.rerun()
            if st.button("CREAR CUENTA"): 
                st.session_state.vista_login = "registro"
                st.rerun()
        elif st.session_state.vista_login == "registro":
            st.subheader("REGISTRO")
            st.text_input("Nombre")
            if st.button("GUARDAR"): 
                st.session_state.vista_login = "inicio"
                st.rerun()

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    aplicar_estilo_app()
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Ubicación", "🛡️ Admin"])

    with tabs[0]:
        st.subheader("Nuestra Flota")
        flota = [
            {"nombre": "Toyota Vitz 2012 (Negro)", "precio": 195, "specs": "Automático | Nafta | Económico", "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
            {"nombre": "Hyundai Tucson 2012", "precio": 260, "specs": "4x2 | Diesel | Confort", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
            {"nombre": "Toyota Voxy 2009", "precio": 240, "specs": "Familiar | 7 Pasajeros | Amplio", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
            {"nombre": "Toyota Vitz 2012 (Blanco)", "precio": 195, "specs": "Automático | Aire Full | Carta Verde", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
        ]
        
        for auto in flota:
            with st.container():
                # Cuadro Blanco para el auto
                st.markdown(f'''
                <div class="card-auto">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <img src="{auto['img']}" width="250" style="border-radius:10px;">
                        <div>
                            <h2 style="margin:0; color:#4A0404;">{auto['nombre']}</h2>
                            <span class="spec-label">{auto['specs']}</span>
                            <h3 style="color:#D4AF37; margin:10px 0;">Tarifa: R$ {auto['precio']} / día</h3>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                with st.expander(f"Agendar {auto['nombre']}"):
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Inicio", min_value=date.today(), key=f"i_{auto['nombre']}")
                    f_f = c2.date_input("Fin", min_value=f_i, key=f"f_{auto['nombre']}")
                    if st.button(f"ALQUILAR", key=f"btn_{auto['nombre']}"):
                        if check_disponibilidad(auto['nombre'], f_i, f_f):
                            total = ((f_f - f_i).days + 1) * auto['precio']
                            st.success(f"Disponible! Total: R$ {total}")
                            conn = sqlite3.connect('jm_asociados.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.user_name, auto['nombre'], f_i, f_f, total, "Pendiente"))
                            conn.commit()
                            conn.close()
                        else:
                            st.error("Fechas no disponibles")

    with tabs[1]:
        st.subheader("📋 Mis Contratos")
        conn = sqlite3.connect('jm_asociados.db')
        df_c = pd.read_sql_query("SELECT * FROM reservas WHERE cliente = ?", conn, params=(st.session_state.user_name,))
        conn.close()
        if not df_c.empty:
            for _, row in df_c.iterrows():
                with st.expander(f"Reserva {row['auto']} ({row['inicio']})"):
                    st.write(f"Estado: {row['estado']}")
                    pdf_data = generar_contrato(row['cliente'], row['auto'], row['inicio'], row['fin'], row['monto_brl'])
                    st.download_button("📄 PDF", data=pdf_data, file_name=f"Contrato_{row['id']}.pdf", key=f"dl_{row['id']}")
        else: st.info("Sin reservas.")
            
# --- TAB 6: RESERVAS ---
else:
    aplicar_estilo_app()
    st.markdown('<div class="header-app"><h1>JM ASOCIADOS - Alquiler de Vehiculos </h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Localización", "⭐ Reseñas", "🛡️ Panel Master"])

    with tabs[0]:
        st.info(f"💰 Cotización BRL/PYG: {cotizacion_hoy}")
        st.subheader("Seleccione su Vehículo")
        cols = st.columns(4)
        for i, (nombre, info) in enumerate(AUTOS.items()):
            with cols[i]:
                st.markdown(f'<div class="card-auto" style="padding:10px; text-align:center;"><img src="{info["img"]}" width="100%"><br><b>{nombre}</b></div>', unsafe_allow_html=True)
                if st.button(f"Alquilar {info['color']}", key=f"btn_cat_{i}"):
                    st.session_state.auto_sel = nombre

        if "auto_sel" in st.session_state:
            st.divider()
            with st.form("form_reserva"):
                st.markdown(f"### Detalle de Reserva: {st.session_state.auto_sel}")
                c1, c2 = st.columns(2)
                nombre_c = c1.text_input("Nombre y Apellido")
                whatsapp = c2.text_input("WhatsApp")
                f_entrega = c1.date_input("Fecha Inicio", date.today())
                dias_alq = c2.number_input("Días", min_value=1, value=1)
                
                f_fin_calc = f_entrega + timedelta(days=dias_alq)
                total_r = AUTOS[st.session_state.auto_sel]['precio'] * dias_alq
                st.markdown(f"#### Total a pagar: R$ {total_r}")

                if st.form_submit_button("✅ RESERVAR"):
                    if check_disponibilidad(st.session_state.auto_sel, f_entrega, f_fin_calc):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto_brl, estado) VALUES (?,?,?,?,?,?)",
                                     (nombre_c, st.session_state.auto_sel, f_entrega, f_fin_calc, total_r, "Pendiente"))
                        conn.commit()
                        conn.close()
                        st.success("✅ ¡Reserva registrada!")
                        st.info(f"PIX: 0002")
                    else:
                        st.error("No disponible.")
                        
# --- TAB 3: UBICACIÓN & REDES ---
with tabs[2]:
    # Estilos específicos para botones sociales
    st.markdown("""
        <style>
            .btn-social {
                display: block;
                padding: 15px;
                margin: 10px 0;
                border-radius: 10px;
                text-decoration: none;
                text-align: center;
                font-weight: bold;
                color: white !important;
                transition: 0.3s;
            }
            .btn-instagram { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
            .btn-whatsapp { background-color: #25D366; }
            .btn-social:hover { transform: scale(1.02); opacity: 0.9; }
        </style>
    """, unsafe_allow_html=True)

    col_m, col_t = st.columns([2, 1])
    
    with col_m:
        st.markdown("### 📍 Nuestra Oficina Principal")
        # Iframe con coordenadas reales de la zona mencionada en CDE
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d900.2285141203064!2d-54.61217757082352!3d-25.507850298980843!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f6908556557879%3A0xc6651915993e5473!2sFarid%20Rahal%2C%20Ciudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709912345678" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
    
    with col_t:
        st.markdown("### 🏢 Dirección")
        st.write("**Edificio Aramí** (Frente al Edificio España)")
        st.write("Esq. Farid Rahal y Curupayty")
        st.write("Ciudad del Este, Paraguay")
        
        st.divider()
        
        st.markdown("### 📱 Redes Sociales")
        st.markdown(f'''
            <a href="https://instagram.com/jymasociados" target="_blank" class="btn-social btn-instagram">
                📸 Instagram Oficial
            </a>
            <a href="https://wa.me/595991681191" target="_blank" class="btn-social btn-whatsapp">
                💬 Contacto WhatsApp
            </a>
        ''', unsafe_allow_html=True)
        
# --- TAB 8: PANEL MASTER (SOLO ADMIN) ---
    if st.session_state.role == "admin":
        with tabs[4]:
            st.title("⚙️ Administración Central")
            conn = sqlite3.connect('jm_asociados.db')
            
            # --- 1. MÉTRICAS Y GRÁFICOS ---
            df_all = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_re = pd.read_sql_query("SELECT * FROM resenas", conn)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Ingresos Totales (BRL)", f"{df_all['monto_brl'].sum():,} BRL")
                st.write("Popularidad de la Flota")
                st.bar_chart(df_all['auto'].value_counts())
            with c2:
                st.write("Últimas Reseñas Recibidas")
                st.dataframe(df_re[['cliente', 'comentario', 'estrellas']].tail(5), use_container_width=True)
            
            st.divider()

            # --- 2. GESTIÓN DE REGISTROS (BORRADO DE PRUEBAS) ---
            st.subheader("🗑️ Gestión de Alquileres")
            st.write("Utilice esta opción para limpiar las pruebas antes de la exposición.")
            
            if not df_all.empty:
                st.dataframe(df_all, use_container_width=True) # Mostrar tabla completa
                
                # Botón de borrado masivo
                if st.button("BORRAR TODOS LOS ALQUILERES (Limpiar Pruebas)"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM reservas")
                    conn.commit()
                    st.warning("⚠️ Todos los registros de alquiler han sido eliminados.")
                    st.rerun()
            else:
                st.info("No hay alquileres registrados actualmente.")

            st.divider()
            
            # --- 3. EXPORTACIÓN ---
            st.write("Exportar reporte para balance de metas:")
            st.download_button("📥 Descargar Excel (CSV)", df_all.to_csv(index=False).encode('utf-8'), "reporte_jm_final.csv")
            
            conn.close()


