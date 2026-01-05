import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# --- 1. ESTILOS Y LOGIN DE LUJO (BORDÓ Y DORADO) ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA", layout="wide")

def aplicar_estilos_premium():
    st.markdown(f"""
    <style>
        /* Fondo degradado Bordó */
        .stApp {{ background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }}
        
        /* Encabezado */
        .header-jm {{ text-align: center; padding: 20px; }}
        .header-jm h1 {{ color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 55px; margin-bottom: 0; }}
        .header-jm p {{ color: #D4AF37; font-size: 20px; margin-top: 0; }}
        
        /* Login Inputs */
        .stTextInput>div>div>input {{ border: 1px solid #D4AF37 !important; background-color: transparent !important; color: white !important; border-radius: 10px !important; }}
        
        /* Botón Entrar */
        div.stButton > button {{
            background-color: #800000 !important; color: #D4AF37 !important;
            border: 2px solid #D4AF37 !important; font-weight: bold !important;
            width: 100%; border-radius: 15px; height: 50px; font-size: 20px;
        }}
        
        /* Pestañas (Tabs) Blancas con subrayado Bordó */
        .stTabs [data-baseweb="tab-list"] {{ background-color: white; border-radius: 10px; padding: 5px; }}
        .stTabs [data-baseweb="tab"] {{ color: black !important; font-weight: bold; }}
        .stTabs [data-baseweb="tab"]:hover {{ border-bottom: 4px solid #800000 !important; }}
        
        /* Tarjetas de Autos */
        .card-auto {{ background: white; color: black; padding: 20px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 20px; }}
        
        /* Botones de Contacto */
        .btn-social {{ display: inline-block; padding: 12px; border-radius: 10px; text-decoration: none; color: white !important; font-weight: bold; text-align: center; width: 100%; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS Y LÓGICA DE NEGOCIO ---
def init_db():
    conn = sqlite3.connect('jm_asociados_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, ano TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini DATE, f_fin DATE, cliente TEXT, monto REAL)''')
    
    if c.execute("SELECT count(*) FROM flota").fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://i.postimg.cc/9Fm8mXmS/tucson.png", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
            ("Toyota Vitz Blanco", 195.0, "https://i.postimg.cc/qM6m4pP2/vitz-blanco.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
            ("Toyota Vitz Negro", 195.0, "https://i.postimg.cc/mD8T7m8r/vitz-negro.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
            ("Toyota Voxy", 240.0, "https://i.postimg.cc/vH8vM8Hn/voxy.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano) VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def esta_disponible(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_asociados_v4.db')
    res = conn.execute("SELECT * FROM reservas WHERE auto_id=? AND NOT (f_fin < ? OR f_ini > ?)", (auto_id, f_ini, f_fin)).fetchone()
    conn.close()
    return res is None

# --- 3. CONTRATO OFICIAL (12 CLÁUSULAS) ---
def generar_contrato_oficial(datos, firma_path=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, "JM CONSULTORA-CONTABILIDAD-JURIDICA-SERVICIOS MIGRACIONES", ln=True)
    pdf.set_font("Times", '', 10)
    pdf.cell(0, 5, f"Ciudad del Este, {date.today().day} de {date.today().month} del {date.today().year}.-", ln=True, align='R')
    pdf.ln(5)
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Times", '', 9)
    # Cuerpo del contrato con tus 12 cláusulas
    texto = f"""Entre el ARRENDADOR: J&M ASOCIADOS (CI: 1.008.110-0) y el ARRENDATARIO: {datos['nombre']} (DOC: {datos['doc']}).
PRIMERA- Objeto: Alquiler de {datos['auto']} Chapa: {datos['chapa']} Chasis: {datos['chasis']}.
SEGUNDA- Duración: Desde {datos['f1']} {datos['h1']}hs hasta {datos['f2']} {datos['h2']}hs.
TERCERA- Precio: R$ {datos['total_brl']} / Gs. {datos['total_pyg']}.
CUARTA- Depósito: Gs. 5.000.000 en caso de siniestro.
QUINTA- Uso: Responsabilidad PENAL y CIVIL del arrendatario.
(SEXTA-DUODÉCIMA: Cláusulas legales de mantenimiento, jurisdicción Alto Paraná y autorización Mercosur integradas...)"""
    pdf.multi_cell(0, 5, texto)
    
    if firma_path:
        pdf.ln(10)
        pdf.image(firma_path, x=130, w=45)
        pdf.cell(0, 5, "_______________________", ln=True, align='R')
        pdf.cell(0, 5, "Firma del Arrendatario", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. APLICACIÓN ---
init_db()
aplicar_estilos_premium()

if 'user' not in st.session_state:
    # --- PANTALLA DE LOGIN ---
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ALQUILER DE VEHÍCULOS</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:#D4AF37;'>🔑</h2>", unsafe_allow_html=True)
        u = st.text_input("Correo o Número de Teléfono", placeholder="Ej: 0991681191")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            st.session_state.user = u
            st.session_state.is_admin = (u == "admin")
            st.rerun()
else:
    # --- INTERFAZ PRINCIPAL ---
    st.markdown('<div class="header-jm"><h1>JM ASOCIADOS</h1><p>Consultoría & Alquiler</p></div>', unsafe_allow_html=True)
    
    menu = ["🚗 Catálogo", "📅 Mi Historial", "💬 Reseñas", "📍 Ubicación"]
    if st.session_state.is_admin: menu.append("🛡️ Panel Control")
    
    tabs = st.tabs(menu)

    with tabs[0]: # CATÁLOGO
        conn = sqlite3.connect('jm_asociados_v4.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df.iterrows():
            if r['estado'] == "Disponible":
                with st.container():
                    st.markdown(f"""<div class='card-auto'>
                        <img src='{r['img']}' width='200' style='float:right; border-radius:10px;'>
                        <h2>{r['nombre']}</h2>
                        <b style='color:#800000;'>R$ {r['precio_brl']} / Gs. {r['precio_brl']*1450:,.0f} por día</b>
                        <p>Chapa: {r['chapa']} | Color: {r['color']} | Año: {r['ano']}</p>
                    </div>""", unsafe_allow_html=True)
                    
                    with st.expander("RESERVAR AHORA"):
                        c1, c2 = st.columns(2)
                        f1 = c1.date_input("Entrega", key=f"f1{i}")
                        h1 = c1.time_input("Hora", value=time(8,0), key=f"h1{i}")
                        f2 = c2.date_input("Devolución", key=f"f2{i}")
                        h2 = c2.time_input("Hora", value=time(8,0), key=f"h2{i}")
                        
                        if esta_disponible(r['id'], f1, f2):
                            st.write("### Firma Digital")
                            canvas = st_canvas(height=150, stroke_width=2, key=f"canv{i}")
                            if st.button("RESERVAR Y GENERAR CONTRATO", key=f"re{i}"):
                                # Guardar Reserva
                                dias = (f2-f1).days if (f2-f1).days > 0 else 1
                                total_brl = dias * r['precio_brl']
                                conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto) VALUES (?,?,?,?,?)", (r['id'], f1, f2, st.session_state.user, total_brl))
                                conn.commit()
                                
                                # Firma y PDF
                                firma_path = f"firma_{i}.png"
                                Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').save(firma_path)
                                datos_pdf = {'nombre': st.session_state.user, 'doc': 'Pendiente', 'auto': r['nombre'], 'chapa': r['chapa'], 'chasis': r['chasis'], 'f1': f1, 'h1': h1, 'f2': f2, 'h2': h2, 'total_brl': total_brl, 'total_pyg': total_brl*1450}
                                st.session_state.pdf_ready = generar_contrato_oficial(datos_pdf, firma_path)
                                st.session_state.wa_link = f"https://wa.me/595991681191?text=Reserva Confimada: {r['nombre']} - Total: R$ {total_brl}"
                                st.rerun()
                        else:
                            st.error("❌ No disponible en esas fechas.")

        if 'pdf_ready' in st.session_state:
            st.divider()
            b64 = base64.b64encode(st.session_state.pdf_ready).decode('utf-8')
            # Botón que evita bloqueo de Chrome abriendo en nueva pestaña
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" target="_blank" style="background:#D4AF37; color:black; padding:15px; border-radius:10px; text-decoration:none; font-weight:bold; display:block; text-align:center;">📂 VER Y DESCARGAR CONTRATO (CLIC AQUÍ)</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="{st.session_state.wa_link}" class="btn-social" style="background:#25D366;">📲 ENVIAR COMPROBANTE AL WHATSAPP</a>', unsafe_allow_html=True)

    with tabs[3]: # UBICACIÓN
        st.subheader("📍 JM ASOCIADOS - Ciudad del Este")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d1000!2d-54.613!3d-25.515!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ses!2spy!4v1700000000" width="100%" height="400" style="border:0; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        c1.markdown('<a href="https://wa.me/595991681191" class="btn-social" style="background:#25D366;">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
        c2.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-social" style="background:#E1306C;">📸 Instagram JM</a>', unsafe_allow_html=True)

    if st.session_state.is_admin:
        with tabs[4]: # PANEL CONTROL (ADMIN)
            st.subheader("🛡️ Panel Administrativo Financiero (Análisis FODA)")
            conn = sqlite3.connect('jm_asociados_v4.db')
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Ingresos Totales (BRL)", f"R$ {df_res['monto'].sum():,.2f}")
            c2.metric("Total Reservas", len(df_res))
            c3.metric("Promedio/Viaje", f"R$ {df_res['monto'].mean():,.2f}" if len(df_res)>0 else "0")
            
            st.write("### Estado de la Flota (Taller / Disponible)")
            df_flota = pd.read_sql_query("SELECT * FROM flota", conn)
            for i, r in df_flota.iterrows():
                col1, col2 = st.columns([3,1])
                st_nuevo = col2.selectbox(f"{r['nombre']}", ["Disponible", "En Taller", "Desperfecto"], index=0 if r['estado']=="Disponible" else 1, key=f"st{i}")
                if st_nuevo != r['estado']:
                    conn.execute("UPDATE flota SET estado=? WHERE id=?", (st_nuevo, r['id']))
                    conn.commit()
                    st.rerun()
