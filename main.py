import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM | SISTEMA INTEGRADO", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #000000 100%); color: white; }
        .header-jm { text-align: center; color: #D4AF37; font-size: 5rem; font-weight: bold; margin-bottom: 0px; }
        .sub-header { text-align: center; color: white; font-size: 1.2rem; margin-bottom: 30px; letter-spacing: 5px; }
        .card-auto { background-color: #f8f9fa; color: #333; padding: 20px; border-radius: 15px; border-left: 5px solid #D4AF37; margin-bottom: 15px; }
        .stat-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #D4AF37; }
        .social-btn { display: inline-block; padding: 10px 20px; margin: 10px; border-radius: 50px; text-decoration: none; font-weight: bold; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS MEJORADA ---
def init_db():
    conn = sqlite3.connect('jm_master_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, correo TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, monto REAL, egreso REAL, inicio TEXT, fin TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comentarios (id INTEGER PRIMARY KEY, usuario TEXT, texto TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto, inicio, fin):
    conn = sqlite3.connect('jm_master_system.db')
    df = pd.read_sql_query("SELECT * FROM reservas WHERE auto=?", conn, params=(auto,))
    conn.close()
    if df.empty: return True
    for _, row in df.iterrows():
        res_inicio = datetime.strptime(row['inicio'], "%Y-%m-%d").date()
        res_fin = datetime.strptime(row['fin'], "%Y-%m-%d").date()
        if not (fin < res_inicio or inicio > res_fin): return False
    return True

init_db()

# --- 3. FUNCIONES DE EXPORTACIÓN ---
def get_table_download_link(df, format='csv'):
    if format == 'csv':
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        return f'<a href="data:file/csv;base64,{b64}" download="JM_Cierre_Anual.csv" class="social-btn" style="background:#2ecc71">Descargar CSV</a>'
    else:
        # Nota: Para Excel real se requiere openpyxl, aquí simulamos con CSV para compatibilidad directa
        return ""

# --- 4. ACCESO ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm">JM</div><div class="sub-header">ALQUILER DE VEHÍCULOS</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_log, tab_reg = st.tabs(["Ingresar", "Registrarse"])
        with tab_log:
            u = st.text_input("Correo")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR AL SISTEMA"):
                st.session_state.logged_in = True
                st.session_state.user_name = u.split('@')[0].upper()
                st.rerun()
else:
    # --- INTERFAZ UNIFICADA ---
    st.markdown('<h2 style="text-align:center; color:#D4AF37;">SISTEMA JM ASOCIADOS</h2>', unsafe_allow_html=True)
    
    # PIN PROTECTOR PARA SECCIONES SENSIBLES
    if 'pin_ok' not in st.session_state: st.session_state.pin_ok = False
    
    menu = st.tabs(["🚗 Alquiler", "📅 Reservas", "📍 Ubicación", "💬 Comentarios", "📊 Panel de Control"])

    # 🚗 ALQUILER
    with menu[0]:
        st.subheader("Nueva Reserva")
        c1, c2 = st.columns(2)
        f_ini = c1.date_input("Fecha Inicio", min_value=datetime.now().date())
        f_fin = c2.date_input("Fecha Fin", min_value=f_ini + timedelta(days=1))
        dias = (f_fin - f_ini).days

        flota = [
            {"n": "Toyota Vitz Negro", "p": 195, "e": 45, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"},
            {"n": "Hyundai Tucson", "p": 260, "e": 60, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"}
        ]

        for v in flota:
            disponible = verificar_disponibilidad(v['n'], f_ini, f_fin)
            total = v['p'] * dias
            with st.container():
                st.markdown('<div class="card-auto">', unsafe_allow_html=True)
                col_img, col_txt = st.columns([1, 2])
                col_img.image(v['img'])
                with col_txt:
                    st.write(f"### {v['n']}")
                    if disponible:
                        st.markdown(f"<h4 style='color:green'>LIBRE</h4>", unsafe_allow_html=True)
                        st.write(f"Monto Total: **{total} BRL**")
                        if st.button(f"Confirmar {v['n']}", key=v['n']):
                            conn = sqlite3.connect('jm_master_system.db')
                            conn.cursor().execute("INSERT INTO reservas (cliente, auto, monto, egreso, inicio, fin, timestamp) VALUES (?,?,?,?,?,?,?)",
                                                 (st.session_state.user_name, v['n'], total, v['e']*dias, f_ini, f_fin, datetime.now()))
                            conn.commit()
                            st.success("¡Reserva guardada con éxito!")
                            st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=JM_PAY_{total}")
                    else:
                        st.error("Ocupado en estas fechas")
                st.markdown('</div>', unsafe_allow_html=True)

    # 📅 HISTORIAL INTERACTIVO
    with menu[1]:
        st.subheader("Cronograma de Uso")
        conn = sqlite3.connect('jm_master_system.db')
        df_h = pd.read_sql_query("SELECT cliente, auto, inicio, fin, monto FROM reservas", conn)
        if not df_h.empty:
            st.dataframe(df_h.style.background_gradient(cmap='YlOrRd'), use_container_width=True)
        else:
            st.info("No hay registros.")

    # 📍 UBICACIÓN Y REDES
    with menu[2]:
        st.subheader("Contacto Directo")
        col_info, col_map = st.columns([1, 1.5])
        with col_info:
            st.markdown("""
            **Dirección:** C/Farid Rahal Canan, Curupayty, Ciudad del Este.  
            **Horario:** Lun - Vie: 08:00 - 16:30  
            **Teléfono:** +595 983 787810
            """)
            st.markdown(f"""
            <a href="https://wa.me/595983787810" class="social-btn" style="background:#25d366">WhatsApp</a>
            <a href="https://instagram.com/jymasociados" class="social-btn" style="background:#e1306c">Instagram</a>
            """, unsafe_allow_html=True)
        col_map.markdown('<iframe src="https://maps.google.com/?cid=3703490403065393590&g_mp=Cidnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaFRleHQ" width="100%" height="300" style="border-radius:15px;"></iframe>', unsafe_allow_html=True)

    # 💬 COMENTARIOS
    with menu[3]:
        st.subheader("Muro de Clientes")
        with st.form("coment"):
            txt = st.text_area("Deja tu reseña:")
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_master_system.db')
                conn.cursor().execute("INSERT INTO comentarios (usuario, texto, fecha) VALUES (?,?,?)", (st.session_state.user_name, txt, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
        
        conn = sqlite3.connect('jm_master_system.db')
        coms = pd.read_sql_query("SELECT * FROM comentarios ORDER BY id DESC", conn)
        for _, c in coms.iterrows():
            st.markdown(f"**{c['usuario']}** ({c['fecha']}): {c['texto']}")

    # 📊 PANEL MASTER (PIN PROTECTED)
    with menu[4]:
        st.subheader("Panel Administrativo de Cierre")
        pin = st.text_input("Clave Maestro para Finanzas", type="password")
        if pin == "2026":
            st.success("Acceso Maestro")
            conn = sqlite3.connect('jm_master_system.db')
            df_m = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            if not df_m.empty:
                # Estadísticas
                ingresos = df_m['monto'].sum()
                egresos = df_m['egreso'].sum()
                utilidad = ingresos - egresos
                
                c_s1, c_s2, c_s3 = st.columns(3)
                c_s1.metric("Ingresos Brutos", f"{ingresos} BRL")
                c_s2.metric("Egresos/Costos", f"{egresos} BRL")
                c_s3.metric("Utilidad Neta", f"{utilidad} BRL", delta=f"{utilidad/ingresos:.1%}")

                st.write("### Resumen por Vehículo")
                st.bar_chart(df_m.groupby('auto')['monto'].sum())

                # Exportación
                st.write("### Cierre de Año")
                st.markdown(get_table_download_link(df_m), unsafe_allow_html=True)
                
                if st.button("🗑️ ELIMINAR TODO EL HISTORIAL (CUIDADO)"):
                    conn.cursor().execute("DELETE FROM reservas")
                    conn.commit()
                    st.warning("Historial borrado.")
            conn.close()

    # BOTÓN FINAL
    st.markdown('<div style="text-align:center; margin-top:100px;">', unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
