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

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA", layout="wide")

def aplicar_estilos_premium():
    st.markdown(f"""
    <style>
        .stApp {{ background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }}
        .header-jm {{ text-align: center; padding: 10px; }}
        .header-jm h1 {{ color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 50px; margin-bottom: 0; }}
        .header-jm p {{ color: #D4AF37; font-size: 18px; margin-top: 0; }}
        
        /* Estilo de Inputs */
        .stTextInput>div>div>input {{ border: 1px solid #D4AF37 !important; background-color: transparent !important; color: white !important; }}
        
        /* Botones Dorados */
        div.stButton > button {{
            background-color: #800000 !important; color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important; font-weight: bold !important;
            width: 100%; border-radius: 10px;
        }}
        
        /* Tabs Blancos */
        .stTabs [data-baseweb="tab-list"] {{ background-color: white; border-radius: 10px; padding: 5px; }}
        .stTabs [data-baseweb="tab"] {{ color: black !important; font-weight: bold; }}
        
        /* Tarjetas */
        .card-auto {{ background: white; color: black; padding: 15px; border-radius: 15px; border-left: 8px solid #D4AF37; margin-bottom: 15px; }}
        .btn-social {{ display: inline-block; padding: 10px; border-radius: 8px; text-decoration: none; color: white !important; font-weight: bold; text-align: center; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados_final.db')
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
    conn = sqlite3.connect('jm_asociados_final.db')
    res = conn.execute("SELECT * FROM reservas WHERE auto_id=? AND NOT (f_fin < ? OR f_ini > ?)", (auto_id, f_ini, f_fin)).fetchone()
    conn.close()
    return res is None

# --- 3. CONTRATO PDF ---
def generar_contrato_oficial(datos, firma_path=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 10, "JM ASOCIADOS - CONTRATO DE ALQUILER", ln=True, align='C')
    pdf.set_font("Times", '', 10)
    
    cuerpo = f"""
    ARRENDATARIO: {datos['nombre']} | DOC: {datos['doc']}
    VEHICULO: {datos['auto']} | CHAPA: {datos['chapa']} | CHASIS: {datos['chasis']}
    PERIODO: Desde {datos['f1']} ({datos['h1']}) hasta {datos['f2']} ({datos['h2']})
    MONTO TOTAL: R$ {datos['total_brl']} / Gs. {datos['total_pyg']:,.0f}
    
    CLÁUSULAS:
    1. El vehículo se entrega en óptimas condiciones.
    2. El arrendatario es responsable penal y civilmente.
    3. Uso exclusivo en territorio nacional y MERCOSUR autorizado.
    (Contrato completo de 12 cláusulas foliado en archivo JM-001)
    """
    pdf.multi_cell(0, 7, cuerpo)
    if firma_path:
        pdf.image(firma_path, x=130, w=50)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. LÓGICA DE NAVEGACIÓN ---
init_db()
aplicar_estilos_premium()

if 'user' not in st.session_state:
    # --- LOGIN ---
    st.markdown('<div class="header-jm"><h1>JM</h1><p>ACCESO AL SISTEMA</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Correo o Teléfono")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR"):
            st.session_state.user = u
            st.session_state.is_admin = (u == "admin")
            st.rerun()
        
        c1, c2 = st.columns(2)
        if c1.button("Crear Cuenta"): st.info("Diríjase a la oficina para registro oficial.")
        if c2.button("Olvidé mi clave"): st.warning("Contacte al soporte técnico.")
else:
    # --- APP PRINCIPAL ---
    with st.sidebar:
        st.markdown(f"👤 **Usuario:** {st.session_state.user}")
        if st.button("CERRAR SESIÓN"):
            del st.session_state['user']
            st.rerun()

    st.markdown('<div class="header-jm"><h1>JM ASOCIADOS</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Catálogo", "📅 Mi Historial", "📍 Ubicación", "🛡️ Admin" if st.session_state.is_admin else "info"])

    with tabs[0]:
        conn = sqlite3.connect('jm_asociados_final.db')
        df = pd.read_sql_query("SELECT * FROM flota", conn)
        for i, r in df.iterrows():
            if r['estado'] == "Disponible":
                with st.container():
                    st.markdown(f"""<div class='card-auto'>
                        <img src='{r['img']}' width='180' style='float:right;'>
                        <h3>{r['nombre']}</h3>
                        <p><b>R$ {r['precio_brl']} / Gs. {r['precio_brl']*1450:,.0f} por día</b></p>
                    </div>""", unsafe_allow_html=True)
                    
                    with st.expander("RESERVAR VEHÍCULO"):
                        c1, c2 = st.columns(2)
                        f1 = c1.date_input("Entrega", key=f"f1{i}")
                        h1 = c1.time_input("Hora Entrega", value=time(8,0), key=f"h1{i}")
                        f2 = c2.date_input("Devolución", key=f"f2{i}")
                        h2 = c2.time_input("Hora Devolución", value=time(8,0), key=f"h2{i}")
                        doc_u = st.text_input("Confirme su Nro Documento", key=f"doc{i}")
                        
                        if esta_disponible(r['id'], f1, f2):
                            st.write("Firma aquí:")
                            canvas = st_canvas(height=100, stroke_width=2, key=f"canv{i}")
                            
                            if st.button("CONFIRMAR ALQUILER", key=f"re{i}"):
                                dias = (f2-f1).days if (f2-f1).days > 0 else 1
                                total = dias * r['precio_brl']
                                
                                # Guardar
                                conn.execute("INSERT INTO reservas (auto_id, f_ini, f_fin, cliente, monto) VALUES (?,?,?,?,?)", (r['id'], f1, f2, st.session_state.user, total))
                                conn.commit()
                                
                                # PDF
                                firma_path = f"f_{i}.png"
                                Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').save(firma_path)
                                datos = {'nombre': st.session_state.user, 'doc': doc_u, 'auto': r['nombre'], 'chapa': r['chapa'], 'chasis': r['chasis'], 'f1': f1, 'h1': h1, 'f2': f2, 'h2': h2, 'total_brl': total, 'total_pyg': total*1450}
                                st.session_state.pdf = generar_contrato_oficial(datos, firma_path)
                                
                                # Mensaje WA
                                saludo = f"Estimados JM ASOCIADOS, un cordial saludo.%0A%0AMi nombre es {st.session_state.user} (Doc: {doc_u}).%0AHe realizado la reserva del {r['nombre']}.%0A%0ADatos:%0A- Entrega: {f1} a las {h1}%0A- Devolución: {f2} a las {h2}%0A- Total: R$ {total}%0A%0AAdjunto el contrato y mi comprobante de pago."
                                st.session_state.wa = f"https://wa.me/595991681191?text={saludo}"
                                st.rerun()

        if 'pdf' in st.session_state:
            st.success("¡Reserva completada!")
            # Botón de descarga para evitar bloqueos
            st.download_button("📥 DESCARGAR CONTRATO (PDF)", st.session_state.pdf, "Contrato_JM.pdf", "application/pdf")
            st.markdown(f'<a href="{st.session_state.wa}" class="btn-social" style="background:#25D366;">📲 NOTIFICAR A WHATSAPP EMPRESA</a>', unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("📍 Nuestra Oficina")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d3600.9!2d-54.6!" width="100%" height="300" style="border:0; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown('<a href="https://wa.me/595991681191" class="btn-social" style="background:#25D366;">WhatsApp Corporativo</a>', unsafe_allow_html=True)
        st.markdown('<a href="https://www.instagram.com/jm_asociados_consultoria" class="btn-social" style="background:#E1306C; margin-top:10px;">Instagram JM</a>', unsafe_allow_html=True)

    if st.session_state.is_admin:
        with tabs[3]:
            st.subheader("🛡️ Panel Administrativo")
            conn = sqlite3.connect('jm_asociados_final.db')
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)
            st.write(f"**Ingresos Totales:** R$ {df_res['monto'].sum():,.2f}")
            
            st.write("---")
            st.write("**Control de Flota:**")
            df_flota = pd.read_sql_query("SELECT * FROM flota", conn)
            for i, r in df_flota.iterrows():
                col1, col2 = st.columns([3,1])
                nuevo = col2.selectbox(f"{r['nombre']}", ["Disponible", "En Taller", "Desperfecto"], index=0 if r['estado']=="Disponible" else 1, key=f"adm{i}")
                if nuevo != r['estado']:
                    conn.execute("UPDATE flota SET estado=? WHERE id=?", (nuevo, r['id']))
                    conn.commit()
                    st.rerun()
