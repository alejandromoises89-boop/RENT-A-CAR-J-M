import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTILO JM ---
st.set_page_config(page_title="JM ALQUILER - SISTEMA CORPORATIVO", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; border-radius: 8px; }
    .card-auto { background-color: rgba(0,0,0,0.5); padding: 20px; border-left: 5px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .wa-btn { background-color: #25D366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
    .ig-btn { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: 1px solid white; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS PERMANENTE ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "AA-123-PY", "Gris"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "BCC-445-PY", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "DDA-778-PY", "Negro"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "XZE-001-PY", "Perla")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. GENERADOR DE CONTRATO (12 CLÁUSULAS) ---
def generar_contrato_pdf(res, placa, color):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    
    clausulas = f"""
    CONTRATO Nro: {res['id']} | FECHA: {datetime.now().strftime('%d/%m/%Y')}
    ARRENDATARIO: {res['cliente']} | VEHICULO: {res['auto']} | PLACA: {placa} | COLOR: {color}
    INICIO: {res['inicio']} | FIN: {res['fin']} | TOTAL: R$ {res['total']}

    CLÁUSULAS DEL CONTRATO:
    1. OBJETO: El arrendamiento del vehículo para transporte personal.
    2. ESTADO: Se entrega en óptimas condiciones mecánicas, eléctricas y de carrocería.
    3. COMBUSTIBLE: El vehículo debe ser devuelto con el mismo nivel de combustible.
    4. SEGURO: El arrendatario es responsable por daños que el seguro no cubra.
    5. MULTAS: Infracciones durante el periodo son responsabilidad exclusiva del arrendatario.
    6. PROHIBICIONES: Prohibido fumar, transportar animales o carga peligrosa.
    7. DEVOLUCIÓN: Retrasos generarán recargos del 10% del valor diario por hora.
    8. TERRITORIO: No se permite la salida del país sin autorización escrita.
    9. MANTENIMIENTO: Prohibido realizar alteraciones mecánicas sin consentimiento.
    10. ACCIDENTES: Informar inmediatamente a JM Asociados al 0991681191.
    11. PAGO: Realizado vía PIX a la llave: 24510861818.
    12. JURISDICCIÓN: Para cualquier pleito rigen las leyes de la República de Paraguay.

    Firma Arrendador: _________________    Firma Cliente: _________________
    """
    pdf.multi_cell(0, 6, clausulas)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. LÓGICA DE BLOQUEO ---
def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    estado_act = c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,)).fetchone()[0]
    conn.close()
    if estado_act == "Taller": return False, "⚠️ EN TALLER"
    if ocupado > 0: return False, "❌ OCUPADO EN ESTA FECHA/HORA"
    return True, "✅ DISPONIBLE"

# --- 5. SISTEMA DE ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

if st.session_state.logueado:
    col_sal = st.columns([1, 8])
    if col_sal[0].button("🚪 Salir"):
        st.session_state.logueado = False
        st.rerun()

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
    c1, c2 = st.tabs(["Ingresar", "Registrarse"])
    with c1:
        corr = st.text_input("Correo")
        passw = st.text_input("Clave", type="password")
        if st.button("ENTRAR"):
            if corr == "admin@jm.com" and passw == "8899":
                st.session_state.logueado, st.session_state.u_nom = True, "admin"; st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                u = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (corr, passw)).fetchone()
                conn.close()
                if u: st.session_state.logueado, st.session_state.u_nom = True, u[0]; st.rerun()
                else: st.error("Acceso denegado")
    with c2:
        with st.form("reg"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); cel = st.text_input("WhatsApp")
            if st.form_submit_button("Crear Cuenta"):
                conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n,e,p,cel)); conn.commit(); conn.close()
                st.success("Registrado correctamente."); st.rerun()

