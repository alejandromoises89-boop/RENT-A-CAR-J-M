import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LO PRIMERO) ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")

# --- 2. COTIZACIÓN EN LÍNEA (SEGURO) ---
def obtener_cotizacion():
    try:
        # API de cambios en tiempo real (BRL a PYG)
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0  # Valor de respaldo si falla internet

COTIZACION_DIA = obtener_cotizacion()

# --- 3. DISEÑO CSS ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&display=swap');
        .stApp {{ background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }}
        h1 {{ font-family: 'Cinzel', serif; color: #D4AF37; text-align: center; font-size: 3.5rem; }}
        .card-auto {{ background: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; text-align: center; margin-bottom: 10px; }}
        .cotizacion-barra {{ text-align: center; background: rgba(212,175,55,0.2); padding: 10px; border-radius: 10px; border: 1px solid #D4AF37; margin-bottom: 20px; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. BASE DE DATOS (REPARADA) ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de Reservas con columna total_pyg
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, 
                  inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, 
                  nacionalidad TEXT, direccion TEXT, total_pyg REAL)''')
    
    # Tabla de Egresos (la que te daba error)
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    
    # Tabla de Flota
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/PGrYTDhJ/2098.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 5. FUNCIÓN PDF (DOBLE MONEDA) ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    
    texto = f"""En Ciudad del Este, a {datetime.now().strftime('%d/%m/%Y')}, JM ASOCIADOS (Locador) y {res['cliente']} (Locatario), con CI {res['ci']}, acuerdan:

1. OBJETO: Alquiler del vehículo {res['auto']}, Placa: {placa}, Color: {color}.
2. PLAZO: Desde {res['inicio']} hasta {res['fin']}.
3. PRECIO: R$ {res['total']:,.0f} (Equivalente a Gs. {res['total_pyg']:,.0f} según cotización actual).
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
    
    pdf.multi_cell(0, 7, texto)
    return pdf.output(dest='S').encode('latin-1')

# --- 6. INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
st.markdown(f'<div class="cotizacion-barra">Cotización Online: 1 Real = {COTIZACION_DIA:,.0f} Gs.</div>', unsafe_allow_html=True)

t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        p_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto">
                <h3>{v["nombre"]}</h3>
                <img src="{v["img"]}" width="100%">
                <p style="font-weight:bold; font-size:1.5rem; color:#D4AF37; margin:0;">R$ {v['precio']} / día</p>
                <p style="color:#28a745; font-weight:bold;">Gs. {p_gs:,.0f} / día</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander(f"Alquilar {v['nombre']}"):
                c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                c_nac = st.text_input("Nacionalidad", value="Paraguaya", key=f"nac{v['nombre']}")
                c_dir = st.text_input("Dirección / Hotel", key=f"dir{v['nombre']}")
                
                f_i = st.date_input("Inicio", key=f"fi{v['nombre']}")
                f_f = st.date_input("Fin", value=date.today()+timedelta(days=1), key=f"ff{v['nombre']}")
                
                dias = max(1, (f_f - f_i).days)
                t_brl = dias * v['precio']
                t_gs = t_brl * COTIZACION_DIA
                
                st.write(f"**Total a pagar: R$ {t_brl} (Gs. {t_gs:,.0f})**")
                foto = st.file_uploader("Subir Comprobante PIX", type=['jpg','png'], key=f"f{v['nombre']}")
                
                if st.button("CONFIRMAR RESERVA", key=f"b{v['nombre']}"):
                    if c_n and c_d and foto:
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT INTO reservas (cliente, ci, auto, inicio, fin, total, comprobante, nacionalidad, direccion, total_pyg) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                     (c_n, c_d, v['nombre'], f_i, f_f, t_brl, foto.read(), c_nac, c_dir, t_gs))
                        conn.commit(); conn.close()
                        st.success("¡Reserva y Contrato Generados!")
                    else: st.error("Complete todos los campos.")

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        # Aquí ya no fallará porque init_db() creó las tablas al inicio
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        for _, r in res_df.iterrows():
            with st.expander(f"Contrato #{r['id']} - {r['cliente']}"):
                f_info = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                placa, color = (f_info[0], f_info[1]) if f_info else ("-", "-")
                
                pdf_file = generar_contrato_pdf(r, placa, color)
                st.download_button("📥 DESCARGAR CONTRATO PDF", pdf_file, f"Contrato_{r['cliente']}.pdf")
        conn.close()
