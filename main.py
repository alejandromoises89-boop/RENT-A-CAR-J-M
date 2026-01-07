import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()

# --- BASE DE DATOS ---
DB_NAME = 'jm_corporativo_permanente.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES ---
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
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_en_guaranies = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''
                <div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <img src="{v["img"]}" width="100%">
                    <p style="font-weight: bold; font-size: 20px; color: #D4AF37; margin-bottom: 2px;">
                        R$ {v['precio']} / día
                    </p>
                    <p style="font-weight: bold; color: #28a745; margin-top: 0px;">
                        Gs. {precio_en_guaranies:,.0f} / día
                    </p>
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
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    precio_dia_gs = total_gs / dias

                    if c_n and c_d and c_w:
                        st.warning("⚠️ **ATENCIÓN:** Antes de proceder al pago, es obligatorio leer el contrato de alquiler.")
                        
                        st.markdown("### 📄 CONTRATO DE ALQUILER (LECTURA OBLIGATORIA)")
                        contrato_html = f"""
                        <div style="background-color: #2b0606; color: #f1f1f1; padding: 20px; border: 1px solid #D4AF37; border-radius: 10px; height: 350px; overflow-y: scroll; font-size: 13px; line-height: 1.6; font-family: sans-serif;">
                            <center><h4 style="color:#D4AF37;">CONTRATO DE ALQUILER Y AUTORIZACIÓN PARA CONDUCIR</h4></center>
                            <b>ARRENDADOR:</b> JM ASOCIADOS | C.I. 1.702.076-0 | Domicilio: CURUPAYTU ESQUINA FARID RAHAL<br>
                            <b>ARRENDATARIO:</b> {c_n.upper()} | C.I./Documento: {c_d}<br><br>
                            <b>PRIMERA - OBJETO:</b> Se alquila el vehículo {v['nombre']} (Chapa: {v['placa']}) en perfecto estado.<br>
                            <b>SEGUNDA - DURACIÓN:</b> {dias} días. Desde {dt_i.strftime('%d/%m/%Y %H:%M')} hasta {dt_f.strftime('%d/%m/%Y %H:%M')}.<br>
                            <b>TERCERA - PRECIO:</b> Gs. {precio_dia_gs:,.0f} por día. <b>TOTAL: Gs. {total_gs:,.0f}</b>.<br>
                            <b>CUARTA - DEPÓSITO:</b> Gs. 5.000.000 en caso de accidente.<br>
                            <b>QUINTA - CONDICIONES:</b> El arrendatario es responsable PENAL y CIVIL de todo lo ocurrido dentro del vehículo.<br>
                            <b>SEXTA - KILOMETRAJE:</b> Límite 200km/día. Exceso: 100.000 Gs adicionales.<br>
                            <b>SÉPTIMA - SEGURO:</b> Cuenta con seguro básico contra terceros y rastreo satelital.<br>
                            <b>OCTAVA:</b> Mantenimiento de agua, combustible y limpieza a cargo del cliente.<br>
                            <b>NOVENA:</b> Devolución en misma condición. Retrasos generan penalización.<br>
                            <b>DÉCIMA:</b> Jurisdicción Tribunales del Alto Paraná, Paraguay.<br><br>
                            <i>Al confirmar y subir el comprobante, usted declara haber leído y aceptado todas las cláusulas.</i>
                        </div>
                        """
                        st.markdown(contrato_html, unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez - Santander</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"f{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ACEPTAR CONTRATO", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read()))
                                conn.commit(); conn.close()
                                
                                st.success("¡Reserva Guardada con Éxito!")

                                # MENSAJE WHATSAPP CON TRIPLE COMILLA (SIN ERROR)
                                msj_wa = f"""Hola JM, soy {c_n}. 
He leído el contrato y acepto los términos. 
🚗 Vehículo: {v['nombre']}
🗓️ Periodo: {dt_i.strftime('%d/%m/%Y')} al {dt_f.strftime('%d/%m/%Y')}
💰 Total: R$ {total_r}
Adjunto mi comprobante de pago."""
                                
                                texto_url = urllib.parse.quote(msj_wa)
                                link_wa = f"https://wa.me/595991681191?text={texto_url}"
                                
                                st.markdown(f'''
                                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">
                                            📲 ENVIAR COMPROBANTE AL WHATSAPP
                                        </div>
                                    </a>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("Por favor, adjunte la foto del comprobante.")
                else:
                    st.error("Vehículo no disponible para estas fechas.")

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN EXACTA</h3>", unsafe_allow_html=True)
    
    # Mapa Exacto de J&M ASOCIADOS Consultoria
    # Se utiliza el Place ID oficial (ChIJ7fT45f2P9pQRtvHHT-ZwZTM) para precisión total
    st.markdown('''
        <div style="border: 3px solid #D4AF37; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px;">
            <iframe 
                src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3601.24151703666!2d-54.6103998!3d-25.5170969!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68ffd65f8f4ed%3A0x336570e64f77f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses-419!2spy!4v1715634567890!5m2!1ses-419!2spy" 
                width="100%" 
                height="450" 
                style="border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
    ''', unsafe_allow_html=True)
    
    # Columnas para los botones de Redes Sociales
    col_social1, col_social2 = st.columns(2)
    
    with col_social1:
        # Botón de Instagram
        st.markdown('''
            <a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank" style="text-decoration:none;">
                <div style="background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
                            color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    📸 INSTAGRAM OFICIAL
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
    with col_social2:
        # Botón de WhatsApp
        # Usamos el formato internacional 595991681191 para que abra directo el chat
        st.markdown('''
            <a href="https://wa.me/595991681191" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    💬 WHATSAPP EMPRESARIAL
                </div>
            </a>
        ''', unsafe_allow_html=True)
    
    # Información adicional debajo de los botones
    st.markdown('''
        <div style="text-align:center; margin-top:20px; color:#D4AF37;">
            <p>📍 C/ Farid Rahal Canan, Curupayty, Cd. del Este 7000, Paraguay</p>
            <p>⏰ Horario de Atención: Lunes a Viernes 08:00 – 16:30</p>
        </div>
    ''', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave de Acceso", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL ESTRATÉGICO")
        
        # --- MÉTRICAS RÁPIDAS ---
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS TOTALES", f"R$ {ing:,.2f}")
        c_f2.metric("GASTOS OPERATIVOS", f"R$ {egr:,.2f}")
        c_f3.metric("UTILIDAD NETA", f"R$ {ing - egr:,.2f}")

        # --- GRÁFICOS ESTADÍSTICOS ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Distribución de Ingresos por Auto")
            if not res_df.empty:
                fig_torta = px.pie(res_df, values='total', names='auto', hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.Gold)
                st.plotly_chart(fig_torta, use_container_width=True)
        
        with col_g2:
            st.subheader("Ingresos vs Gastos")
            fig_bar = px.bar(x=["Ingresos", "Gastos"], y=[ing, egr], 
                            color=["Ingresos", "Gastos"],
                            color_discrete_map={"Ingresos": "#D4AF37", "Gastos": "#800020"})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- SECCIÓN DE GASTOS ---
        with st.expander("💸 CARGAR NUEVO GASTO / EGRESO"):
            with st.form("form_gasto"):
                con = st.text_input("Concepto del Gasto (Ej: Lavado, Mecánico)")
                mon = st.number_input("Monto en R$", min_value=0.0)
                fec = st.date_input("Fecha", date.today())
                if st.form_submit_button("Registrar Egreso"):
                    if con and mon > 0:
                        conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, fec))
                        conn.commit()
                        st.success("Gasto registrado correctamente")
                        st.rerun()

        # --- GESTIÓN DE FLOTA (DISPONIBILIDAD) ---
        st.subheader("🛠️ ESTADO DE LA FLOTA")
        for _, f in flota_adm.iterrows():
            col_a1, col_a2, col_a3 = st.columns([2, 1, 1])
            col_a1.write(f"**{f['nombre']}** | Placa: {f['placa']}")
            
            # Color del estado
            color_estado = "green" if f['estado'] == "Disponible" else "orange"
            col_a2.markdown(f'<span style="color:{color_estado}; font-weight:bold;">{f["estado"]}</span>', unsafe_allow_html=True)
            
            if col_a3.button("CAMBIAR ESTADO", key=f"btn_flota_{f['nombre']}"):
                nuevo = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit()
                st.rerun()

        # --- EXPORTACIÓN Y RESERVAS ---
        st.subheader("📑 REGISTRO DE RESERVAS Y EXPORTACIÓN")
        
        # Botón para descargar Excel
        if not res_df.empty:
            # Limpiamos el DF para el Excel (quitamos el comprobante que es pesado)
            excel_df = res_df.drop(columns=['comprobante'])
            st.download_button(
                label="📥 DESCARGAR REPORTE EXCEL",
                data=excel_df.to_csv(index=False).encode('utf-8'),
                file_name=f"Reporte_JM_{date.today()}.csv",
                mime="text/csv"
            )

        # Visualización Detallada
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                col_r1, col_r2 = st.columns(2)
                
                with col_r1:
                    st.write("**Datos del Cliente:**")
                    st.write(f"ID: {r['ci']}")
                    st.write(f"Contacto: {r['celular']}")
                    if r['comprobante']:
                        st.write("**Comprobante de Pago:**")
                        st.image(r['comprobante'], use_container_width=True)
                
                with col_r2:
                    st.write("**Acciones:**")
                    # Buscamos placa y color para el PDF
                    f_info = conn.execute("SELECT placa, color FROM flota WHERE nombre=?", (r['auto'],)).fetchone()
                    pdf_data = generar_contrato_pdf(r, f_info[0], f_info[1])
                    
                    st.download_button("📄 DESCARGAR CONTRATO", pdf_data, f"Contrato_{r['cliente']}.pdf", key=f"pdf_{r['id']}")
                    
                    if st.button("❌ ELIMINAR RESERVA", key=f"del_{r['id']}"):
                        conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()
        
        conn.close()