# --- 6. APP PRINCIPAL ---
else:
    tab1, tab2, tab3 = st.tabs(["🚗 RESERVAR", "📍 CONTACTO", "🛡️ ADMINISTRACIÓN"])

    with tab1:
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"></div>', unsafe_allow_html=True)
                with st.expander(f"Verificar fechas: {v['nombre']}"):
                    c_in, c_fn = st.columns(2)
                    dt1 = datetime.combine(c_in.date_input("Inicio", key=f"d1{v['nombre']}"), c_in.time_input("H1", time(9,0), key=f"h1{v['nombre']}"))
                    dt2 = datetime.combine(c_fn.date_input("Fin", key=f"d2{v['nombre']}"), c_fn.time_input("H2", time(10,0), key=f"h2{v['nombre']}"))
                    
                    ok, msj = esta_disponible(v['nombre'], dt1, dt2)
                    if ok:
                        st.success(msj)
                        if st.button(f"Confirmar Reserva: {v['nombre']}"):
                            total = max(1, (dt2-dt1).days) * v['precio']
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)", (st.session_state.u_nom, v['nombre'], dt1, dt2, total))
                            conn.commit(); conn.close()
                            st.success("✅ BLOQUEADO")
                            txt = f"*JM RESERVA*\nAuto: {v['nombre']}\nTotal: R$ {total}\nPIX: 24510861818"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(txt)}" class="wa-btn">📲 WHATSAPP CORPORATIVO 0991681191</a>', unsafe_allow_html=True)
                    else: st.error(msj)

    with tab2:
        st.subheader("Ubícanos")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.218563364966!2d-54.613386!3d-25.514418!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzUxLjkiUyA1NMKwMzYnNDguMiJX!5e0!3m2!1ses!2spy!4v1680000000000" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="ig-btn">📸 INSTAGRAM OFICIAL</a>', unsafe_allow_html=True)

    with tab3:
        if st.session_state.u_nom == "admin":
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            egr = pd.read_sql_query("SELECT * FROM egresos", conn)
            
            st.title("🛡️ DASHBOARD FINANCIERO")
            
            # --- Estadísticas Rápidas ---
            total_ingresos = res['total'].sum()
            total_egresos = egr['monto'].sum()
            balance = total_ingresos - total_egresos
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Ingresos Totales", f"R$ {total_ingresos:,.2f}")
            m2.metric("Egresos Totales", f"R$ {total_egresos:,.2f}")
            m3.metric("Flujo Neto", f"R$ {balance:,.2f}")
            
            # --- Gráficas ---
            col_g1, col_g2 = st.columns(2)
            if not res.empty:
                fig_ing = px.bar(res, x='auto', y='total', color='auto', title="Ingresos por Vehículo", template="plotly_dark")
                col_g1.plotly_chart(fig_ing, use_container_width=True)
                
                fig_pie = px.pie(res, values='total', names='cliente', title="Distribución por Cliente", template="plotly_dark")
                col_g2.plotly_chart(fig_pie, use_container_width=True)

            # --- Gestión de Egresos ---
            st.divider()
            with st.expander("💸 REGISTRAR NUEVO EGRESO (Gasto)"):
                with st.form("form_egreso"):
                    con_eg = st.text_input("Concepto del Gasto")
                    mon_eg = st.number_input("Monto (R$)", min_value=0.0)
                    if st.form_submit_button("Guardar Egreso"):
                        conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con_eg, mon_eg, date.today()))
                        conn.commit()
                        st.success("Gasto registrado")
                        st.rerun()

            # --- Gestión de Reservas y Contratos ---
            st.divider()
            st.subheader("📋 LISTA DE RESERVAS Y CONTRATOS")
            for _, r in res.iterrows():
                col_i, col_p, col_b = st.columns([3, 1, 1])
                col_i.write(f"ID {r['id']} | **{r['cliente']}** | {r['auto']} | {r['total']} R$")
                
                # Obtener placa y color para el contrato
                f_info = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf_c = generar_contrato_pdf(r, f_info[0], f_info[1])
                col_p.download_button("📥 CONTRATO", pdf_c, f"Contrato_{r['id']}_{r['cliente']}.pdf", key=f"pdf{r['id']}")
                
                if col_b.button("🗑️ Borrar", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()
            conn.close()