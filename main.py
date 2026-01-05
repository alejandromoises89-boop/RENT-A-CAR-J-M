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

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA FINAL", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 10px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 50px; margin-bottom: 0; }
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: rgba(255,255,255,0.05) !important; color: white !important; }
        div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; border-radius: 12px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .card-auto { background: white; color: black; padding: 15px; border-radius: 15px; border-left: 10px solid #D4AF37; margin-bottom: 20px; }
        .resena-card { background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 3px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_final_v10.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, nombre TEXT, precio_brl REAL, img TEXT, estado TEXT, chasis TEXT, chapa TEXT, color TEXT, ano TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, auto_id INTEGER, f_ini TEXT, f_fin TEXT, cliente TEXT, monto REAL, doc TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, password TEXT, nombre TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resenas (id INTEGER PRIMARY KEY, usuario TEXT, comentario TEXT, estrellas INTEGER)''')
    
    c.execute("SELECT count(*) FROM flota")
    if c.fetchone()[0] == 0:
        autos = [
            ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible", "TUC-7721", "AA-123", "Gris", "2012"),
            ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "VTZ-001", "BCC-445", "Blanco", "2010"),
            ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible", "VTZ-998", "XAM-990", "Negro", "2011"),
            ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible", "VOX-556", "HHP-112", "Perla", "2009")
        ]
        c.executemany("INSERT INTO flota (nombre, precio_brl, img, estado, chasis, chapa, color, ano) VALUES (?,?,?,?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def verificar_bloqueo(auto_id, f_ini, f_fin):
    conn = sqlite3.connect('jm_final_v10.db')
    res = conn.execute("SELECT * FROM reservas WHERE auto_id = ? AND NOT (f_fin < ? OR f_ini > ?)", (auto_id, str(f_ini), str(f_fin))).fetchone()
    conn.close()
    return res is None

def generar_pdf(d, firma_img=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, "CONTRATO DE ALQUILER - JM ASOCIADOS", ln=True, align='C')
    pdf.set_font("Times", '', 10)
    pdf.ln(5)
    clausulas = f"""Este contrato certifica que el cliente {d['nombre']} (Doc: {d['doc']}) alquila el {d['auto']} (Chapa: {d['chapa']}) 
desde el {d['f1']} hasta el {d['f2']}.

12 CLÁUSULAS LEGALES:
1. Uso exclusivo MERCOSUR. 2. Responsabilidad Civil y Penal del cliente. 3. Depósito de Gs. 5.000.000.
(Contrato foliado bajo registros de JM Consultora)..."""
    pdf.multi_cell(0, 6, clausulas)
    if firma_img:
        firma_img.save("temp_f.png")
        pdf.image("temp_f.png", x=140, y=pdf.get_y()+5, w=40)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. LOGIN ---
init_db()
aplicar_estilos_premium()

if 'logged' not in st.session_state: st.session_state.logged = False

if not st.session_state.logged:
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO JM ASOCIADOS</p></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["ENTRAR", "REGISTRO", "SOPORTE"])
    with t1:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "1234":
                st.session_state.logged, st.session_state.role, st.session_state.name = True, "admin", "Administrador"
                st.rerun()
            else:
                conn = sqlite3.connect('jm_final_v10.db')
                r = conn.execute("SELECT nombre FROM usuarios WHERE user=? AND password=?", (u, p)).fetchone()
                if r:
                    st.session_state.logged, st.session_state.role, st.session_state.name = True, "user", r[0]
                    st.rerun()
                else: st.error("Datos incorrectos")
    with t2:
        nu, nn, np = st.text_input("Celular"), st.text_input("Nombre"), st.text_input("Clave", type="password")
        if st.button("REGISTRAR"):
            conn = sqlite3.connect('jm_final_v10.db')
            conn.execute("INSERT INTO usuarios VALUES (?,?,?)", (nu, np, nn))
            conn.commit()
            st.success("Registrado correctamente.")
    with t3: st.info("Escriba a soporte: +595 991 681191")

else:
    # --- APP PRINCIPAL ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.name}**")
        if st.button("SALIR"):
            st.session_state.logged = False
            st.rerun()

    tabs = st.tabs(["🚗 Catálogo", "⭐ Reseñas", "📍 Ubicación", "🛡️ Admin" if st.session_state.role == "admin" else "📲 Contacto"])

    with tabs[0]: # CATALOGO
        conn = sqlite3.connect('jm_final_v10.db')
        df_a = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df_a.iterrows():
            with st.container():
                st.markdown(f"<div class='card-auto'><img src='{r['img']}' width='150' style='float:right;'><h3>{r['nombre']}</h3><p>R$ {r['precio_brl']} / Gs. {r['precio_brl']*1450:,.0f}</p></div>", unsafe_allow_html=True)
                with st.expander("RESERVAR"):
                    f1, f2 = st.date_input("Inicio", key=f"f1{i}"), st.date_input("Fin", key=f"f2{i}")
                    doc = st.text_input("CI/RG/CPF", key=f"d{i}")
                    if verificar_bloqueo(r['id'], f1, f2):
                        canvas = st_canvas(height=80, stroke_width=2, key=f"c{i}")
                        if st.button("GENERAR RESERVA Y CONTRATO", key=f"b{i}"):
                            total = max((f2-f1).days, 1) * r['precio_brl']
                            conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto, doc) VALUES (?,?,?,?,?,?)", (r['id'], str(f1), str(f2), st.session_state.name, total, doc))
                            conn.commit()
                            img_f = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                            pdf_b = generar_pdf({'nombre': st.session_state.name, 'doc': doc, 'auto': r['nombre'], 'chapa': r['chapa'], 'f1': f1, 'f2': f2}, img_f)
                            
                            st.success("Reserva lista. Siga los pasos:")
                            st.download_button("1. 📥 DESCARGAR CONTRATO (OBLIGATORIO)", pdf_b, "contrato.pdf")
                            
                            msg = urllib.parse.quote(f"Reserva: {r['nombre']} de {f1} a {f2}. Cliente: {st.session_state.name}.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={msg}" style="background:#25D366; color:white; padding:12px; display:block; text-align:center; border-radius:10px; text-decoration:none;">2. 📲 NOTIFICAR A WHATSAPP</a>', unsafe_allow_html=True)
                    else: st.error("No disponible")

    with tabs[1]: # RESEÑAS
        st.subheader("💬 Reseñas de Clientes")
        with st.form("f_res"):
            com = st.text_area("Tu comentario")
            est = st.slider("Estrellas", 1, 5, 5)
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_final_v10.db')
                conn.execute("INSERT INTO resenas (usuario, comentario, estrellas) VALUES (?,?,?)", (st.session_state.name, com, est))
                conn.commit()
        conn = sqlite3.connect('jm_final_v10.db')
        res_df = pd.read_sql_query("SELECT * FROM resenas ORDER BY id DESC", conn)
        for _, rw in res_df.iterrows():
            st.markdown(f"<div class='resena-card'><b>{rw['usuario']}</b> ({'⭐'*rw['estrellas']})<br>{rw['comentario']}</div>", unsafe_allow_html=True)

    with tabs[2]: # UBICACIÓN
        st.subheader("📍 Nuestra Ubicación")
        # Iframe con link directo de Embed Maps para que se vea siempre
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.4474776107873!2d-54.6139176!3d-25.5101662!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzM2LjYiUyA1NMKwMzYnNTAuMSJX!5e0!3m2!1ses!2spy!4v1625000000000!5m2!1ses!2spy" width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>', unsafe_allow_html=True)

    if st.session_state.role == "admin":
        with tabs[3]: # ADMIN
            pin = st.text_input("PIN", type="password")
            if pin == "1234":
                conn = sqlite3.connect('jm_final_v10.db')
                df_r = pd.read_sql_query("SELECT * FROM reservas", conn)
                st.metric("Total R$", f"{df_r['monto'].sum():,.2f}")
                st.dataframe(df_r)
                if st.button("LIMPIAR"):
                    conn.execute("DELETE FROM reservas")
                    conn.commit()
                    st.rerun()
    else:
        with tabs[3]: # CONTACTO USUARIO
            st.subheader("📲 Contacto Directo")
            st.markdown('<a href="https://wa.me/595991681191" style="background:#25D366; color:white; padding:15px; display:block; text-align:center; border-radius:10px; text-decoration:none;">💬 WhatsApp Corporativo</a>', unsafe_allow_html=True)
            st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" style="background:#E1306C; color:white; padding:15px; display:block; text-align:center; border-radius:10px; text-decoration:none; margin-top:10px;">📸 Instagram Oficial</a>', unsafe_allow_html=True)
