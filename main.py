import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles  # IMPORTANTE: Tener styles.py en la misma carpeta

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="J&M ASOCIADOS", layout="wide")
st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)

# --- BASE DE DATOS ---
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

# --- FUNCIONES ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE ALQUILER - J&M ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    texto = f"""
    ORDEN Nro: {res['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ---------------------------------------------------------------------------------------
    CLIENTE: {res['cliente']} | DOCUMENTO: {res['ci']} | WA: {res['celular']}
    AUTO: {res['auto']} | PLACA: {placa} | COLOR: {color}
    DESDE: {res['inicio']} | HASTA: {res['fin']}
    PAGO TOTAL: R$ {res['total']} (PIX MARINA BAEZ)
    ---------------------------------------------------------------------------------------
    """
    pdf.multi_cell(0, 7, texto)
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

# --- INTERFAZ ---
st.markdown("<h1>J&M ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37;">R$ {v['precio']} / día</p>
                </div>
            ''', unsafe_allow_html=True)
            with st.expander(f"Alquilar {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    if c_n and c_d and c_w:
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total}</b><br>Llave: 24510861818<br>Marina Baez - Santander</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read()))
                            conn.commit(); conn.close()
                            st.success("¡Reserva Guardada!")
                            msg = f"Hola J&M, soy {c_n}. Acabo de pagar R$ {total} por el {v['nombre']}."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div class="btn-wa">📲 ENVIAR COMPROBANTE AL WHATSAPP</div></a>', unsafe_allow_html=True)
                else: st.error("No disponible.")

with t_ubi:
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d115200.0!2d-54.6!3d-25.5!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ses!2spy!4v10" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:20px;"></iframe>', unsafe_allow_html=True)
    st.markdown('<br><a href="https://www.instagram.com/jm_asociados_consultoria" target="_blank" style="text-decoration:none;"><div style="background-color:#E1306C; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold;">📸 INSTAGRAM OFICIAL</div></a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        st.title("📊 BALANCE Y FINANZAS")
        ing, egr = res_df['total'].sum() if not res_df.empty else 0, egr_df['monto'].sum() if not egr_df.empty else 0
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS TOTALES", f"R$ {ing:,.2f}")
        c_f2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_f3.metric("FLUJO NETO", f"R$ {ing - egr:,.2f}")
        
        if not res_df.empty:
            fig = px.bar(res_df, x='auto', y='total', color='auto', title="Ingresos por Vehículo", template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#D4AF37")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("💸 REGISTRAR GASTO"):
            con = st.text_input("Concepto")
            mon = st.number_input("Monto R$", 0.0)
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, date.today()))
                conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE FLOTA")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            col_b1, col_b2 = st.columns([3, 1])
            col_b1.write(f"**{f['nombre']}** - ({f['estado']})")
            if col_b2.button("BLOQUEAR/ACTIVAR", key=f"sw{f['nombre']}"):
                nuevo = "No Disponible" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📑 RESERVAS ACTIVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                ca, cb = st.columns(2)
                if r['comprobante']: ca.image(r['comprobante'], width=200)
                f_d = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf = generar_contrato_pdf(r, f_d[0], f_d[1])
                cb.download_button("📥 CONTRATO PDF", pdf, f"Contrato_{r['cliente']}.pdf", key=f"pdf{r['id']}")
                if cb.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()