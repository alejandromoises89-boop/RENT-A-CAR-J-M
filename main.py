import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURACIÓN, ESTÉTICA Y DISEÑO ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%);
        color: #D4AF37;
    }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    
    input, textarea, [data-baseweb="select"], [data-baseweb="input"] {
        background-color: rgba(0,0,0,0.7) !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    .stButton>button {
        background-color: #000000 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 5px;
    }

    .card-auto {
        background-color: rgba(0,0,0,0.4);
        padding: 20px;
        border-left: 4px solid #D4AF37;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }

    .btn-contact {
        display: block; width: 100%; padding: 10px; text-align: center;
        border-radius: 5px; text-decoration: none; font-weight: bold;
        margin-top: 10px; border: 1px solid #D4AF37;
    }
    .wa { background-color: #25D366; color: white !important; }
    .ig { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS E INICIALIZACIÓN ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_name' not in st.session_state: st.session_state.u_name = ""
if 'pagina' not in st.session_state: st.session_state.pagina = "login"

def init_db():
    conn = sqlite3.connect('jm_final_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios_jm 
                 (nombre TEXT, celular TEXT, direccion TEXT, correo TEXT PRIMARY KEY, 
                  documento TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio DATE, fin DATE, 
                  h_entrega TEXT, h_devolucion TEXT, total REAL, contrato_blob BLOB)''')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, año TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    c.execute("DELETE FROM flota")
    c.executemany("INSERT INTO flota VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit(); conn.close()

init_db()

# --- 3. FUNCIONES DE APOYO ---
def generar_pdf_blob(d):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CONTRATO DE ARRENDAMIENTO JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, f"Cliente: {d['cliente']}\nVehiculo: {d['auto']}\nChapa: {d['chapa']}\nPeriodo: {d['inicio']} al {d['fin']}\nTotal: R$ {d['total']}\n\nFirma Digital Registrada: {d['firma']}")
    return pdf.output(dest='S').encode('latin-1')

def get_fechas_bloqueadas(auto):
    conn = sqlite3.connect('jm_final_v6.db')
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, r in df.iterrows():
        start = datetime.strptime(r['inicio'], '%Y-%m-%d').date()
        end = datetime.strptime(r['fin'], '%Y-%m-%d').date()
        while start <= end:
            bloqueadas.add(start); start += timedelta(days=1)
    return bloqueadas

# --- 4. INTERFAZ DE ACCESO ---
if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.markdown("<h2 style='text-align:center;'>Acceso JM</h2>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; font-size:60px;'>🔒</h1>", unsafe_allow_html=True)
        email = st.text_input("Correo")
        pw = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if email == "admin@jm.com" and pw == "8899":
                st.session_state.logueado = True; st.session_state.u_name = "admin"; st.rerun()
            else:
                conn = sqlite3.connect('jm_final_v6.db')
                user = conn.execute("SELECT nombre FROM usuarios_jm WHERE correo=? AND password=?", (email, pw)).fetchone()
                conn.close()
                if user:
                    st.session_state.logueado = True; st.session_state.u_name = user[0]; st.rerun()
                else: st.error("Datos incorrectos")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("Crear Cuenta"): st.session_state.pagina = "registro"; st.rerun()
        if c2.button("Olvidé mi contraseña"): st.session_state.pagina = "recuperar"; st.rerun()
        if c3.button("🔑 Biometría"): st.info("Escaneando FaceID/Huella...")

    elif st.session_state.pagina == "registro":
        st.markdown("### Registro de Nuevo Cliente")
        with st.form("reg_form"):
            n = st.text_input("Nombre Completo"); cel = st.text_input("Celular"); dir = st.text_input("Dirección")
            em = st.text_input("Correo"); doc = st.text_input("Documento (CPF/RG/CI/Pasaporte)"); psw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Guardar para Siempre"):
                conn = sqlite3.connect('jm_final_v6.db')
                conn.execute("INSERT INTO usuarios_jm VALUES (?,?,?,?,?,?)", (n, cel, dir, em, doc, psw))
                conn.commit(); conn.close()
                st.success("¡Registrado!"); st.session_state.pagina = "login"; st.rerun()
        if st.button("Volver"): st.session_state.pagina = "login"; st.rerun()

    elif st.session_state.pagina == "recuperar":
        st.markdown("### Recuperar Acceso")
        m = st.text_input("Correo registrado")
        if st.button("Enviar enlace"): st.success(f"Enlace enviado a {m}"); st.session_state.pagina = "login"; st.rerun()

# --- 5. APLICACIÓN PRINCIPAL ---
else:
    st.markdown("<h2 style='text-align:center;'>JM ALQUILER DE VEHÍCULOS</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Cerrar Sesión"): st.session_state.logueado = False; st.session_state.pagina = "login"; st.rerun()

    tabs = st.tabs(["🚗 Flota", "📍 Ubicación", "🛡️ Admin Máster"])

    with tabs[0]:
        conn = sqlite3.connect('jm_final_v6.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        conn.close()
        for _, a in df_a.iterrows():
            with st.container():
                st.markdown(f'''<div class="card-auto">
                    <img src="{a['img']}" width="100%" style="max-width:350px; border-radius:10px; border:1px solid #D4AF37;">
                    <h3>{a['nombre']}</h3>
                    <p>{a['color']} | {a['año']} | Chapa: {a['chapa']}</p>
                    <h4 style="color:#D4AF37;">R$ {a['precio']} / día</h4>
                </div>''', unsafe_allow_html=True)
                
                bloq = get_fechas_bloqueadas(a['nombre'])
                with st.expander("RESERVAR VEHÍCULO"):
                    firma = st.text_input("Firma Digital (Nombre Completo)", key=f"f_{a['nombre']}")
                    c1, c2 = st.columns(2)
                    d_i = c1.date_input("Entrega", date.today(), key=f"di_{a['nombre']}")
                    h_e = c1.time_input("Hora Entrega", time(9,0), key=f"he_{a['nombre']}")
                    d_f = c2.date_input("Devolución", d_i + timedelta(days=1), key=f"df_{a['nombre']}")
                    h_d = c2.time_input("Hora Devolución", time(9,0), key=f"hd_{a['nombre']}")
                    
                    if d_i in bloq or d_f in bloq:
                        st.error("⚠️ Fechas ya reservadas.")
                    else:
                        total = max((d_f - d_i).days, 1) * a['precio']
                        st.write(f"### Total: R$ {total}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn_{a['nombre']}"):
                            if not firma: st.error("Debe firmar")
                            else:
                                pdf = generar_pdf_blob({'cliente':st.session_state.u_name,'auto':a['nombre'],'chapa':a['chapa'],'inicio':d_i,'fin':d_f,'total':total,'firma':firma})
                                conn = sqlite3.connect('jm_final_v6.db')
                                conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, h_entrega, h_devolucion, total, contrato_blob) VALUES (?,?,?,?,?,?,?,?)",
                                             (st.session_state.u_name, a['nombre'], d_i, d_f, str(h_e), str(h_d), total, pdf))
                                conn.commit(); conn.close()
                                st.success("✅ Reserva y Contrato guardados.")
                                
                                # MENSAJE DE WHATSAPP FORMAL CON DATOS PIX
                                msg = (f"Hola, un saludo cordial de JM ALQUILER DE VEHÍCULOS. 👋\n\n"
                                       f"Me presento, soy el sistema de reservas de JM. He registrado su solicitud con éxito:\n"
                                       f"🚗 Vehículo: {a['nombre']}\n"
                                       f"📅 Periodo: {d_i} al {d_f}\n"
                                       f"💰 Total a pagar: R$ {total}\n\n"
                                       f"📍 DATOS PARA EL PAGO (PIX):\n"
                                       f"🔹 Llave Pix: 24510861818\n"
                                       f"🔹 Banco: Santander\n"
                                       f"🔹 Titular: Marina Baez\n\n"
                                       f"Por favor, adjunte su comprobante de pago por este medio para validar su reserva definitiva. ¡Gracias por elegirnos!")
                                
                                st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" class="btn-contact wa">📤 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)

    with tabs[1]:
        # MAPA CORREGIDO APUNTANDO A J&M ASOCIADOS
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3600.957544066063!2d-54.6103998!3d-25.5170969!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68fbd64f8f4ed%3A0x336570e64f07f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses-419!2spy!4v1715600000000!5m2!1ses-419!2spy" width="100%" height="400" style="border:1px solid #D4AF37; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://wa.me/595991681191" class="btn-contact wa">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact ig">📸 Instagram Oficial</a>', unsafe_allow_html=True)

    with tabs[2]:
        if st.session_state.u_name == "admin":
            st.markdown("### 🛡️ PANEL MÁSTER Y FINANZAS")
            conn = sqlite3.connect('jm_final_v6.db')
            df_r = pd.read_sql_query("SELECT id, cliente, auto, inicio, fin, total, contrato_blob FROM reservas", conn)
            conn.close()

            if not df_r.empty:
                st.markdown("#### 📊 Análisis de Ingresos")
                col_m1, col_m2, col_m3 = st.columns(3)
                total_ingresos = df_r['total'].sum()
                promedio_reserva = df_r['total'].mean()
                total_reservas = len(df_r)

                col_m1.metric("Ingresos Totales", f"R$ {total_ingresos:,.2f}")
                col_m2.metric("Nº de Reservas", total_reservas)
                col_m3.metric("Ticket Promedio", f"R$ {promedio_reserva:,.2f}")

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_auto = px.bar(df_r.groupby('auto')['total'].sum().reset_index(), 
                                      x='auto', y='total', title="Ingresos por Vehículo",
                                      color_discrete_sequence=['#D4AF37'])
                    fig_auto.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#D4AF37")
                    st.plotly_chart(fig_auto, use_container_width=True)

                with col_g2:
                    fig_pie = px.pie(df_r, values='total', names='auto', title="Distribución de Ventas",
                                     color_discrete_sequence=px.colors.sequential.YlOrBr)
                    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="#D4AF37")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.divider()

                st.markdown("#### 📄 Gestión de Contratos")
                for _, r in df_r.iterrows():
                    with st.container():
                        c_i, c_b = st.columns([3,1])
                        c_i.write(f"**ID:** {r['id']} | **Cliente:** {r['cliente']} | **Auto:** {r['auto']} | **Total:** R$ {r['total']}")
                        if r['contrato_blob']:
                            c_b.download_button("📄 Bajar Contrato", r['contrato_blob'], f"Contrato_{r['id']}.pdf", "application/pdf", key=f"dl_{r['id']}")
                    st.divider()
            else:
                st.info("Aún no hay datos financieros para mostrar.")

            st.markdown("#### 🗑️ Zona de Seguridad")
            pin = st.text_input("PIN Maestro para Eliminar Datos", type="password")
            if st.button("LIMPIAR TODOS LOS REGISTROS"):
                if pin == "0000":
                    conn = sqlite3.connect('jm_final_v6.db'); conn.execute("DELETE FROM reservas"); conn.commit(); conn.close()
                    st.success("Historial borrado"); st.rerun()
                else: st.error("PIN Incorrecto")
        else: st.warning("Acceso exclusivo Admin.")