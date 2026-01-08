import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILOS CSS PREMIUM (FONDO OSCURO Y DETALLES DORADOS) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; color: white; }
    .stTabs [data-baseweb="tab-list"] { background-color: #0e1117; }
    .stTabs [data-baseweb="tab"] { color: white; border-radius: 10px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    
    .card-auto { border: 1px solid #D4AF37; padding: 15px; border-radius: 15px; background: #1c1f26; text-align: center; margin-bottom: 10px; }
    .cal-header { font-size: 16px; font-weight: bold; text-align: center; color: #D4AF37; margin-bottom: 5px; }
    .cal-grid-fijo { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; max-width: 300px; margin: 0 auto; }
    .cal-box-fijo { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; font-size: 11px; background: #2d323e; color: white; border-radius: 3px; position: relative; }
    .ocupado { color: #555 !important; background-color: #1a1c23 !important; }
    .raya-roja-h { position: absolute; width: 80%; height: 2px; background-color: #ff4b4b; top: 50%; }
    
    .contrato-scroll {
        background-color: #f9f9f9; color: #333; padding: 25px; border-radius: 5px; 
        height: 400px; overflow-y: scroll; font-family: 'Courier New', Courier, monospace;
        font-size: 12px; line-height: 1.4; border: 2px solid #D4AF37; text-align: justify;
    }
    .btn-whatsapp { background-color: #25D366; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    .btn-insta { background-color: #E1306C; color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
""", unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_final.db'

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, 
        auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, precio_pactado REAL)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto_r REAL, monto_g REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, chasis TEXT, año TEXT)')
    
    # Datos iniciales de la flota si está vacía
    autos_iniciales = [
        ("HYUNDAI TUCSON", 280000, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "KMHJU81VBCU36106", "2012"),
        ("TOYOTA VITZ BLANCO", 180000, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "NCP131-XXXX", "2015")
    ]
    c.executemany("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?)", autos_iniciales)
    conn.commit(); conn.close()

init_db()

# --- FUNCIONES ---
def get_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close(); bloqueadas = set()
    for _, row in df.iterrows():
        start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
        for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
    return bloqueadas

# --- INTERFAZ ---
st.title("J&M ASOCIADOS 🚗")
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRACIÓN"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h4>{v["nombre"]}</h4><img src="{v["img"]}" width="180px"><p style="color:#D4AF37;">Gs. {v["precio"]:,.0f} / día</p><p>Estado: {v["estado"]}</p></div>', unsafe_allow_html=True)
            if v["estado"] == "En Taller":
                st.warning("Vehículo en mantenimiento")
            else:
                with st.expander(f"Agendar {v['nombre']}"):
                    ocupadas = get_fechas_ocupadas(v['nombre'])
                    # Calendario simplificado para ver disponibilidad
                    hoy = date.today()
                    c1, c2 = st.columns(2)
                    fi = c1.date_input("Recogida", key=f"fi{v['nombre']}", value=hoy)
                    hi = c1.time_input("Hora", value=time(10,0), key=f"hi{v['nombre']}")
                    ff = c2.date_input("Devolución", key=f"ff{v['nombre']}", value=hoy + timedelta(days=1))
                    hf = c2.time_input("Hora ", value=time(12,0), key=f"hf{v['nombre']}")
                    
                    c_n = st.text_input("Nombre del Arrendatario", key=f"n{v['nombre']}")
                    c_ci = st.text_input("CPF / Cédula / RG", key=f"ci{v['nombre']}")
                    c_wa = st.text_input("WhatsApp (con código de país)", key=f"wa{v['nombre']}")
                    
                    dias = (ff - fi).days
                    if dias <= 0: dias = 1
                    total = dias * v['precio']
                    
                    if c_n and c_ci:
                        st.markdown("**LEA EL CONTRATO ANTES DE CONFIRMAR:**")
                        contrato_html = f"""
                        <div class="contrato-scroll">
                            <center><b>CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR</b></center><br>
                            <b>ARRENDADOR:</b> J&M ASOCIADOS. RUC: 1.702.076-0. Domicilio: CURUPAYTU ESQ. FARID RAHAL.<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()}. Doc: {c_ci}.<br><br>
                            <b>PRIMERA - Objeto:</b> El arrendador otorga el vehículo {v['nombre']}, Año {v['año']}, Color BLANCO, Chasis {v['chasis']}, Chapa {v['placa']}.<br><br>
                            <b>SEGUNDA - Duración:</b> {dias} días. Comienza {fi} {hi} y finaliza {ff} {hf}.<br><br>
                            <b>TERCERA - Precio:</b> Gs. {v['precio']:,.0f} por día. TOTAL: Gs. {total:,.0f}. Pago por adelantado.<br><br>
                            <b>CUARTA - Depósito:</b> Gs. 5.000.000 en caso de siniestro.<br><br>
                            <b>QUINTA - Condiciones:</b> Uso personal. El ARRENDATARIO es responsable PENAL y CIVIL de lo ocurrido dentro del vehículo.<br><br>
                            <b>SEXTA - Kilometraje:</b> Límite 200km/día. Exceso: Gs. 100.000.<br><br>
                            <b>SÉPTIMA - Seguro:</b> Responsabilidad Civil, Accidentes y Rastreo Satelital.<br><br>
                            <b>DÉCIMA SEGUNDA - Firma:</b> Ambas partes aceptan en Ciudad del Este, fecha {hoy}.
                        </div>
                        """
                        st.markdown(contrato_html, unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante de Pago / Documento", key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ACEPTAR TÉRMINOS", key=f"btn{v['nombre']}"):
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, precio_pactado) VALUES (?,?,?,?,?,?,?,?,?)", 
                                         (c_n, c_ci, c_wa, v['nombre'], datetime.combine(fi, hi), datetime.combine(ff, hf), total, foto.read() if foto else None, v['precio']))
                            conn.commit(); conn.close()
                            
                            msg = f"Hola JM, soy {c_n}. Acepto el contrato.\n🚗 Vehículo: {v['nombre']}\n🗓️ Periodo: {fi} al {ff}\n💰 Total: Gs. {total:,.0f}"
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-whatsapp">ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)

with t_ubi:
    st.header("📍 Ubicación de la Empresa")
    st.write("Curupayty casi Farid Rahal, Ciudad del Este, Paraguay.")
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d3601.528373305141!2d-54.6111559!3d-25.5208003!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2zMjXCsDMxJzE0LjkiUyA1NMKwMzYnNDAuMiJX!5e0!3m2!1ses!2spy!4v1715800000000!5m2!1ses!2spy" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
    
    st.divider()
    c1, c2 = st.columns(2)
    c1.markdown('<a href="https://www.instagram.com/jymasociados" class="btn-insta">SIGUENOS EN INSTAGRAM</a>', unsafe_allow_html=True)
    c2.markdown('<a href="https://wa.me/595991681191" class="btn-whatsapp">WHATSAPP CORPORATIVO</a>', unsafe_allow_html=True)

with t_adm:
    if st.sidebar.text_input("Clave de Acceso", type="password") == "8899":
        st.subheader("🛡️ Panel de Control Administrativo")
        
        # --- CARGA DE GASTOS ---
        with st.expander("💸 CARGAR GASTO (EGRESO)"):
            with st.form("gastos"):
                concepto = st.text_input("Concepto (Ej: Lavado, Taller)")
                colg1, colg2 = st.columns(2)
                m_r = colg1.number_input("Monto en Reales (R$)", value=0.0)
                m_g = colg2.number_input("Monto en Guaraníes (Gs.)", value=0)
                if st.form_submit_button("Guardar Gasto"):
                    conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO egresos (concepto, monto_r, monto_g, fecha) VALUES (?,?,?,?)", (concepto, m_r, m_g, date.today())); conn.commit(); conn.close()
                    st.success("Gasto registrado")

        # --- GESTIÓN DE FLOTA Y PRECIOS ---
        with st.expander("⚙️ AJUSTAR PRECIOS Y ESTADOS"):
            conn = sqlite3.connect(DB_NAME); flota_db = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
            for idx, row in flota_db.iterrows():
                c_f1, c_f2, c_f3 = st.columns([2,1,1])
                nuevo_p = c_f1.number_input(f"Precio {row['nombre']}", value=float(row['precio']), key=f"p_{row['nombre']}")
                nuevo_e = c_f2.selectbox(f"Estado", ["Disponible", "En Taller"], index=0 if row['estado']=="Disponible" else 1, key=f"e_{row['nombre']}")
                if c_f3.button("Actualizar", key=f"upd_{row['nombre']}"):
                    conn = sqlite3.connect(DB_NAME); conn.execute("UPDATE flota SET precio=?, estado=? WHERE nombre=?", (nuevo_p, nuevo_e, row['nombre'])); conn.commit(); conn.close(); st.rerun()

        # --- BALANCE Y GRÁFICOS ---
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn); conn.close()
        
        st.divider()
        st.subheader("📊 Estadísticas de Ingresos vs Egresos")
        col_m1, col_m2 = st.columns(2)
        total_ingresos = res_df['total'].sum() if not res_df.empty else 0
        total_egresos = egr_df['monto_g'].sum() if not egr_df.empty else 0
        col_m1.metric("INGRESOS TOTALES", f"Gs. {total_ingresos:,.0f}")
        col_m2.metric("EGRESOS TOTALES", f"Gs. {total_egresos:,.0f}", delta_color="inverse")

        if not res_df.empty:
            st.plotly_chart(px.line(res_df, x='inicio', y='total', title="Tendencia de Ingresos", markers=True, color_discrete_sequence=['#D4AF37']))
            st.plotly_chart(px.pie(res_df, values='total', names='auto', title="Ingresos por Vehículo", hole=0.4))

        # --- REGISTRO DE CLIENTES Y COMPROBANTES ---
        st.divider()
        st.subheader("📑 Reservas y Comprobantes")
        for _, r in res_df.iterrows():
            with st.expander(f"Cliente: {r['cliente']} - {r['auto']}"):
                st.write(f"**Doc/CPF:** {r['ci']} | **WA:** {r['celular']}")
                st.write(f"**Periodo:** {r['inicio']} al {r['fin']}")
                st.write(f"**Total Pagado:** Gs. {r['total']:,.0f}")
                if r['comprobante']:
                    st.image(r['comprobante'], width=300)
                    st.download_button("Descargar Comprobante", r['comprobante'], file_name=f"comprobante_{r['cliente']}.png")
                if st.button("Eliminar Registro", key=f"del_{r['id']}"):
                    conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); conn.close(); st.rerun()