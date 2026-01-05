import streamlit as st
import sqlite3
import pandas as pd
import base64
import requests
from datetime import datetime, date
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas # Requiere: pip install streamlit-drawable-canvas
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INTERFAZ PREMIUM ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA DE GESTIÓN", layout="wide")

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

# --- 2. COTIZACIÓN EN LÍNEA ---
def get_exchange_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/BRL")
        return r.json()['rates']['PYG']
    except:
        return 1450.0 # Valor de respaldo

# --- 3. BASE DE DATOS Y DATOS TÉCNICOS ---
def init_db():
    conn = sqlite3.connect('jm_final_safe.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, 
                  chasis TEXT, chapa TEXT, color TEXT, ano TEXT, modelo TEXT)''')
    
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        # AQUÍ PUEDES EDITAR LOS DATOS DE CADA AUTO SIN DAÑAR NADA
        autos_data = [
            ("Hyundai Tucson", 260.0, "https://i.ibb.co/6R2M3S1/tucson.png", "Disponible", "TUC-993882771", "AA-123-ZZ", "Gris Plata", "2012", "Tucson GL"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VITZ-0012233", "BCC-445", "Blanco", "2010", "Vitz RS"),
            ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/MhZfC8D/vitznegro.png", "Disponible", "VITZ-9988776", "XAM-990", "Negro", "2011", "Vitz Style"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-5566778", "HHP-112", "Perla", "2009", "Voxy ZS")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano, modelo) VALUES (?,?,?,?,?,?,?,?,?)", autos_data)
    conn.commit()
    conn.close()

# --- 4. GENERADOR DE CONTRATO CON FIRMA ---
def generar_contrato_oficial(datos, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, "JM ASOCIADOS - CONSULTORA JURÍDICA & ALQUILER DE VEHÍCULOS", ln=True)
    pdf.set_font("Times", '', 9)
    pdf.cell(0, 5, f"Fecha de emisión: {date.today()}", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, f"ARRENDATARIO: {datos['cliente']} | DOC: {datos['doc']} | TEL: {datos['tel']}", ln=True)
    pdf.ln(5)

    # Bloque Automático de Datos del Vehículo
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 7, "DETALLES DEL VEHÍCULO", ln=True, fill=True)
    pdf.set_font("Times", '', 10)
    pdf.multi_cell(0, 6, f"""Marca/Modelo: {datos['auto']} - {datos['sub_modelo']} | Año: {datos['ano']}
Color: {datos['color']} | Chasis: {datos['chasis']} | Chapa: {datos['chapa']}""")
    
    # Bloque de Precios y Fechas
    pdf.ln(3)
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 7, "DURACIÓN Y COSTOS", ln=True, fill=True)
    pdf.set_font("Times", '', 10)
    pdf.multi_cell(0, 6, f"""Desde: {datos['f1']} hasta {datos['f2']}
Precio Diario: R$ {datos['p_brl']} | Total: R$ {datos['t_brl']}
Cambio del día: R$ 1 = {datos['t_pyg']/datos['t_brl']:.0f} Gs. | TOTAL EN GUARANÍES: {datos['t_pyg']:,.0f} Gs.""")

    # Cláusulas (Resumen de tu original)
    pdf.ln(5)
    pdf.set_font("Times", '', 9)
    pdf.multi_cell(0, 5, """PRIMERA: El vehículo se entrega en perfecto estado. SEGUNDA: El arrendatario es responsable Civil y Penalmente. TERCERA: Autorización para conducir en Mercosur. CUARTA: Depósito de seguridad Gs. 5.000.000.""")
    
    # Insertar Firma Digital si existe
    if firma_img is not None:
        pdf.ln(10)
        pdf.image(firma_img, x=130, w=50)
        pdf.cell(0, 5, "_______________________", ln=True, align='R')
        pdf.cell(0, 5, "Firma del Arrendatario", ln=True, align='R')

    return pdf.output(dest='S').encode('latin-1')

# --- 5. APP PRINCIPAL ---
init_db()
aplicar_estilos_jm()
cambio_pyg = get_exchange_rate()

if 'user' not in st.session_state:
    # LOGIN ESTILO JM
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>🔐 JM ASOCIADOS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Usuario (Correo/Tel)")
        p = st.text_input("Contraseña", type="password")
        d = st.text_input("Documento (CI/CPF/RG)")
        t = st.text_input("WhatsApp")
        if st.button("ENTRAR"):
            st.session_state.user = u
            st.session_state.doc = d
            st.session_state.tel = t
            st.session_state.is_admin = (u == "admin")
            st.rerun()
else:
    st.markdown("<div class='header-jm'><h1>JM ASOCIADOS</h1><p>Consultoría & Alquiler de Autos</p></div>", unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Catálogo", "🛡️ Admin", "📍 Contacto"])

    with tabs[0]:
        conn = sqlite3.connect('jm_final_safe.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df.iterrows():
            if r['estado'] == "Disponible" or st.session_state.is_admin:
                with st.container():
                    st.markdown(f"""<div class='card-auto'>
                        <img src='{r['img']}' width='150' style='float:right;'>
                        <h2 style='margin:0;'>{r['nombre']}</h2>
                        <b style='color:#800000;'>R$ {r['precio_brl']} / Gs. {r['precio_brl']*cambio_pyg:,.0f} por día</b><br>
                        <small>Chapa: {r['chapa']} | Color: {r['color']} | Año: {r['ano']}</small>
                    </div>""", unsafe_allow_html=True)
                    
                    if r['estado'] == "Disponible":
                        with st.expander("ALQUILAR ESTE VEHÍCULO"):
                            c1, c2 = st.columns(2)
                            f1 = c1.date_input("Inicio", key=f"f1{i}")
                            f2 = c2.date_input("Fin", key=f"f2{i}")
                            dias = (f2 - f1).days if (f2 - f1).days > 0 else 1
                            
                            st.markdown(f"**Total a pagar:** R$ {dias * r['precio_brl']} / Gs. {dias * r['precio_brl'] * cambio_pyg:,.0f}")
                            
                            st.write("### FIRMA DIGITAL (Dibuje su firma abajo)")
                            canvas_result = st_canvas(
                                fill_color="rgba(255, 255, 255, 0.3)",
                                stroke_width=2,
                                stroke_color="#000000",
                                background_color="#FFFFFF",
                                height=150,
                                key=f"canvas_{i}",
                            )

                            if st.button("GENERAR CONTRATO FIRMADO", key=f"btn{i}"):
                                if canvas_result.image_data is not None:
                                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                                    firma_path = f"firma_{i}.png"
                                    img.save(firma_path)
                                    
                                    datos_finales = {
                                        'cliente': st.session_state.user, 'doc': st.session_state.doc, 'tel': st.session_state.tel,
                                        'auto': r['nombre'], 'sub_modelo': r['modelo'], 'ano': r['ano'], 'color': r['color'],
                                        'chasis': r['chasis'], 'chapa': r['chapa'], 'f1': f1, 'f2': f2,
                                        'p_brl': r['precio_brl'], 't_brl': dias * r['precio_brl'], 't_pyg': dias * r['precio_brl'] * cambio_pyg
                                    }
                                    st.session_state.pdf_master = generar_contrato_oficial(datos_finales, firma_path)
                                    st.success("Contrato generado con éxito.")

        if 'pdf_master' in st.session_state:
            st.divider()
            b64 = base64.b64encode(st.session_state.pdf_master).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
            st.download_button("📥 DESCARGAR CONTRATO OFICIAL", st.session_state.pdf_master, "Contrato_JM.pdf")

    if st.session_state.is_admin:
        with tabs[1]:
            st.subheader("🛡️ Panel de Control de Taller")
            for i, r in df.iterrows():
                col1, col2 = st.columns([3,1])
                nuevo_st = col2.selectbox(f"{r['nombre']}", ["Disponible", "En Taller"], index=0 if r['estado']=="Disponible" else 1, key=f"adm{i}")
                if nuevo_st != r['estado']:
                    conn = sqlite3.connect('jm_final_safe.db')
                    conn.execute("UPDATE flota SET estado=? WHERE id=?", (nuevo_st, r['id']))
                    conn.commit()
                    st.rerun()
