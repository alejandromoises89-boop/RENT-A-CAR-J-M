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

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 15px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 50px; margin-bottom: 0; }
        .header-jm p { color: #D4AF37; font-size: 18px; margin-top: 0; }
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: transparent !important; color: white !important; }
        div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold !important; width: 100%; border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .card-auto { background: white; color: black; padding: 15px; border-radius: 15px; border-left: 8px solid #D4AF37; margin-bottom: 15px; }
        .btn-social { display: inline-block; padding: 10px; border-radius: 8px; text-decoration: none; color: white !important; font-weight: bold; text-align: center; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, ano TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini DATE, f_fin DATE, cliente TEXT, monto REAL, doc TEXT)''')
    if c.execute("SELECT count(*) FROM flota").fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
            ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano) VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

# --- 3. GENERADOR DE CONTRATO CON TODAS LAS CLÁUSULAS ---
def generar_pdf_jm(d, firma=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, "JM CONSULTORA-CONTABILIDAD-JURIDICA-SERVICIOS MIGRACIONES", ln=True)
    pdf.set_font("Times", '', 9)
    pdf.cell(0, 5, f"Ciudad del Este, {date.today().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(5)
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 7, "CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR", ln=True, align='C')
    pdf.ln(4)
    
    pdf.set_font("Times", '', 8.5)
    clausulas = f"""ARRENDADOR: J&M ASOCIADOS (RUC 1.008.110-0). ARRENDATARIO: {d['nombre']} (Doc: {d['doc']}).
VEHÍCULO: {d['auto']} | Chapa: {d['chapa']} | Chasis: {d['chasis']} | Color: {d['color']} | Año: {d['ano']}
PRIMERA- Objeto: El vehículo se entrega en perfecto estado de funcionamiento comprobado por video técnico.
SEGUNDA- Duración: Desde {d['f1']} ({d['h1']}) hasta {d['f2']} ({d['h2']}).
TERCERA- Precio: R$ {d['total']} / Gs. {d['total']*1450:,.0f} pagados por adelantado.
CUARTA- Depósito: Gs. 5.000.000 en caso de siniestro (accidente).
QUINTA- Uso: Responsabilidad PENAL y CIVIL total del arrendatario. Prohibido subarrendar.
SEXTA- Kilometraje: Kilómetros libres en Paraguay, Brasil y Argentina (MERCOSUR).
SÉPTIMA- Seguro: Responsabilidad civil y rastreo satelital activo. Negligencia no cubierta.
OCTAVA- Mantenimiento: El arrendatario cuida agua, combustible y limpieza.
NOVENA- Devolución: En mismas condiciones. Penalidad: Media diaria por retraso.
DÉCIMA- Incumplimiento: Rescisión inmediata.
UNDÉCIMA- Jurisdicción: Tribunales del Alto Paraná, Paraguay.
DÉCIMA SEGUNDA- Firma: Se autoriza la conducción en todo el territorio Nacional y MERCOSUR."""
    
    pdf.multi_cell(0, 4.5, clausulas)
    if firma:
        pdf.image(firma, x=135, y=pdf.get_y()+5, w=45)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. APP ---
init_db()
aplicar_estilos_premium()

if 'user' not in st.session_state:
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO AL SISTEMA</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Correo o Teléfono")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            st.session_state.user, st.session_state.is_admin = u, (u == "admin")
            st.rerun()
        st.markdown("<p style='text-align:center; font-size:12px;'>Crear Cuenta | Olvidé mi contraseña</p>", unsafe_allow_html=True)
else:
    with st.sidebar:
        st.title("JM ASOCIADOS")
        if st.button("CERRAR SESIÓN"):
            del st.session_state['user']
            st.rerun()

    tabs = st.tabs(["🚗 Catálogo", "📍 Ubicación", "🛡️ Panel Control" if st.session_state.is_admin else "📞 Contacto"])

    with tabs[0]: # CATALOGO
        conn = sqlite3.connect('jm_final_v6.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df.iterrows():
            if r['estado'] == "Disponible":
                with st.container():
                    st.markdown(f"<div class='card-auto'><img src='{r['img']}' width='150' style='float:right;'><h3>{r['nombre']}</h3><p><b>R$ {r['precio_brl']} / Gs. {r['precio_brl']*1450:,.0f} p/ día</b></p></div>", unsafe_allow_html=True)
                    with st.expander("RESERVAR"):
                        f1, h1 = st.date_input("Entrega", key=f"f1{i}"), st.time_input("Hora", value=time(8,0), key=f"h1{i}")
                        f2, h2 = st.date_input("Devolución", key=f"f2{i}"), st.time_input("Hora", value=time(8,0), key=f"h2{i}")
                        doc_u = st.text_input("Documento (CI/RG/CPF)", key=f"doc{i}")
                        canvas = st_canvas(height=100, stroke_width=2, key=f"c{i}")
                        if st.button("CONFIRMAR RESERVA", key=f"b{i}"):
                            dias = max((f2-f1).days, 1)
                            total = dias * r['precio_brl']
                            conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto, doc) VALUES (?,?,?,?,?,?)", (r['id'], f1, f2, st.session_state.user, total, doc_u))
                            conn.commit()
                            firma_p = f"f_{i}.png"
                            Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').save(firma_p)
                            d_pdf = {'nombre': st.session_state.user, 'doc': doc_u, 'auto': r['nombre'], 'chapa': r['chapa'], 'chasis': r['chasis'], 'color': r['color'], 'ano': r['ano'], 'f1': f1, 'h1': h1, 'f2': f2, 'h2': h2, 'total': total}
                            st.session_state.pdf_master = generar_pdf_jm(d_pdf, firma_p)
                            msg = f"Estimados JM ASOCIADOS, un cordial saludo. Mi nombre es {st.session_state.user} (Doc: {doc_u}). Reservé el {r['nombre']} del {f1} al {f2}. Total: R$ {total}. Adjunto contrato y comprobante."
                            st.session_state.wa_link = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.rerun()

        if 'pdf_master' in st.session_state:
            st.download_button("📥 DESCARGAR CONTRATO (PDF)", st.session_state.pdf_master, "Contrato_JM.pdf", "application/pdf")
            st.markdown(f'<a href="{st.session_state.wa_link}" class="btn-social" style="background:#25D366;">📲 ENVIAR A WHATSAPP EMPRESA</a>', unsafe_allow_html=True)

    with tabs[1]: # UBICACIÓN CORREGIDA
        st.subheader("📍 Ubicación Corporativa")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3600.8654157545!2d-54.611111!3d-25.511111!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQwLjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1630000000000" width="100%" height="400" style="border:0; border-radius:15px;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)
        col_wa, col_ig = st.columns(2)
        col_wa.markdown('<a href="https://wa.me/595991681191" class="btn-social" style="background:#25D366;">💬 WhatsApp</a>', unsafe_allow_html=True)
        col_ig.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-social" style="background:#E1306C;">📸 Instagram</a>', unsafe_allow_html=True)

    if st.session_state.is_admin:
        with tabs[2]: # ADMIN CON PIN
            st.subheader("🛡️ Finanzas y Control de Flota")
            pin = st.text_input("Ingrese PIN de Seguridad para Finanzas", type="password")
            if pin == "1234":
                conn = sqlite3.connect('jm_final_v6.db')
                df_r = pd.read_sql_query("SELECT * FROM reservas", conn)
                st.metric("INGRESOS TOTALES", f"R$ {df_r['monto'].sum():,.2f}")
                st.dataframe(df_r)
                if st.button("🗑️ BORRAR TODAS LAS RESERVAS"):
                    conn.execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()
                st.write("---")
                st.write("**Disponibilidad de Flota:**")
                df_f = pd.read_sql_query("SELECT * FROM flota", conn)
                for i, r in df_f.iterrows():
                    col1, col2 = st.columns([3,1])
                    nuevo = col2.selectbox(f"{r['nombre']}", ["Disponible", "En Taller", "Desperfecto"], index=0 if r['estado']=="Disponible" else 1, key=f"st{i}")
                    if nuevo != r['estado']:
                        conn.execute("UPDATE flota SET estado=? WHERE id=?", (nuevo, r['id']))
                        conn.commit()
                        st.rerun()
            else:
                st.warning("PIN incorrecto para ver finanzas.")
