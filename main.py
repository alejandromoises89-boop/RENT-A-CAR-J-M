import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ROMANO DORADO ---
st.set_page_config(page_title="JM | Contrato Digital", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Playfair+Display:ital@0;1&display=swap');
        .stApp { background: linear-gradient(180deg, #b02121 0%, #3b0a0a 45%, #000000 100%); color: white; }
        .logo-jm { font-family: 'Cinzel', serif; color: #D4AF37; font-size: 6rem; text-align: center; font-weight: 700; margin: 0; }
        .logo-sub { font-family: 'Cinzel', serif; color: #D4AF37; font-size: 1.2rem; text-align: center; letter-spacing: 8px; margin-bottom: 30px; }
        .contrato-box { 
            background-color: white; color: #1a1a1a; padding: 40px; border-radius: 5px; 
            font-family: 'Times New Roman', serif; line-height: 1.5; border: 1px solid #ccc;
            box-shadow: 0 0 20px rgba(0,0,0,0.5); margin: 20px auto; max-width: 850px;
        }
        .clausula-titulo { font-weight: bold; text-decoration: underline; text-transform: uppercase; }
        .firma-box { border-top: 1px solid black; width: 250px; text-align: center; margin-top: 50px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE CONTRATO (12 CLÁUSULAS) ---
def generar_contrato(datos_cliente, datos_reserva):
    fecha_hoy = datetime.now().strftime("%d de %B de %Y")
    
    # Estructura del Contrato
    html_contrato = f"""
    <div class="contrato-box">
        <center>
            <h2 style="margin:0;">CONTRATO DE ALQUILER DE VEHÍCULO</h2>
            <p><b>JM ASOCIADOS CONSULTORÍA</b></p>
        </center>
        <br>
        <p>En la ciudad de Ciudad del Este, a los {fecha_hoy}, entre <b>JM ASOCIADOS</b> (El Locador) 
        y el Sr./Sra. <b>{datos_cliente['nombre']}</b>, con documento <b>{datos_cliente['doc_num']}</b>, 
        nacionalidad <b>{datos_cliente['nacionalidad']}</b> y domicilio en <b>{datos_cliente['direccion']}</b> (El Locatario), 
        se conviene lo siguiente:</p>

        <p><span class="clausula-titulo">PRIMERA: OBJETO.</span> El Locador entrega en alquiler el vehículo <b>{datos_reserva['auto']}</b> en perfecto estado.</p>
        <p><span class="clausula-titulo">SEGUNDA: PLAZO.</span> El periodo de alquiler inicia el {datos_reserva['inicio']} y finaliza el {datos_reserva['fin']}.</p>
        <p><span class="clausula-titulo">TERCERA: PRECIO.</span> El monto total asciende a <b>{datos_reserva['monto']} Reales</b>.</p>
        <p><span class="clausula-titulo">CUARTA: USO.</span> El vehículo será utilizado exclusivamente para transporte personal.</p>
        <p><span class="clausula-titulo">QUINTA: COMBUSTIBLE.</span> El Locatario deberá devolver el vehículo con el mismo nivel recibido.</p>
        <p><span class="clausula-titulo">SEXTA: SEGUROS.</span> El seguro cubre daños contra terceros según póliza vigente.</p>
        <p><span class="clausula-titulo">SÉPTIMA: MULTAS.</span> Las infracciones de tránsito son responsabilidad del Locatario.</p>
        <p><span class="clausula-titulo">OCTAVA: PROHIBICIONES.</span> Queda prohibido subarrendar el vehículo o conducir bajo efectos de alcohol.</p>
        <p><span class="clausula-titulo">NOVENA: ACCIDENTES.</span> En caso de siniestro, se debe informar a JM inmediatamente.</p>
        <p><span class="clausula-titulo">DÉCIMA: MANTENIMIENTO.</span> El mantenimiento preventivo está a cargo del Locador.</p>
        <p><span class="clausula-titulo">UNDÉCIMA: RESCISIÓN.</span> El incumplimiento de cualquier cláusula dará lugar a la rescisión inmediata.</p>
        <p><span class="clausula-titulo">DUODÉCIMA: JURISDICCIÓN.</span> Para todos los efectos legales, las partes se someten a los tribunales de Ciudad del Este.</p>
        
        <br><br>
        <div style="display: flex; justify-content: space-around;">
            <div class="firma-box">JM ASOCIADOS<br>(Locador)</div>
            <div class="firma-box">{datos_cliente['nombre']}<br>(Locatario)</div>
        </div>
        <p style="text-align:center; font-size: 0.8rem; margin-top:30px;">
            <i>Documento generado digitalmente - Aceptación mediante firma biométrica/sistema.</i>
        </p>
    </div>
    """
    return html_contrato

# --- 3. PANTALLA DE ACCESO (LOGÍN ÚNICO) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="logo-jm">JM</div><div class="logo-sub">Alquiler de Autos</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab_log, tab_reg = st.tabs(["INGRESAR", "REGISTRARSE"])
        with tab_log:
            u_e = st.text_input("Correo")
            u_p = st.text_input("Clave", type="password")
            if st.button("ENTRAR"):
                conn = sqlite3.connect('jm_final_safe.db')
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios WHERE correo=? AND password=?", (u_e, u_p))
                user = c.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.u_id = user[0]
                    st.session_state.u_data = {"nombre": user[1], "doc_num": user[6], "nacionalidad": user[7], "direccion": user[8]}
                    st.rerun()
                else: st.error("❌ No registrado")
        with tab_reg:
            with st.form("reg"):
                nom = st.text_input("Nombre Completo")
                cor = st.text_input("Email")
                cla = st.text_input("Clave", type="password")
                doc = st.text_input("Nro Documento")
                nac = st.text_input("Nacionalidad")
                dir = st.text_input("Dirección Exacta")
                if st.form_submit_button("GUARDAR MIS DATOS"):
                    conn = sqlite3.connect('jm_final_safe.db')
                    conn.cursor().execute("INSERT INTO usuarios (nombre, correo, password, doc_num, nacionalidad, direccion) VALUES (?,?,?,?,?,?)", (nom, cor, cla, doc, nac, dir))
                    conn.commit()
                    st.success("✅ Datos guardados. Ya puedes Ingresar.")

# --- 4. SECCIÓN DE CONTRATO TRAS ALQUILAR ---
else:
    st.markdown(f'<h4 style="text-align:right; color:#D4AF37;">👤 {st.session_state.u_data["nombre"]}</h4>', unsafe_allow_html=True)
    
    # Simulación de reserva para demostración
    reserva_actual = {
        "auto": "Toyota Vitz Blanco",
        "monto": 585,
        "inicio": "2026-01-10",
        "fin": "2026-01-13"
    }

    st.write("### 📄 Contrato de Alquiler Generado")
    
    # Mostramos el contrato con los datos estirados del registro
    st.markdown(generar_contrato(st.session_state.u_data, reserva_actual), unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🖨️ IMPRIMIR CONTRATO"):
            st.info("Preparando versión para imprimir...")
    with col_c2:
        st.success("📝 Al presionar 'Confirmar Alquiler', los datos se estamparon en
