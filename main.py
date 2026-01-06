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

# --- 2. BASE DE DATOS (CORREGIDA PARA EVITAR EL ERROR DE COLUMNAS) ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Creamos las tablas asegurando las columnas correctas
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    # Insertar flota inicial si no existe
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

# --- 3. GENERADOR DE CONTRATO ---
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
    2. ESTADO: Se entrega en óptimas condiciones mecánicas y de limpieza.
    3. COMBUSTIBLE: Se devuelve con el mismo nivel recibido.
    4. SEGURO: Responsabilidad del cliente ante daños no cubiertos.
    5. MULTAS: El cliente asume responsabilidad por infracciones de tránsito.
    6. PROHIBICIONES: No fumar ni transportar animales.
    7. DEVOLUCIÓN: Retrasos aplican recargo del 10% por hora.
    8. TERRITORIO: No salir del país sin permiso previo.
    9. MANTENIMIENTO: No realizar reparaciones sin aviso.
    10. ACCIDENTES: Reportar al 0991681191 inmediatamente.
    11. PAGO: Vía PIX a la llave: 24510861818.
    12. JURISDICCIÓN: Rigen las leyes de la República de Paraguay.

    Firma Arrendador: _________________    Firma Cliente: _________________
    """
    pdf.multi_cell(0, 6, clausulas)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. LÓGICA DE DISPONIBILIDAD ---
def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verifica si hay cruce de horarios para el mismo auto
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    if ocupado > 0: return False, "❌ VEHÍCULO NO DISPONIBLE: Ya reservado en este horario."
    return True, "✅ DISPONIBLE"

# --- 5. ACCESO ---
if 'logueado' not in st.session_state: st.session_state.logueado = False

if st.session_state.logueado:
    col_sal = st.columns([1, 10])
    if col_sal[0].button("🚪 Salir"):
        st.session_state.logueado = False
        st.rerun()

if not st.session_state.logueado:
    st.markdown("<h1 style='text-align:center;'>JM ACCESO</h1>", unsafe_allow_html=True)
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
        with st.form("registro_form"):
            n = st.text_input("Nombre"); e = st.text_input("Correo"); p = st.text_input("Clave"); cel = st.text_input("WhatsApp")
            if st.form_submit_button("Crear Cuenta"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO usuarios (nombre, correo, password, celular) VALUES (?,?,?,?)", (n,e,p,cel))
                    conn.commit(); conn.close()
                    st.success("¡Registrado! Ya puedes ingresar."); st.rerun()
                except: st.error("El correo ya existe o hay un error en los datos.")

# --- 6. APP PRINCIPAL ---
else:
    t1, t2, t3 = st.tabs(["🚗 RESERVAR", "📍 CONTACTO", "🛡️ ADMIN"])

    with t1:
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        for _, v in flota.iterrows():
            with st.container():
                st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"></div>', unsafe_allow_html=True)
                with st.expander(f"Verificar disponibilidad: {v['nombre']}"):
                    c_in, c_fn = st.columns(2)
                    dt1 = datetime.combine(c_in.date_input("Inicio", key=f"d1{v['nombre']}"), c_in.time_input("Hora Entrega", time(9,0), key=f"h1{v['nombre']}"))
                    dt2 = datetime.combine(c_fn.date_input("Fin", key=f"d2{v['nombre']}"), c_fn.time_input("Hora Devolución", time(10,0), key=f"h2{v['nombre']}"))
                    
                    ok, msj = esta_disponible(v['nombre'], dt1, dt2)
                    if ok:
                        st.success(msj)
                        if st.button(f"Confirmar Alquiler {v['nombre']}"):
                            total = max(1, (dt2-dt1).days) * v['precio']
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total) VALUES (?,?,?,?,?)", (st.session_state.u_nom, v['nombre'], dt1, dt2, total))
                            conn.commit(); conn.close()
                            st.success("✅ RESERVA BLOQUEADA")
                            txt = f"*JM RESERVA*\nAuto: {v['nombre']}\nTotal: R$ {total}\nPIX: 24510861818"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(txt)}" class="wa-btn">📲 WHATSAPP 0991681191</a>', unsafe_allow_html=True)
                    else: st.error(msj)

    with t2:
        st.subheader("Ubícanos")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14400.0!2d-54.6!3d-25.5!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzAwLjAiUyA1NMKwMzYnMDAuMCJX!5e0!3m2!1ses!2spy!4v123456789" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="ig-btn">📸 INSTAGRAM</a>', unsafe_allow_html=True)

    with t3:
        if st.session_state.u_nom == "admin":
            conn = sqlite3.connect(DB_NAME)
            res = pd.read_sql_query("SELECT * FROM reservas", conn)
            egr = pd.read_sql_query("SELECT * FROM egresos", conn)
            
            # --- Estadísticas y Gráficas ---
            st.title("📊 ESTADÍSTICAS FINANCIERAS")
            ingresos = res['total'].sum()
            gastos = egr['monto'].sum()
            
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Ingresos Totales", f"R$ {ingresos:,.2f}")
            c_m2.metric("Egresos (Gastos)", f"R$ {gastos:,.2f}")
            c_m3.metric("Flujo Neto", f"R$ {ingresos - gastos:,.2f}")
            
            if not res.empty:
                fig = px.bar(res, x='auto', y='total', color='auto', title="Ingresos por Auto", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            # --- Registrar Egresos ---
            st.divider()
            with st.expander("💸 REGISTRAR GASTO / EGRESO"):
                with st.form("f_eg"):
                    det = st.text_input("Concepto")
                    mon = st.number_input("Monto R$", min_value=0.0)
                    if st.form_submit_button("Guardar"):
                        conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (det, mon, date.today()))
                        conn.commit(); st.rerun()

            # --- Gestión de Contratos ---
            st.divider()
            st.subheader("📋 LISTA DE RESERVAS")
            for _, r in res.iterrows():
                col_i, col_p, col_b = st.columns([3, 1, 1])
                col_i.write(f"ID {r['id']} | **{r['cliente']}** | {r['auto']}")
                
                f_inf = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                pdf = generar_contrato_pdf(r, f_inf[0], f_inf[1])
                col_p.download_button("📥 CONTRATO", pdf, f"Contrato_{r['id']}.pdf", key=f"p{r['id']}")
                
                if col_b.button("🗑️ Borrar", key=f"d{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
            conn.close()