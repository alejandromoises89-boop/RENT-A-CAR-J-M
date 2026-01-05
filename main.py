import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from fpdf import FPDF
import urllib.parse
import requests

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA TOTAL", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto {
        background-color: white; color: black; padding: 20px;
        border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 15px;
    }
    .btn-wa { 
        background-color: #25D366; color: white !important; padding: 12px; 
        border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold;
    }
    .btn-insta { 
        background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; 
        padding: 12px; border-radius: 10px; text-align: center; display: block; text-decoration: none; font-weight: bold;
    }
    @media (max-width: 600px) {
        .card-auto { flex-direction: column !important; text-align: center; }
        .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 5px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCIA Y ESTADO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = "user"
if 'vista' not in st.session_state: st.session_state.vista = "login"

# --- 3. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, año TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, total REAL, tipo TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS resenas (cliente TEXT, estrellas INTEGER, comentario TEXT)')
    
    # Datos iniciales de la flota
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

init_db()

# --- 4. FUNCIONES TÉCNICAS ---
def get_cotizacion():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=2)
        return r.json()['rates']['PYG']
    except: return 1450.0

def get_fechas_ocupadas(auto):
    conn = sqlite3.connect('jm_final_pro.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    fechas = []
    for _, r in df.iterrows():
        start, end = pd.to_datetime(r['inicio']).date(), pd.to_datetime(r['fin']).date()
        while start <= end:
            fechas.append(start)
            start += timedelta(days=1)
    return fechas

def generar_contrato(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    clausulas = [
        f"1. OBJETO: El Arrendador cede el uso del vehículo {d['auto']} (Chasis: {d['chasis']}, Chapa: {d['chapa']}) al cliente {d['cliente']}.",
        f"2. PLAZO: Desde {d['inicio']} hasta {d['fin']}.",
        f"3. PRECIO: El monto total es de R$ {d['total']}.",
        "4. GARANTÍA: Se establece un depósito de seguridad obligatorio.",
        "5. SEGURO: Cobertura contra terceros incluida.",
        "6. COMBUSTIBLE: Retorno con el mismo nivel de entrega.",
        "7. MULTAS: Responsabilidad absoluta del arrendatario.",
        "8. MANTENIMIENTO: Prohibido reparaciones externas sin aviso.",
        "9. CARTA VERDE: Necesaria para cruce de fronteras.",
        "10. DAÑOS: El cliente asume costos por desperfectos causados.",
        "11. LIMPIEZA: Cargo adicional si el vehículo vuelve sucio.",
        "12. LEY: Sujeto a las leyes de la República del Paraguay."
    ]
    for c in clausulas:
        pdf.multi_cell(0, 7, c)
        pdf.ln(1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LÓGICA DE NAVEGACIÓN ---
cot = get_cotizacion()

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.session_state.vista == "login":
            u = st.text_input("Usuario / Email")
            p = st.text_input("Contraseña", type="password")
            if st.button("INGRESAR"):
                if u == "admin" and p == "8899": st.session_state.role = "admin"
                st.session_state.autenticado = True; st.session_state.user = u; st.rerun()
            if st.button("Crear Cuenta"): st.session_state.vista = "reg"; st.rerun()
            if st.button("Olvidé mi contraseña"): st.warning("Enlace de recuperación enviado al correo.")
        else:
            st.subheader("Registro")
            st.text_input("Nombre Completo")
            st.text_input("Email")
            if st.button("Registrar"): st.session_state.vista = "login"; st.rerun()
            if st.button("Volver"): st.session_state.vista = "login"; st.rerun()
else:
    st.markdown(f"<div style='text-align:right; color:#D4AF37;'>Cotización: 1 BRL = {cot:,.0f} PYG</div>", unsafe_allow_html=True)
    t = st.tabs(["🚗 Flota", "📍 Mapa", "⭐ Reseñas", "🛡️ Panel Master"])

    with t[0]:
        conn = sqlite3.connect('jm_final_pro.db')
        df_f = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        for _, a in df_f.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="200" style="float:left; margin-right:20px; border-radius:10px;">
                    <h3>{a['nombre']} ({a['año']})</h3>
                    <p>Color: {a['color']} | Chapa: {a['chapa']}</p>
                    <h4 style="color:#D4AF37;">R$ {a['precio']} (~ {(a['precio']*cot):,.0f} PYG)</h4>
                    <p>Estado: <b>{a['estado']}</b></p>
                    <div style="clear:both;"></div></div>''', unsafe_allow_html=True)
                
                if a['estado'] == "Disponible":
                    with st.expander("Reservar y Generar Contrato"):
                        f_i = st.date_input("Inicio", date.today(), key=f"i_{a['nombre']}")
                        f_f = st.date_input("Fin", f_i + timedelta(days=1), key=f"f_{a['nombre']}")
                        bloq = get_fechas_ocupadas(a['nombre'])
                        if f_i in bloq or f_f in bloq:
                            st.error("Fechas no disponibles")
                        else:
                            total = (f_f - f_i).days * a['precio']
                            if st.button("Confirmar Reserva", key=f"b_{a['nombre']}"):
                                conn = sqlite3.connect('jm_final_pro.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total, tipo) VALUES (?,?,?,?,?,?)",
                                             (st.session_state.user, a['nombre'], f_i, f_f, total, "Ingreso"))
                                conn.commit(); conn.close()
                                
                                # WhatsApp
                                msg = f"Reserva JM: {a['nombre']} para {st.session_state.user}. Total R$ {total}"
                                url = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                                st.markdown(f'<a href="{url}" class="btn-wa">Notificar WhatsApp Corporativo</a>', unsafe_allow_html=True)
                                
                                # Contrato
                                pdf = generar_contrato({'cliente':st.session_state.user,'auto':a['nombre'],'inicio':f_i,'fin':f_f,'total':total,'chasis':a['chasis'],'chapa':a['chapa']})
                                st.download_button("Descargar Contrato (12 Cláusulas)", pdf, "Contrato.pdf")

    with t[1]:
        st.markdown('<iframe src="https://maps.app.goo.gl/YEHnzNxYwgKJePxt5?g_st=awb" width="100%" height="400"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-insta">IR A INSTAGRAM</a>', unsafe_allow_html=True)

    with t[2]:
        val = st.feedback("stars")
        com = st.text_area("Comentario")
        if st.button("Publicar Reseña"): st.success("¡Gracias!")

    if st.session_state.role == "admin":
        with t[3]:
            st.title("🛡️ Administración Master")
            conn = sqlite3.connect('jm_final_pro.db')
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            c1, c2 = st.columns(2)
            c1.metric("Ingresos Totales", f"R$ {df_res['total'].sum():,}")
            fig = px.bar(df_res, x="auto", y="total", color="auto", title="Ingresos por Auto")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("⚙️ Editar Flota")
            auto_sel = st.selectbox("Vehículo", df_f['nombre'].tolist())
            with st.form("edit"):
                new_ch = st.text_input("Chasis", value=df_f[df_f['nombre']==auto_sel]['chasis'].iloc[0])
                new_cp = st.text_input("Chapa", value=df_f[df_f['nombre']==auto_sel]['chapa'].iloc[0])
                new_est = st.selectbox("Estado", ["Disponible", "Taller"])
                if st.form_submit_button("Actualizar"):
                    conn.execute("UPDATE flota SET chasis=?, chapa=?, estado=? WHERE nombre=?", (new_ch, new_cp, new_est, auto_sel))
                    conn.commit(); st.rerun()
            
            if st.button("⚠️ BORRAR TODO"):
                if st.text_input("PIN 0000") == "0000":
                    conn.execute("DELETE FROM reservas"); conn.commit(); st.rerun()
            conn.close()
