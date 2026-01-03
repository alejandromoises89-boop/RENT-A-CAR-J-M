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
    .card-auto { background-color: white; color: black; padding: 25px; border-radius: 15px; margin-bottom: 15px; border: 2px solid #D4AF37; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE NEGOCIO ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL)''')
    conn.commit()
    conn.close()

def verificar_disponibilidad(auto_nombre, inicio, fin):
    conn = sqlite3.connect('jm_asociados.db')
    df = pd.read_sql_query(f"SELECT inicio, fin FROM reservas WHERE auto = '{auto_nombre}'", conn)
    conn.close()
    nuevo_ini, nuevo_fin = pd.to_datetime(inicio), pd.to_datetime(fin)
    for _, row in df.iterrows():
        if (nuevo_ini <= pd.to_datetime(row['fin'])) and (nuevo_fin >= pd.to_datetime(row['inicio'])):
            return False
    return True

def generar_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"CLIENTE: {nombre}")
    p.drawString(50, 730, f"VEHÍCULO: {auto}")
    p.drawString(50, 710, f"PERIODO: {f1} al {f2}")
    p.drawString(50, 680, "Este documento certifica la reserva del vehículo.")
    p.showPage()
    p.save()
    return buffer.getvalue()

# --- 3. FLOTA CONFIGURADA ---
flota = [
    {"nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    {"nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    {"nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    {"nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
]

# --- 4. INTERFAZ ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Usuario / Email")
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
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "⚙️ Panel Master"])

    with tabs[0]:
        for auto in flota:
            st.markdown(f'<div class="card-auto">', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} - Color: {auto['color']}")
                st.write(f"**Tarifa:** Gs. {auto['precio']:,} / día")
                f_ini = st.date_input("Recogida", key=f"i_{auto['nombre']}_{auto['color']}")
                f_fin = st.date_input("Devolución", key=f"f_{auto['nombre']}_{auto['color']}")
                
                if st.button("Alquilar", key=f"btn_{auto['nombre']}_{auto['color']}"):
                    if verificar_disponibilidad(auto['nombre'], f_ini, f_fin):
                        conn = sqlite3.connect('jm_asociados.db')
                        conn.cursor().execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto) VALUES (?,?,?,?,?)",
                                             (st.session_state.user_name, f"{auto['nombre']} {auto['color']}", str(f_ini), str(f_fin), auto['precio']))
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ Vehículo Bloqueado Exitosamente")
                        
                        # --- NOTIFICACIONES Y PAGOS ---
                        st.image("https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=PIX_24510861818_MARINA", caption="Escanea PIX - Marina Baez")
                        
                        pdf = generar_pdf(st.session_state.user_name, auto['nombre'], f_ini, f_fin)
                        st.download_button("📥 Descargar Contrato (PDF)", data=pdf, file_name="Contrato_JM.pdf")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            msg_wa = f"Hola J&M! Soy {st.session_state.user_name}, reservé el {auto['nombre']} {auto['color']} del {f_ini} al {f_fin}."
                            st.markdown(f'[📲 Notificar Empresa (WhatsApp)](https://wa.me/595991681191?text={urllib.parse.quote(msg_wa)})', unsafe_allow_html=True)
                        with col_b:
                            mailto = f"mailto:{st.session_state.user_name}?subject=Reserva J&M&body=Detalles de su alquiler..."
                            st.markdown(f'[📧 Enviar Copia al Cliente (Email)]({mailto})', unsafe_allow_html=True)
                    else:
                        st.error("❌ Fechas no disponibles para este auto.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        conn = sqlite3.connect('jm_asociados.db')
        df = pd.read_sql_query(f"SELECT auto, inicio, fin, monto FROM reservas WHERE cliente='{st.session_state.user_name}'", conn)
        st.table(df)
        conn.close()

    with tabs[2]:
        if st.session_state.role == "admin":
            conn = sqlite3.connect('jm_asociados.db')
            df_all = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.metric("Ingresos Totales", f"Gs. {df_all['monto'].sum():,}")
            st.dataframe(df_all)
            conn.close()
