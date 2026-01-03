import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import io
from reportlab.pdfgen import canvas

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%); color: white; }
    .header-jm { text-align: center; color: #D4AF37; }
    .login-box { border: 1px solid #D4AF37; padding: 25px; border-radius: 15px; background: rgba(0,0,0,0.3); }
    .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; color: #D4AF37 !important; background: transparent !important; }
    div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; font-weight: bold !important; border: 1px solid #D4AF37 !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: black !important; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #800000 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE BASE DE DATOS INTERNA ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL)''')
    conn.commit()
    conn.close()

def guardar_reserva(cliente, auto, inicio, fin, monto):
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto) VALUES (?,?,?,?,?)",
              (cliente, auto, str(inicio), str(fin), monto))
    conn.commit()
    conn.close()

def obtener_flota():
    return [
        {"id": "TUCSON", "nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
        {"id": "VITZ_W", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
        {"id": "VITZ_N", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
        {"id": "VOXY", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
    ]

# --- 3. FUNCIONES DE APOYO ---
def generar_contrato_pdf(nombre, auto, f1, f2):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(150, 800, "CONTRATO DE ALQUILER - J&M ASOCIADOS")
    p.setFont("Helvetica", 12)
    p.drawString(50, 750, f"ARRENDATARIO: {nombre}")
    p.drawString(50, 730, f"VEHÍCULO: {auto}")
    p.drawString(50, 710, f"FECHAS: Desde {f1} hasta {f2}")
    p.drawString(50, 680, "TÉRMINOS: El cliente declara recibir el vehículo en óptimas condiciones.")
    p.drawString(50, 600, "Firma del Cliente: _________________________")
    p.showPage()
    p.save()
    return buffer.getvalue()

# --- 4. INTERFAZ DE LOGIN ---
init_db()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        user = st.text_input("Usuario (admin@jymasociados.com)")
        pw = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            if user == "admin@jymasociados.com" and pw == "JM2026_MASTER":
                st.session_state.role = "admin"
                st.session_state.user_name = "ADMIN_MASTER"
                st.session_state.logged_in = True
            else:
                st.session_state.role = "user"
                st.session_state.user_name = user
                st.session_state.logged_in = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- 5. APP PRINCIPAL ---
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos & Alta Gama</p></div>', unsafe_allow_html=True)
    
    titulos = ["🚗 Catálogo", "📅 Mi Historial", "💬 Comentarios"]
    if st.session_state.role == "admin": titulos.append("⚙️ Panel de Control")
    
    tabs = st.tabs(titulos)

    with tabs[0]: # CATALOGO
        st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
        for auto in obtener_flota():
            c1, c2 = st.columns([1, 2])
            c1.image(auto['img'], use_container_width=True)
            with c2:
                st.subheader(f"{auto['nombre']} - {auto['color']}")
                st.write(f"**Tarifa:** {auto['precio']:,} Gs")
                f1 = st.date_input("Inicio", key=f"i_{auto['id']}")
                f2 = st.date_input("Fin", key=f"f_{auto['id']}")
                if st.button(f"Reservar {auto['nombre']}", key=f"btn_{auto['id']}"):
                    guardar_reserva(st.session_state.user_name, auto['nombre'], f1, f2, auto['precio'])
                    st.success("✅ Reserva Exitosa")
                    
                    pdf = generar_contrato_pdf(st.session_state.user_name, auto['nombre'], f1, f2)
                    st.download_button("📥 Descargar Contrato PDF", data=pdf, file_name="Contrato_JM.pdf")
                    
                    st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=24510861818-Marina-Baez", caption="QR PIX: Llave 24510861818")
                    
                    msg = f"Hola J&M! Reservé el {auto['nombre']} del {f1} al {f2}."
                    st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank">📲 Enviar Comprobante</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[-1]:
            st.markdown('<div style="background:white; color:black; padding:20px; border-radius:10px;">', unsafe_allow_html=True)
            st.title("Panel Administrativo")
            conn = sqlite3.connect('jm_asociados.db')
            df = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.dataframe(df)
            st.download_button("📊 Exportar Excel", data=df.to_csv().encode('utf-8'), file_name="Finanzas_JM.csv")
            conn.close()
            st.markdown('</div>', unsafe_allow_html=True)
