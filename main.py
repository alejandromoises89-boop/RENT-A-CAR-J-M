import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA OFICIAL", layout="wide")

def aplicar_estilos_jm():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle, #800000 0%, #2a0000 100%); color: white; }
        .header-jm { background-color: white; padding: 20px; text-align: center; border-bottom: 5px solid #D4AF37; border-radius: 0 0 25px 25px; margin-bottom: 20px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 45px; margin: 0; }
        .header-jm p { color: #800000; font-size: 18px; font-weight: bold; margin: 0; }
        .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 15px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y DATOS TÉCNICOS ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, 
                  chasis TEXT, chapa TEXT, color TEXT, ano TEXT, modelo TEXT)''')
    
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        autos_data = [
            ("Hyundai Tucson", 260.0, "https://i.ibb.co/6R2M3S1/tucson.png", "Disponible", "TUC-993882771", "AA-123-ZZ", "Gris Plata", "2012", "Tucson GL"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VITZ-0012233", "BCC-445", "Blanco", "2010", "Vitz RS"),
            ("Toyota Vitz Negro", 195.0, "https://i.postimg.cc/mD8T7m8r/vitz-negro.png", "Disponible", "VITZ-9988776", "XAM-990", "Negro", "2011", "Vitz Style"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-5566778", "HHP-112", "Perla", "2009", "Voxy ZS")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano, modelo) VALUES (?,?,?,?,?,?,?,?,?)", autos_data)
    conn.commit()
    conn.close()

# --- 3. GENERADOR DE CONTRATO (TODAS LAS CLÁUSULAS) ---
def generar_contrato_oficial(datos, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 9)
    pdf.cell(0, 4, "JM CONSULTORA-CONTABILIDAD-JURIDICA-SERVICIOS MIGRACIONES", ln=True)
    pdf.set_font("Times", '', 9)
    pdf.cell(0, 4, f"Ciudad del Este, {date.today().day} de {date.today().month} del {date.today().year}.-", ln=True, align='R')
    pdf.ln(3)
    
    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 7, "CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    
    pdf.set_font("Times", 'B', 9)
    pdf.cell(0, 5, f"ARRENDADOR: J&M ASOCIADOS | C.I. 1.008.110-0 | Domicilio: Curupayty Esq. Farid Rahal", ln=True)
    pdf.cell(0, 5, f"ARRENDATARIO: {datos['cliente']} | Doc: {datos['doc']} | Tel: {datos['tel']}", ln=True)
    pdf.ln(2)

    pdf.set_font("Times", '', 8.5)
    texto_contrato = f"""
    PRIMERA- Objeto: Alquiler de vehículo Marca: {datos['auto']}, Modelo: {datos['sub_modelo']}, Año: {datos['ano']}, Color: {datos['color']}, Chasis: {datos['chasis']}, Chapa: {datos['chapa']}. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR.
    SEGUNDA- Duración: El contrato tendrá una duración de {datos['dias']} días, desde {datos['f1']} hasta {datos['f2']}.
    TERCERA- Precio: {datos['p_brl']} Reales por día. Total: R$ {datos['t_brl']} (Aprox Gs. {datos['t_pyg']:,.0f}). Pago por adelantado.
    CUARTA- Depósito: El arrendatario pagará Gs. 5.000.000 en caso de siniestro para cubrir daños.
    QUINTA- Condiciones de Uso: 1. Uso personal. 2. Arrendatario responsable PENAL y CIVIL. 3. Prohibido subarrendar. 4. Salida del país requiere aprobación.
    SEXTA- Kilometraje: Incluye kilómetros libres por Paraguay, Brasil y Argentina.
    SÉPTIMA- Seguro: Cobertura Civil, accidentes y rastreo satelital. Daños por negligencia a cargo del arrendatario.
    OCTAVA- Mantenimiento: Arrendatario responsable de agua, combustible y limpieza.
    NOVENA- Devolución: En las mismas condiciones. Penalización por demora: media diaria o diaria completa.
    DÉCIMA- Incumplimiento: Rescisión inmediata y reclamo de daños.
    UNDÉCIMA- Jurisdicción: Tribunales del Alto Paraná, Paraguay.
    DÉCIMA SEGUNDA- Firma: Ambas partes firman en señal de conformidad.
    """
    pdf.multi_cell(0, 4, texto_contrato)
    
    if firma_img:
        pdf.ln(5)
        pdf.image(firma_img, x=130, w=40)
        pdf.cell(0, 5, "_______________________", ln=True, align='R')
        pdf.cell(0, 5, "Firma del Arrendatario", ln=True, align='R')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. APP ---
init_db()
aplicar_estilos_jm()

if 'user' not in st.session_state:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>🔑 ACCESO JM</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Usuario (Correo/Tel)")
        p = st.text_input("Contraseña", type="password")
        d = st.text_input("Documento (CI/CPF/RG)")
        t = st.text_input("WhatsApp")
        if st.button("ENTRAR AL SISTEMA"):
            st.session_state.user = u
            st.session_state.doc = d
            st.session_state.tel = t
            st.session_state.is_admin = (u == "admin")
            st.rerun()
else:
    st.markdown("<div class='header-jm'><h1>JM ASOCIADOS</h1><p>Alquiler de Vehículos</p></div>", unsafe_allow_html=True)
    
    # TABS PARA TODOS LOS USUARIOS (Contacto es visible para todos ahora)
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "📞 Contacto", "🛡️ Panel Admin" if st.session_state.is_admin else ""])

    with tabs[0]: # CATÁLOGO
        conn = sqlite3.connect('jm_final_safe.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df.iterrows():
            if r['estado'] == "Disponible":
                with st.container():
                    st.markdown(f"""<div class='card-auto'>
                        <img src='{r['img']}' width='150' style='float:right; border-radius:10px;'>
                        <h2>{r['nombre']}</h2>
                        <b style='color:#800000;'>R$ {r['precio_brl']} por día</b><br>
                        <small>Chapa: {r['chapa']} | Chasis: {r['chasis']}</small>
                    </div>""", unsafe_allow_html=True)
                    
                    with st.expander("RESERVAR Y FIRMAR CONTRATO"):
                        f1 = st.date_input("Inicio", key=f"f1{i}")
                        f2 = st.date_input("Fin", key=f"f2{i}")
                        dias = (f2 - f1).days if (f2 - f1).days > 0 else 1
                        total_brl = dias * r['precio_brl']
                        
                        st.write("### Firma Digital del Arrendatario")
                        canvas_res = st_canvas(fill_color="white", stroke_width=2, stroke_color="black", background_color="white", height=100, key=f"canv{i}")

                        if st.button("GENERAR Y PREVISUALIZAR", key=f"btn{i}"):
                            # Procesar firma
                            firma_p = f"f_{i}.png"
                            Image.fromarray(canvas_res.image_data.astype('uint8'), 'RGBA').save(firma_p)
                            
                            datos = {
                                'cliente': st.session_state.user, 'doc': st.session_state.doc, 'tel': st.session_state.tel,
                                'auto': r['nombre'], 'sub_modelo': r['modelo'], 'ano': r['ano'], 'color': r['color'],
                                'chasis': r['chasis'], 'chapa': r['chapa'], 'f1': f1, 'f2': f2, 'dias': dias,
                                'p_brl': r['precio_brl'], 't_brl': total_brl, 't_pyg': total_brl * 1450
                            }
                            st.session_state.pdf_master = generar_contrato_oficial(datos, firma_p)
                            
                            # MENSAJE PARA WHATSAPP
                            msg = f"Hola JM ASOCIADOS, soy {st.session_state.user}. Acabo de reservar el {r['nombre']} por {dias} días. Monto: R$ {total_brl}. Adjunto mi contrato."
                            st.session_state.wa_link = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.rerun()

        if 'pdf_master' in st.session_state:
            st.divider()
            st.markdown("### 📄 VISTA PREVIA Y ENVÍO")
            b64 = base64.b64encode(st.session_state.pdf_master).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500"></iframe>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR PDF", st.session_state.pdf_master, "Contrato_JM.pdf")
            c2.markdown(f'<a href="{st.session_state.wa_link}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:10px;">📲 ENVIAR A WHATSAPP EMPRESARIAL</button></a>', unsafe_allow_html=True)

    with tabs[2]: # CONTACTO
        st.markdown("### 📞 CONTACTO DIRECTO")
        st.write("📍 Av. Curupayty Esq. Farid Rahal, Edif. Arami. Ciudad del Este.")
        st.markdown("[📸 Instagram](https://www.instagram.com/jm_asociados_consultoria)")
        st.markdown("[📍 Ubicación Google Maps](https://share.google/00OZ2MIrc78mmI2Vy)")

    if st.session_state.is_admin:
        with tabs[3]: # ADMIN
            st.subheader("🛡️ PANEL ADMINISTRATIVO")
            for i, r in df.iterrows():
                col1, col2 = st.columns([3,1])
                st_nuevo = col2.selectbox(f"{r['nombre']}", ["Disponible", "En Taller"], index=0 if r['estado']=="Disponible" else 1, key=f"adm{i}")
                if st_nuevo != r['estado']:
                    conn = sqlite3.connect('jm_final_safe.db')
                    conn.execute("UPDATE flota SET estado=? WHERE id=?", (st_nuevo, r['id']))
                    conn.commit()
                    st.rerun()
