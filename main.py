import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles  # Asegúrate de tener styles.py con aplicar_estilo_premium()

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")
st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES LÓGICAS ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "DATOS DEL ARRENDAMIENTO", ln=True)
    pdf.set_font("Arial", size=9)
    
    # Cálculo de días para el desglose
    d_inicio = pd.to_datetime(res['inicio'])
    d_fin = pd.to_datetime(res['fin'])
    total_dias = max(1, (d_fin - d_inicio).days)
    precio_dia = res['total'] / total_dias
    
    texto_datos = f"""Orden Nro: {res['id']} | Fecha: {datetime.now().strftime('%d/%m/%Y')}
CLIENTE: {res['cliente']} | DOCUMENTO/CPF: {res['ci']}
CONTACTO: {res['celular']}
VEHICULO: {res['auto']} | PLACA: {placa} | COLOR: {color}
RECOGIDA: {res['inicio']} | DEVOLUCION: {res['fin']}
---------------------------------------------------------------------------------
PRECIO POR DIA: R$ {precio_dia:,.2f} | TOTAL DIAS: {total_dias}
TOTAL PAGADO: R$ {res['total']:,.2f} | Gs. {res['total']*1400:,.0f}
---------------------------------------------------------------------------------"""
    pdf.multi_cell(0, 6, texto_datos)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "CLAUSULAS CONTRACTUALES", ln=True)
    pdf.set_font("Arial", size=8)
    clausulas = [
        "1. OBJETO: El Arrendador cede el uso del vehículo en óptimas condiciones.",
        "2. DESTINO: Uso exclusivo para transporte personal, prohibido carga o remolque.",
        "3. DEVOLUCION: El retraso mayor a 1 hora generará multas de R$ 50/hora.",
        "4. SEGURO: Cobertura contra terceros. Daños propios a cargo del cliente.",
        "5. COMBUSTIBLE: Se entrega lleno y se recibe lleno, sin excepciones.",
        "6. MANTENIMIENTO: Prohibido realizar reparaciones externas sin aviso.",
        "7. CONDUCTOR: Solo el titular del contrato está autorizado a conducir.",
        "8. SINIESTROS: Notificación obligatoria en menos de 2 horas a JM Asociados.",
        "9. MULTAS: El cliente asume responsabilidad legal por infracciones de tránsito.",
        "10. JURISDICCION: Somometimiento legal a los tribunales de Ciudad del Este.",
        "11. PROHIBICIONES: No fumar ni transportar sustancias ilícitas en el móvil.",
        "12. RESERVA: Cancelaciones tardías (<24h) no califican para reembolso."
    ]
    for c in clausulas:
        pdf.multi_cell(0, 5, c)
    
    pdf.ln(10)
    pdf.cell(90, 10, "_________________________          _________________________", ln=True)
    pdf.cell(90, 5, "      Firma Arrendatario                        Firma Arrendador")
    return pdf.output(dest='S').encode('latin-1')

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    row = c.fetchone()
    if row and row[0] == "No Disponible":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- 4. INTERFAZ DE USUARIO ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="color:#D4AF37; font-size:20px;">R$ {v['precio']} / día</p></div>''', unsafe_allow_html=True)
            with st.expander(f"Alquilar {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"i{v['nombre']}"), c1.time_input("Hora", time(9,0), key=f"hi{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"f{v['nombre']}"), c2.time_input("Hora", time(9,0), key=f"hf{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo*", key=f"n{v['nombre']}")
                    c_d = st.text_input("CPF / Documento*", key=f"d{v['nombre']}")
                    c_e = st.text_input("Correo Electrónico*", key=f"e{v['nombre']}")
                    c_w = st.text_input("WhatsApp*", key=f"w{v['nombre']}")
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total_r = dias * v['precio']
                    total_g = total_r * 1400 
                    
                    st.info(f"📊 {dias} días | Total: R$ {total_r:,.2f} / Gs. {total_g:,.0f}")

                    if c_n and c_d and c_e and c_w:
                        st.markdown(f'<div class="pix-box"><b>PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Comprobante de Pago", type=['jpg','png'], key=f"up{v['nombre']}")
                        if st.button("FINALIZAR RESERVA", key=f"bt{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, f"{c_w} | {c_e}", v['nombre'], dt_i, dt_f, total_r, foto.read()))
                            conn.commit(); conn.close()
                            st.success("¡Reserva Confirmada!")
                            msj = f"Hola JM, soy *{c_n}* (CPF: {c_d}). Alquilé {v['nombre']} por {dias} días (R$ {total_r}). Adjunto comprobante."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msj)}" target="_blank"><div style="background-color:#25D366;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">📲 ENVIAR A WHATSAPP</div></a>', unsafe_allow_html=True)
                else: st.error("No disponible en estas fechas.")

with t_ubi:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.370347395462!2d-54.6133!3d-25.5147!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzUyLjkiUyA1NMKwMzYnNDcuOSJX!5e0!3m2!1ses!2spy!4v1620000000000" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Acceso Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME); res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn); conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("INGRESOS", f"R$ {res_df['total'].sum():,.2f}")
        c2.metric("GASTOS", f"R$ {egr_df['monto'].sum():,.2f}")
        c3.metric("NETO", f"R$ {(res_df['total'].sum() - egr_df['monto'].sum()):,.2f}")

        st.subheader("📑 GESTIÓN DE CONTRATOS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                conn = sqlite3.connect(DB_NAME)
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                conn.close()
                st.download_button("📥 DESCARGAR CONTRATO PDF", generar_contrato_pdf(r, f_d[0], f_d[1]), f"Contrato_{r['cliente']}.pdf")