import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles  # Asegúrate de tener styles.py con la función aplicar_estilo_premium()

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide")
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
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CONTRATO DE LOCACIÓN DE VEHÍCULO - JM ASOCIADOS", ln=True, align='C')
    pdf.ln(5)
    
    # Datos de las Partes
    pdf.set_font("Arial", size=10)
    fecha_hoy = datetime.now().strftime('%d/%m/%Y')
    
    texto_intro = (
        f"En la ciudad de Ciudad del Este, Paraguay, en fecha {fecha_hoy}, se celebra el presente contrato "
        f"entre JM ASOCIADOS, en adelante el LOCADOR, y el Sr./Sra. {res['cliente']}, con documento "
        f"nro. {res['ci']}, en adelante el LOCATARIO. Ambas partes acuerdan las siguientes cláusulas:"
    )
    pdf.multi_cell(0, 6, texto_intro)
    pdf.ln(3)

    # Las 12 Cláusulas Legales
    clausulas = [
        ("PRIMERA (OBJETO):", f"El LOCADOR cede en alquiler al LOCATARIO el vehículo {res['auto']}, placa {placa}, color {color}."),
        ("SEGUNDA (PLAZO):", f"El periodo de vigencia será desde el {res['inicio']} hasta el {res['fin']}."),
        ("TERCERA (PRECIO):", f"El precio total convenido es de R$ {res['total']}, pagados vía PIX/Transferencia."),
        ("CUARTA (RESPONSABILIDAD):", "El LOCATARIO asume responsabilidad civil y penal por cualquier accidente o daño a terceros."),
        ("QUINTA (COMBUSTIBLE):", "El vehículo se entrega con el tanque lleno/marcado y debe devolverse en el mismo estado."),
        ("SEXTA (MULTAS):", "Cualquier infracción de tránsito durante el periodo será costeada por el LOCATARIO."),
        ("SÉPTIMA (PROHIBICIONES):", "Queda prohibido ceder el manejo a terceros no autorizados o conducir bajo efectos del alcohol."),
        ("OCTAVA (MANTENIMIENTO):", "El LOCATARIO se obliga a cuidar el vehículo, evitando malos tratos mecánicos."),
        ("NOVENA (SEGURO):", "El vehículo cuenta con seguro limitado. Daños menores corren por cuenta del LOCATARIO."),
        ("DÉCIMA (LÍMITE):", "El vehículo no podrá salir del territorio nacional sin autorización expresa."),
        ("UNDÉCIMA (RESCISIÓN):", "El incumplimiento de estas cláusulas dará derecho al LOCADOR a retirar el vehículo inmediatamente."),
        ("DUODÉCIMA (JURISDICCIÓN):", "Las partes se someten a la jurisdicción de los tribunales de Ciudad del Este.")
    ]

    for titulo, contenido in clausulas:
        pdf.set_font("Arial", 'B', 10)
        pdf.write(5, titulo + " ")
        pdf.set_font("Arial", size=10)
        pdf.write(5, contenido + "\n")
        pdf.ln(2)

    # Espacio para Firmas
    pdf.ln(15)
    pdf.cell(90, 10, "__________________________", 0, 0, 'C')
    pdf.cell(90, 10, "__________________________", 0, 1, 'C')
    pdf.cell(90, 5, "JM ASOCIADOS (LOCADOR)", 0, 0, 'C')
    pdf.cell(90, 5, f"{res['cliente']} (LOCATARIO)", 0, 1, 'C')

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
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
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
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                             (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total, foto.read()))
                                conn.commit(); conn.close()
                                
                                st.success("¡Reserva Guardada con éxito!")
                                
                                # MENSAJE WHATSAPP PROFESIONAL
                                msj_wa = (
                                    f"Hola JM, soy {c_n}.\n\n"
                                    f"📄 Mis datos: \n"
                                    f"Documento/CPF: {c_d}\n\n"
                                    f"🚗 Detalles del Alquiler: \n"
                                    f"Vehículo: {v['nombre']}\n"
                                    f"🗓️ Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                    f"🗓️ Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                    f"💰 Monto Pagado: R$ {total}\n\n"
                                    f"Aquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!"
                                )
                                texto_url = urllib.parse.quote(msj_wa)
                                link_wa = f"https://wa.me/595991681191?text={texto_url}"
                                
                                st.markdown(f'''
                                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">
                                            📲 ENVIAR DATOS Y COMPROBANTE AL WHATSAPP
                                        </div>
                                    </a>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("Por favor, adjunte la foto del comprobante.")
                else:
                    st.error("Vehículo no disponible para estas fechas.")

with t_ubi:
    st.markdown("<h3>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    
    # Mapa de Ciudad del Este (Versión estable sin errores de API)
    st.markdown('''
        <div style="border: 2px solid #D4AF37; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <iframe 
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57610.05739023021!2d-54.654344186523425!3d-25.5174415!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f690806437979b%3A0x6a2c300895318049!2sCiudad%20del%20Este%2C%20Paraguay!5e0!3m2!1ses!2spy!4v1700000000000!5m2!1ses!2spy" 
                width="100%" 
                height="450" 
                style="border:0;" 
                allowfullscreen="" 
                loading="lazy" 
                referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
    ''', unsafe_allow_html=True)
    
    # Botón de Instagram debajo del mapa
    st.markdown('<br><a href="https://www.instagram.com/jm_asociados_consultoria" target="_blank" style="text-decoration:none;"><div style="background-color:#E1306C; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:18px;">📸 VISITAR INSTAGRAM OFICIAL</div></a>', unsafe_allow_html=True)

with t_adm:
    clave = st.text_input("Clave Admin", type="password")
    if clave == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        st.title("📊 BALANCE Y FINANZAS")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS", f"R$ {ing:,.2f}")
        c_f2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_f3.metric("NETO", f"R$ {ing - egr:,.2f}")
        
        if not res_df.empty:
            fig = px.bar(res_df, x='auto', y='total', color='auto', template="plotly_dark")
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
            col_b1.write(f"*{f['nombre']}* - ({f['estado']})")
            if col_b2.button("CAMBIAR", key=f"sw{f['nombre']}"):
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

contrato_html = f"""
<div class="documento-papel">
    <center>
        <h2 style="margin-bottom:5px;">CONTRATO DE ALQUILER DE VEHÍCULO</h2>
        <p style="margin-top:0;"><b>JM ASOCIADOS</b></p>
    </center>
    
    <p>En la ciudad de Ciudad del Este, Paraguay, en fecha <b>{datetime.now().strftime('%d/%m/%Y')}</b>, se celebra el presente contrato entre <b>JM ASOCIADOS</b>, en adelante el LOCADOR, y el Sr./Sra. <b>{nombre_display}</b>, con documento nro. <b>{doc_display}</b>, nacionalidad <b>{nac_display}</b>, domiciliado en <b>{dir_display}</b>, en adelante el LOCATARIO.</p>

    <p><span class="clausula-header">PRIMERA: OBJETO.</span> El LOCADOR cede en alquiler al LOCATARIO el vehículo marca/modelo: <b>{veh_display}</b>, el cual se encuentra en óptimas condiciones de funcionamiento.</p>
    
    <p><span class="clausula-header">SEGUNDA: PLAZO.</span> El periodo de vigencia será desde el <b>{f_inicio.strftime('%d/%m/%Y')}</b> hasta el <b>{f_fin.strftime('%d/%m/%Y')}</b>, fecha en que el vehículo debe ser restituido.</p>
    
    <p><span class="clausula-header">TERCERA: PRECIO.</span> El precio total convenido por el periodo es de <b>{monto_display} Reales</b>, pagaderos al momento de la firma.</p>
    
    <p><span class="clausula-header">CUARTA: RESPONSABILIDAD.</span> El LOCATARIO asume la responsabilidad total, civil y penal, por cualquier accidente o daño a terceros.</p>
    
    <p><span class="clausula-header">QUINTA: COMBUSTIBLE.</span> El vehículo se entrega con el tanque según inventario y debe devolverse en el mismo estado.</p>
    
    <p><span class="clausula-header">SEXTA: MULTAS.</span> Cualquier infracción de tránsito durante el periodo será costeada exclusivamente por el LOCATARIO.</p>
    
    <p><span class="clausula-header">SÉPTIMA: PROHIBICIONES.</span> Queda terminantemente prohibido ceder el manejo a terceros no autorizados o conducir bajo efectos de estupefacientes.</p>
    
    <p><span class="clausula-header">OCTAVA: MANTENIMIENTO.</span> El LOCATARIO se obliga a cuidar el vehículo como propio, evitando malos tratos mecánicos.</p>
    
    <p><span class="clausula-header">NOVENA: SEGURO.</span> El vehículo cuenta con seguro limitado. Daños menores o deducibles corren por cuenta del LOCATARIO.</p>
    
    <p><span class="clausula-header">DÉCIMA: LÍMITE TERRITORIAL.</span> El vehículo no podrá salir del territorio nacional sin autorización expresa por escrito.</p>
    
    <p><span class="clausula-header">UNDÉCIMA: RESCISIÓN.</span> El incumplimiento de cualquiera de estas cláusulas dará derecho al LOCADOR a retirar el vehículo sin previo aviso.</p>
    
    <p><span class="clausula-header">DUODÉCIMA: JURISDICCIÓN.</span> Las partes se someten a la jurisdicción de los tribunales de Ciudad del Este para cualquier controversia.</p>

    <br><br>
    <div style="display: flex; justify-content: space-around;">
        <div class="firma-espacio">POR JM ASOCIADOS<br>(EL LOCADOR)</div>
        <div class="firma-espacio">{nombre_display}<br>(EL LOCATARIO)</div>
    </div>
</div>
"""

st.markdown(contrato_html, unsafe_allow_html=True)

# --- 5. ACCIONES ---
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🖨️ IMPRIMIR / GUARDAR PDF"):
        st.write("Abriendo diálogo de impresión...")

with col_btn2:
    # Generar link de WhatsApp para notificar
    texto_wa = f"Hola JM, contrato generado para {nombre}. Vehículo: {vehiculo}. Total: {monto} Reales."
    link_wa = f"https://wa.me/595991681191?text={texto_wa.replace(' ', '%20')}"
    st.markdown(f'<a href="{link_wa}" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">ALQUILAR Y NOTIFICAR AL CORPORATIVO</div></a>', unsafe_allow_html=True)
