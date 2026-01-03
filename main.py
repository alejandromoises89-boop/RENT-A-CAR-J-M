import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
from datetime import datetime
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS | PORTAL", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
    .header-jm { text-align: center; color: #D4AF37; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #800000 !important; text-decoration: underline; }
    .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; margin-bottom: 10px; border: 2px solid #D4AF37; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA DE BLOQUEO ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comentarios 
                 (id INTEGER PRIMARY KEY, usuario TEXT, mensaje TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto_nombre, inicio, fin):
    conn = sqlite3.connect('jm_asociados.db')
    df = pd.read_sql_query(f"SELECT inicio, fin FROM reservas WHERE auto = '{auto_nombre}'", conn)
    conn.close()
    
    nuevo_ini = pd.to_datetime(inicio)
    nuevo_fin = pd.to_datetime(fin)
    
    for _, row in df.iterrows():
        exis_ini = pd.to_datetime(row['inicio'])
        exis_fin = pd.to_datetime(row['fin'])
        # Lógica de solapamiento
        if (nuevo_ini <= exis_fin) and (nuevo_fin >= exis_ini):
            return False
    return True

def guardar_reserva(cliente, auto, inicio, fin, monto):
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto) VALUES (?,?,?,?,?)",
              (cliente, auto, str(inicio), str(fin), monto))
    conn.commit()
    conn.close()

def generar_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"CLIENTE: {nombre}")
    p.drawString(50, 730, f"VEHÍCULO: {auto}")
    p.drawString(50, 710, f"PERIODO: {f1} al {f2}")
    p.drawString(50, 680, "VALIDEZ: Este documento confirma la reserva ejecutiva del vehículo.")
    p.showPage()
    p.save()
    return buffer.getvalue()

# --- 3. DATOS DE LA FLOTA ---
flota = [
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}, # Link genérico estable
    {"nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

# --- 4. CONTROL DE ACCESO ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Correo o Teléfono")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if u == "admin@jymasociados.com" and p == "JM2026_MASTER":
                st.session_state.role, st.session_state.user_name = "admin", "ADMIN_MASTER"
            else:
                st.session_state.role, st.session_state.user_name = "user", u
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios", "⚙️ Panel Master"])

    with tabs[0]: # CATALOGO
        for auto in flota:
            st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} ({auto['color']})")
                st.write(f"**Tarifa Diaria:** Gs. {auto['precio']:,}")
                f_ini = st.date_input("Fecha Recogida", key=f"ini_{auto['nombre']}_{auto['color']}")
                f_fin = st.date_input("Fecha Devolución", key=f"fin_{auto['nombre']}_{auto['color']}")
                
                if st.button(f"Alquilar {auto['nombre']} {auto['color']}", key=f"btn_{auto['nombre']}_{auto['color']}"):
                    if verificar_disponibilidad(auto['nombre'], f_ini, f_fin):
                        guardar_reserva(st.session_state.user_name, auto['nombre'], f_ini, f_fin, auto['precio'])
                        st.success("✅ ¡Reserva Exitosa! No hay choque de fechas.")
                        pdf = generar_pdf(st.session_state.user_name, auto['nombre'], f_ini, f_fin)
                        st.download_button("📥 Descargar Contrato", data=pdf, file_name="Contrato_JM.pdf")
                        st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_24510861818_MARINA", caption="Escanea para pagar PIX")
                    else:
                        st.error("❌ Vehículo NO disponible en esas fechas. Ya existe una reserva.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # HISTORIAL
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        conn = sqlite3.connect('jm_asociados.db')
        df_h = pd.read_sql_query(f"SELECT auto, inicio, fin, monto FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        st.table(df_h)
        conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]: # COMENTARIOS
        st.subheader("Reseñas de Clientes")
        txt = st.text_area("Escribe tu experiencia:")
        if st.button("Publicar Reseña"):
            conn = sqlite3.connect('jm_asociados.db')
            conn.cursor().execute("INSERT INTO comentarios (usuario, mensaje, fecha) VALUES (?,?,?)", (st.session_state.user_name, txt, str(datetime.now())))
            conn.commit()
            conn.close()
            st.success("¡Gracias!")

    with tabs[3]: # PANEL MASTER
        if st.session_state.role == "admin":
            conn = sqlite3.connect('jm_asociados.db')
            df_m = pd.read_sql_query("SELECT * FROM reservas", conn)
            df_c = pd.read_sql_query("SELECT * FROM comentarios", conn)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Ingresos Totales", f"Gs. {df_m['monto'].sum():,}")
            m2.metric("Total Reservas", len(df_m))
            m3.metric("Comentarios", len(df_c))
            
            st.write("### Ocupación de Flota")
            st.bar_chart(df_m['auto'].value_counts())
            st.dataframe(df_m)
            conn.close()
        else:
            st.warning("Acceso exclusivo para administradores.")
