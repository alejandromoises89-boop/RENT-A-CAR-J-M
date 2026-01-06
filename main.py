import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles  # Asegúrate de tener styles.py con la función aplicar_estilo_premium()

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&display=swap');
            .stApp { background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }
            h1 { font-family: 'Cinzel', serif; color: #D4AF37; text-align: center; font-size: 4rem; }
            .card-auto { background: white; color: black; padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; margin-bottom: 15px; text-align: center; }
            .documento-papel { background: white; color: black; padding: 40px; font-family: 'Times New Roman', serif; line-height: 1.4; border: 1px solid #ccc; box-shadow: 0 0 20px rgba(0,0,0,0.5); max-width: 800px; margin: auto; }
            .clausula-header { font-weight: bold; text-decoration: underline; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, nacionalidad TEXT, direccion TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://i.ibb.co/PGrYTDhJ/2098.png", "Disponible", "AAVI502", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    
    cuerpotexto = f"""En Ciudad del Este, a {datetime.now().strftime('%d/%m/%Y')}, JM ASOCIADOS (Locador) y {res['cliente']} (Locatario) con CI {res['ci']}, nacionalidad {res.get('nacionalidad', 'N/A')} y domicilio en {res.get('direccion', 'N/A')}, acuerdan:

1. OBJETO: Alquiler del vehículo {res['auto']}, Placa: {placa}, Color: {color}.
2. PLAZO: Desde {res['inicio']} hasta {res['fin']}.
3. PRECIO: R$ {res['total']} pagaderos vía PIX.
4. RESPONSABILIDAD: El Locatario asume responsabilidad civil y penal total por accidentes.
5. COMBUSTIBLE: Debe devolverse con el mismo nivel recibido.
6. MULTAS: Las infracciones son cargo exclusivo del Locatario.
7. PROHIBICIONES: Prohibido subarrendar o conducir bajo efectos de sustancias.
8. MANTENIMIENTO: El Locatario debe cuidar el vehículo como propio.
9. SEGURO: Daños fuera de póliza o deducibles corren por el Locatario.
10. LÍMITE: Prohibida la salida del país sin permiso escrito.
11. RESCISIÓN: El incumplimiento anula el contrato de inmediato.
12. JURISDICCIÓN: Se somete a los tribunales de Ciudad del Este.

Firmas:
Locador: JM ASOCIADOS                    Locatario: {res['cliente']}"""
    
    pdf.multi_cell(0, 7, cuerpotexto)
    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "No Disponible":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- 4. INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight: bold; font-size: 20px; color: #D4AF37;">R$ {v['precio']} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    c_nac = st.text_input("Nacionalidad", key=f"nac{v['nombre']}")
                    c_dir = st.text_input("Dirección / Hotel", key=f"dir{v['nombre']}")
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total = dias * v['precio']
                    
                    if c_n and c_d:
                        st.markdown(f'<div style="background:rgba(212,175,55,0.1); padding:15px; border-radius:10px; border:1px solid #D4AF37; color:white;"><b>PAGO PIX: R$ {total}</b><br>Llave: 24510861818 (Marina Baez)</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y CONTRATO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, nacionalidad, direccion) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read(), c_nac, c_dir))
                                conn.commit(); conn.close()
                                st.success("✅ ¡Reserva y Contrato Generados!")
                                st.balloons()
                            else: st.warning("Por favor adjunte el comprobante.")

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.373447385844!2d-54.6166!3d-25.5133" width="100%" height="450" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        st.subheader("📑 GESTIÓN DE CONTRATOS")
        for _, r in res_df.iterrows():
            with st.expander(f"CONTRATO #{r['id']} - {r['cliente']}"):
                col_a, col_b = st.columns(2)
                if r['comprobante']: col_a.image(r['comprobante'], caption="Comprobante PIX", width=250)
                
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                placa, color = (f_d[0], f_d[1]) if f_d else ("N/A", "N/A")
                
                pdf_bytes = generar_contrato_pdf(r, placa, color)
                col_b.download_button("📥 DESCARGAR CONTRATO PDF", pdf_bytes, f"Contrato_{r['cliente']}.pdf")
                if col_b.button("🗑️ ELIMINAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
