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

# --- 1. CONFIGURACIÓN Y ESTILOS PREMIUM ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA V9", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 10px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 55px; margin-bottom: 0; }
        .header-jm p { color: #D4AF37; font-size: 18px; font-style: italic; }
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: rgba(255,255,255,0.05) !important; color: white !important; border-radius: 10px !important; }
        div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; border-radius: 12px; height: 45px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .card-auto { background: white; color: black; padding: 15px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE BASE DE DATOS (CON LOS AUTOS CORRECTOS) ---
def init_db():
    conn = sqlite3.connect('jm_final_v9.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, ano TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini DATE, f_fin DATE, cliente TEXT, monto REAL, doc TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (user TEXT PRIMARY KEY, password TEXT, nombre TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, usuario TEXT, comentario TEXT, estrellas INTEGER)''')
    
    # Lista de autos actualizada según tu solicitud
    autos_correctos = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
    ]
    
    # Comprobar si los autos ya existen para no duplicar o dar error
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano) VALUES (?,?,?,?,?,?,?,?)", autos_correctos)
    
    conn.commit()
    conn.close()

def verificar_bloqueo(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_final_v9.db')
    query = "SELECT * FROM reservas WHERE auto_id = ? AND NOT (f_fin < ? OR f_ini > ?)"
    res = conn.execute(query, (auto_id, str(f_ini), str(f_fin))).fetchone()
    conn.close()
    return res is None

# --- 3. CONTRATO PDF (12 CLÁUSULAS) ---
def generar_contrato_pdf(d, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 5, "JM ASOCIADOS - CONTRATO DE ALQUILER", ln=True, align='C')
    pdf.set_font("Times", '', 8.5)
    pdf.ln(5)
    
    texto_contrato = f"""1. ARRENDADOR: JM Asociados. 2. ARRENDATARIO: {d['nombre']} con Doc: {d['doc']}.
3. OBJETO: Alquiler del vehículo {d['auto']}, Chapa {d['chapa']}.
4. PLAZO: Del {d['f1']} al {d['f2']}. 5. PRECIO: R$ {d['total']}.
6. DEPÓSITO: Gs. 5.000.000 en garantía. 7. USO: El vehículo debe ser usado bajo normas legales.
8. RESPONSABILIDAD: Civil y Penal a cargo del arrendatario. 9. MANTENIMIENTO: A cargo de la empresa.
10. DEVOLUCIÓN: En las mismas condiciones recibidas. 11. JURISDICCIÓN: Ciudad del Este.
12. AUTORIZACIÓN: Se autoriza la conducción en territorio Nacional y MERCOSUR."""
    
    pdf.multi_cell(0, 5, texto_contrato)
    
    if firma_img:
        firma_img.save("firma_temp.png")
        pdf.image("firma_temp.png", x=135, y=pdf.get_y()+5, w=45)
        pdf.ln(12)
        pdf.cell(0, 5, "_______________________", ln=True, align='R')
        pdf.cell(0, 5, "Firma del Arrendatario", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SISTEMA DE LOGIN Y FLUJO ---
init_db()
aplicar_estilos_premium()

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO AL SISTEMA</p></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["INICIAR SESIÓN", "CREAR CUENTA", "OLVIDÉ MI CLAVE"])
    
    with t1:
        u = st.text_input("Usuario (Teléfono)")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "1234":
                st.session_state.autenticado, st.session_state.role, st.session_state.name = True, "admin", "Administrador"
                st.rerun()
            else:
                conn = sqlite3.connect('jm_final_v9.db')
                res = conn.execute("SELECT nombre FROM usuarios WHERE user=? AND password=?", (u, p)).fetchone()
                if res:
                    st.session_state.autenticado, st.session_state.role, st.session_state.name = True, "user", res[0]
                    st.rerun()
                else: st.error("Usuario o contraseña incorrectos.")
    with t2:
        nu, nn, np = st.text_input("Número de Teléfono"), st.text_input("Nombre Completo"), st.text_input("Nueva Contraseña", type="password")
        if st.button("REGISTRARSE"):
            conn = sqlite3.connect('jm_final_v9.db')
            conn.execute("INSERT INTO usuarios VALUES (?,?,?)", (nu, np, nn))
            conn.commit()
            st.success("Cuenta creada exitosamente.")
    with t3:
        st.info("Contacte con soporte para recuperar su cuenta.")
        st.markdown('<a href="https://wa.me/595991681191" class="btn-social" style="color:#D4AF37;">📲 Soporte Técnico</a>', unsafe_allow_html=True)

else:
    # --- INTERFAZ PRINCIPAL ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.name}**")
        if st.button("CERRAR SESIÓN"):
            st.session_state.autenticado = False
            st.rerun()

    tabs = st.tabs(["🚗 Catálogo", "⭐ Reseñas", "📍 Ubicación", "🛡️ Admin" if st.session_state.role == "admin" else "📞 Ayuda"])

    with tabs[0]: # CATALOGO
        conn = sqlite3.connect('jm_final_v9.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df_a.iterrows():
            with st.container():
                st.markdown(f"<div class='card-auto'><img src='{r['img']}' width='180' style='float:right; border-radius:10px;'><h3>{r['nombre']}</h3><p><b>R$ {r['precio_brl']} / Gs. {r['precio_brl']*1450:,.0f} por día</b></p><p>Chapa: {r['chapa']} | Año: {r['ano']}</p></div>", unsafe_allow_html=True)
                with st.expander("RESERVAR VEHÍCULO"):
                    f1, f2 = st.date_input("Entrega", key=f"f1{i}"), st.date_input("Devolución", key=f"f2{i}")
                    doc = st.text_input("Número de Documento", key=f"d{i}")
                    if verificar_bloqueo(r['id'], f1, f2):
                        st.write("Firme aquí:")
                        canvas = st_canvas(height=100, stroke_width=2, key=f"c{i}")
                        if st.button("CONFIRMAR Y FIRMAR", key=f"b{i}"):
                            total = max((f2-f1).days, 1) * r['precio_brl']
                            conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto, doc) VALUES (?,?,?,?,?,?)", (r['id'], str(f1), str(f2), st.session_state.name, total, doc))
                            conn.commit()
                            img_firma = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                            pdf = generar_contrato_pdf({'nombre': st.session_state.name, 'doc': doc, 'auto': r['nombre'], 'chapa': r['chapa'], 'f1': f1, 'f2': f2, 'total': total}, img_firma)
                            st.download_button("📥 DESCARGAR CONTRATO", pdf, f"Contrato_{r['nombre']}.pdf")
                            
                            saludo = urllib.parse.quote(f"Hola JM ASOCIADOS, soy {st.session_state.name}. Reservé el {r['nombre']} del {f1} al {f2}. Monto: R$ {total}. Adjunto contrato.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={saludo}" style="background:#25D366; color:white; padding:10px; display:block; text-align:center; border-radius:10px; text-decoration:none;">📲 ENVIAR A WHATSAPP</a>', unsafe_allow_html=True)
                    else:
                        st.error("❌ No disponible en esas fechas.")

    with tabs[1]: # RESEÑAS
        st.subheader("💬 Deja tu comentario")
        # Aquí puedes añadir el código de reseñas previo...

    with tabs[2]: # UBICACIÓN
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.234!2d-54.61!3d-25.51" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[3]: # ADMIN
            pin = st.text_input("PIN Admin", type="password")
            if pin == "1234":
                conn = sqlite3.connect('jm_final_v9.db')
                df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
                st.metric("Total Ingresos", f"R$ {df_res['monto'].sum():,.2f}")
                st.dataframe(df_res)
