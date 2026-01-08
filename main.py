import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS - Sistema Corporativo",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

# --- ESTILOS CSS PREMIUM (FONDO OSCURO Y DORADO) ---
st.markdown("""
    <style>
    /* Fondo y Textos Generales */
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3, h4 { color: #D4AF37 !important; font-family: 'Playfair Display', serif; }
    
    /* Tarjetas de Autos */
    .card-auto { 
        background-color: #1a1c23; border: 1px solid #D4AF37; 
        padding: 20px; border-radius: 15px; text-align: center;
        transition: transform 0.3s;
    }
    .card-auto:hover { transform: scale(1.02); }
    
    /* Contrato Scroll */
    .contrato-scroll {
        background-color: #f9f9f9; color: #1a1a1a; padding: 25px; 
        border-radius: 10px; height: 400px; overflow-y: scroll; 
        font-family: 'Courier New', Courier, monospace; font-size: 13px;
        line-height: 1.5; border: 2px solid #D4AF37; text-align: justify;
    }
    
    /* Calendario Estilo Dark */
    .cal-box { 
        aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; 
        font-size: 12px; border: 0.1px solid #3d4452; background: #2d323e; color: white;
    }
    .ocupado { background-color: #1a1c23 !important; color: #555 !important; }
    .raya-roja { position: absolute; width: 80%; height: 2px; background-color: #ff4b4b; top: 50%; }

    /* Botones */
    .btn-insta { background: linear-gradient(45deg, #f09433, #bc1888); color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    .btn-wa { background-color: #25D366; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
""", unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, 
        auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total_gs REAL, comprobante BLOB, whatsapp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS egresos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto_r REAL, monto_gs REAL, fecha DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flota (
        nombre TEXT PRIMARY KEY, precio_gs REAL, img TEXT, estado TEXT, 
        placa TEXT, color TEXT, marca TEXT, modelo TEXT, año TEXT, chasis TEXT)''')
    
    # Datos técnicos completos para el contrato
    autos = [
        ("Hyundai Tucson Blanco", 280000, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "BLANCO", "HYUNDAI", "TUCSON", "2012", "KMHJU81VBCU36106"),
        ("Toyota Vitz Blanco", 180000, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "BLANCO", "TOYOTA", "VITZ", "2015", "NCP13-123456"),
        ("Toyota Voxy Gris", 240000, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "GRIS", "TOYOTA", "VOXY", "2014", "ZRR80-009876")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?,?)", a)
    conn.commit(); conn.close()

init_db()

# --- FUNCIONES ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close(); bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

# --- INTERFAZ ---
st.markdown("<h1 style='text-align: center;'>J&M ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto">
                <h3>{v["nombre"]}</h3>
                <img src="{v["img"]}" width="80%">
                <p style="font-size:22px; font-weight:bold; color:#D4AF37;">Gs. {v["precio_gs"]:,.0f} / día</p>
                <p style="color:{"#25D366" if v["estado"]=="Disponible" else "#ff4b4b"};">{v["estado"]}</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander("Consultar Disponibilidad y Reservar"):
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                # Calendario Visual
                c_m1, c_m2 = st.columns(2)
                for idx, (m, a) in enumerate([(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]):
                    with [c_m1, c_m2][idx]:
                        st.write(f"**{calendar.month_name[m]} {a}**")
                        cal = calendar.monthcalendar(a, m)
                        for sem in cal:
                            cols_cal = st.columns(7)
                            for d_idx, dia in enumerate(sem):
                                if dia != 0:
                                    f_act = date(a, m, dia)
                                    es_o = f_act in ocupadas
                                    color = "ocupado" if es_o else ""
                                    raya = '<div class="raya-roja"></div>' if es_o else ""
                                    cols_cal[d_idx].markdown(f'<div class="cal-box {color}">{dia}{raya}</div>', unsafe_allow_html=True)

                st.divider()
                # Formulario de Reserva
                col_f1, col_f2 = st.columns(2)
                f_ini = col_f1.date_input("Fecha Inicio", key=f"fi_{v['nombre']}")
                h_ini = col_f1.time_input("Hora Entrega", time(10, 0), key=f"hi_{v['nombre']}")
                f_fin = col_f2.date_input("Fecha Fin", key=f"ff_{v['nombre']}")
                h_fin = col_f2.time_input("Hora Devolución", time(12, 0), key=f"hf_{v['nombre']}")
                
                c_nom = st.text_input("Nombre Completo (Arrendatario)", key=f"nom_{v['nombre']}")
                c_doc = st.text_input("Cédula / CPF / RG", key=f"doc_{v['nombre']}")
                c_tel = st.text_input("Teléfono / WhatsApp", key=f"tel_{v['nombre']}")
                
                dias = max(1, (f_fin - f_ini).days)
                total_gs = dias * v['precio_gs']
                
                if c_nom and c_doc:
                    st.markdown("#### CONTRATO GENERADO")
                    contrato_txt = f"""
                    <div class="contrato-scroll">
                    <center><b>CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR</b></center><br>
                    <b>ENTRE:</b><br>
                    <b>ARRENDADOR:</b> J&M ASOCIADOS. CI: 1.702.076-0. CURUPAYTU ESQ. FARID RAHAL.<br>
                    <b>ARRENDATARIO:</b> {c_nom.upper()}. Doc: {c_doc}. Tel: {c_tel}.<br><br>
                    <b>PRIMERA - Objeto:</b> El arrendador otorga en alquiler:<br>
                    * Marca: {v['marca']}<br>* Modelo: {v['modelo']}<br>* Año: {v['año']}<br>* Color: {v['color']}<br>
                    * Chasis: {v['chasis']}<br>* Chapa/Patente: {v['placa']}<br><br>
                    <b>SEGUNDA - Duración:</b> {dias} días. Desde {f_ini} {h_ini} hasta {f_fin} {h_fin}.<br><br>
                    <b>TERCERA - Precio:</b> Gs. {v['precio_gs']:,.0f} por día. <b>TOTAL: Gs. {total_gs:,.0f}</b>.<br><br>
                    <b>CUARTA - Depósito:</b> Gs. 5.000.000 en caso de siniestro.<br><br>
                    <b>QUINTA - Uso:</b> El ARRENDATARIO es responsable PENAL y CIVIL de todo lo ocurrido dentro del vehículo.<br><br>
                    ... (Cláusulas de kilometraje, seguro y mantenimiento)<br><br>
                    <b>DÉCIMA SEGUNDA - Firma:</b> Ambas partes aceptan en Ciudad del Este, {date.today()}.<br><br>
                    __________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;__________________________<br>
                    J&M ASOCIADOS&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{c_nom.upper()}
                    </div>
                    """
                    st.markdown(contrato_txt, unsafe_allow_html=True)
                    
                    foto = st.file_uploader("Adjuntar Comprobante de Pago", key=f"foto_{v['nombre']}")
                    if st.button("CONFIRMAR RESERVA Y ACEPTAR CONTRATO", key=f"btn_{v['nombre']}"):
                        if foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total_gs, comprobante, whatsapp) VALUES (?,?,?,?,?,?,?,?,?)",
                                         (c_nom, c_doc, c_tel, v['nombre'], datetime.combine(f_ini, h_ini), datetime.combine(f_fin, h_fin), total_gs, foto.read(), c_tel))
                            conn.commit(); conn.close()
                            st.success("Reserva guardada con éxito.")
                            msg = f"Hola JM, soy {c_nom}. Confirmo reserva de {v['nombre']} del {f_ini} al {f_fin}. Total: Gs. {total_gs:,.0f}."
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-wa">ENVIAR COMPROBANTE AL WHATSAPP</a>', unsafe_allow_html=True)
                        else: st.warning("Por favor sube el comprobante.")

with t_ubi:
    st.markdown("### 📍 Ubicación de la Empresa")
    st.write("Curupayty casi Farid Rahal, Ciudad del Este, Paraguay.")
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.123!2d-54.6123!3d-25.5123!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ0LjMiUyA1NMKwMzYnNDQuMyJX!5e0!3m2!1ses!2spy!4v1620000000000!5m2!1ses!2spy" width="100%" height="400" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
    
    st.divider()
    c_u1, c_u2 = st.columns(2)
    c_u1.markdown('<a href="https://instagram.com/jm_asociados_consultoria" class="btn-insta">📸 SEGUINOS EN INSTAGRAM</a>', unsafe_allow_html=True)
    c_u2.markdown('<a href="https://wa.me/595983635573" class="btn-wa">💬 WHATSAPP CORPORATIVO</a>', unsafe_allow_html=True)

with t_adm:
    if st.sidebar.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_df = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("🛡️ DASHBOARD DE ADMINISTRACIÓN")
        
        # --- BLOQUEO DE FECHAS (Carga Histórica) ---
        with st.expander("📅 CARGA DE RESERVAS ANTERIORES (Historial)"):
            with st.form("historial"):
                h_cli = st.text_input("Cliente"); h_auto = st.selectbox("Vehículo", flota_df['nombre'])
                h_ini = st.date_input("Inicio", value=date(2025, 1, 1)); h_fin = st.date_input("Fin", value=date(2025, 1, 5))
                h_tot = st.number_input("Monto Cobrado (Gs.)", value=0)
                if st.form_submit_button("Registrar para Bloquear Fechas"):
                    conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total_gs) VALUES (?,?,?,?,?)", (h_cli, h_auto, h_ini, h_fin, h_tot))
                    conn.commit(); st.rerun()

        # --- GASTOS ---
        with st.expander("💸 CARGAR GASTO (EGRESO)"):
            with st.form("egre"):
                con_g = st.text_input("Concepto (Ej: Lavado 100.000gs)"); col_g1, col_g2 = st.columns(2)
                mon_r = col_g1.number_input("Monto R$", value=0.0); mon_gs = col_g2.number_input("Monto Gs.", value=0)
                if st.form_submit_button("Guardar Gasto"):
                    conn.execute("INSERT INTO egresos (concepto, monto_r, monto_gs, fecha) VALUES (?,?,?,?)", (con_g, mon_r, mon_gs, date.today()))
                    conn.commit(); st.rerun()

        # --- ESTADÍSTICAS ---
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("INGRESOS TOTALES", f"Gs. {res_df['total_gs'].sum():,.0f}")
        c_m2.metric("EGRESOS TOTALES", f"Gs. {egr_df['monto_gs'].sum():,.0f}")
        
        if not res_df.empty:
            st.plotly_chart(px.line(res_df, x='inicio', y='total_gs', title="Flujo de Ingresos (Líneas)", color_discrete_sequence=['#D4AF37']))
            st.plotly_chart(px.pie(res_df, values='total_gs', names='auto', title="Ingresos por Auto", hole=0.4))

        # --- GESTIÓN DE FLOTA ---
        st.subheader("🛠️ AJUSTE DE PRECIOS Y ESTADO")
        for _, f in flota_df.iterrows():
            col_a, col_b, col_c = st.columns([2,1,1])
            nuevo_p = col_a.number_input(f"Precio {f['nombre']}", value=float(f['precio_gs']), key=f"p_{f['nombre']}")
            nuevo_e = col_b.selectbox("Estado", ["Disponible", "En Taller"], index=0 if f['estado']=="Disponible" else 1, key=f"e_{f['nombre']}")
            if col_c.button("Actualizar", key=f"up_{f['nombre']}"):
                conn.execute("UPDATE flota SET precio_gs=?, estado=? WHERE nombre=?", (nuevo_p, nuevo_e, f['nombre']))
                conn.commit(); st.rerun()

        # --- LISTADO RESERVAS ---
        st.subheader("📑 REGISTRO COMPLETO")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']} ({r['auto']})"):
                st.write(f"**Doc/CPF:** {r['ci']} | **WA:** {r['whatsapp']}")
                st.write(f"**Periodo:** {r['inicio']} al {r['fin']} | **Total:** Gs. {r['total_gs']:,.0f}")
                if r['comprobante']: 
                    st.image(r['comprobante'], width=300)
                    st.download_button("Descargar Comprobante", r['comprobante'], file_name=f"compro_{r['id']}.png")
                if st.button("Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()