import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA", layout="wide")

if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'role' not in st.session_state: st.session_state.role = "user"
if 'auto_sel' not in st.session_state: st.session_state.auto_sel = None

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, tel TEXT, auto TEXT, inicio DATE, fin DATE, total REAL, estado TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resenas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, comentario TEXT, estrellas INTEGER, fecha DATE)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. DATOS DE FLOTA ---
AUTOS = {
    "Toyota Vitz 2012 (Negro)": {"precio": 195, "specs": "Automático | Nafta | Económico", "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
    "Hyundai Tucson 2012": {"precio": 260, "specs": "4x2 | Diesel | Confort", "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
    "Toyota Voxy 2009": {"precio": 240, "specs": "Familiar | 7 Pasajeros | Amplio", "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
    "Toyota Vitz 2012 (Blanco)": {"precio": 195, "specs": "Automático | Aire Full | Carta Verde", "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
}

# --- 4. ESTILOS ---
st.markdown("""<style>
    .stApp { background-color: #4A0404; color: white; }
    .card-auto { background-color: white; color: black; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 15px; }
    .btn-social { display: block; padding: 15px; margin: 10px 0; border-radius: 10px; text-decoration: none; text-align: center; font-weight: bold; color: white !important; }
    .btn-whatsapp { background-color: #25D366; }
    .btn-insta { background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); }
    .header-jm { background-color: #300000; padding: 20px; color: #D4AF37; text-align: center; border-bottom: 5px solid #D4AF37; margin-bottom: 20px; }
</style>""", unsafe_allow_html=True)

# --- 5. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("USUARIO / TELÉFONO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("INGRESAR"):
            if u == "admin" and p == "2026": st.session_state.role = "admin"
            st.session_state.autenticado = True
            st.session_state.user_name = u
            st.rerun()
else:
    st.markdown('<div class="header-jm"><h1>JM ASOCIADOS - Alquiler de Vehículos</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["🚗 Catálogo", "📅 Mis Alquileres", "📍 Ubicación", "⭐ Reseñas", "🛡️ Panel Master"])

    # --- TAB 1: CATÁLOGO Y PAGO ---
    with tabs[0]:
        for nombre, info in AUTOS.items():
            with st.container():
                st.markdown(f'''<div class="card-auto"><div style="display: flex; align-items: center; gap: 20px;">
                    <img src="{info['img']}" width="200"><div>
                    <h3 style="color:#4A0404; margin:0;">{nombre}</h3>
                    <p style="color:#666;">{info['specs']}</p>
                    <h4 style="color:#D4AF37;">Tarifa: R$ {info['precio']} / día</h4>
                    </div></div></div>''', unsafe_allow_html=True)
                if st.button(f"Seleccionar {nombre}", key=f"sel_{nombre}"):
                    st.session_state.auto_sel = nombre

        if st.session_state.auto_sel:
            st.divider()
            with st.form("form_pago"):
                st.subheader(f"Confirmar Reserva: {st.session_state.auto_sel}")
                c1, c2 = st.columns(2)
                tel = c1.text_input("Número de WhatsApp")
                dias = c2.number_input("Días de Alquiler", 1, 30)
                f_ini = c1.date_input("Fecha de Inicio", date.today())
                total = dias * AUTOS[st.session_state.auto_sel]['precio']
                
                st.markdown(f"### Total: R$ {total}")
                st.info("🏦 **DATOS PARA PAGO PIX:**\n\nChave PIX: **JMASOCIADOS2026PIX**\nBanco: JM Bank")
                
                if st.form_submit_button("CONFIRMAR RESERVA"):
                    conn = sqlite3.connect('jm_asociados.db')
                    conn.cursor().execute("INSERT INTO reservas (cliente, tel, auto, inicio, fin, total, estado) VALUES (?,?,?,?,?,?,?)",
                                 (st.session_state.user_name, tel, st.session_state.auto_sel, f_ini, f_ini + timedelta(days=dias), total, "Pendiente"))
                    conn.commit()
                    conn.close()
                    
                    # Enlace de WhatsApp
                    msg = f"Hola JM ASOCIADOS! He reservado el {st.session_state.auto_sel}.\nTotal: R$ {total}.\nAquí envío mi comprobante PIX."
                    url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                    st.success("✅ Reserva registrada en sistema.")
                    st.markdown(f'<a href="{url_wa}" target="_blank" class="btn-social btn-whatsapp">📤 Enviar Comprobante por WhatsApp</a>', unsafe_allow_html=True)

    # --- TAB 3: UBICACIÓN ---
    with tabs[2]:
        col_m, col_info = st.columns([2, 1])
        with col_m:
            st.markdown("### 📍 Ubicación")
            st.markdown('<iframe src="https://www.google.com/maps/embed?..." width="100%" height="400" style="border:0; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        with col_info:
            st.write("**Edificio Aramí**")
            st.write("Esq. Farid Rahal y Curupayty, CDE")
            st.markdown('<a href="https://instagram.com/jymasociados" class="btn-social btn-insta">📸 Instagram</a>', unsafe_allow_html=True)

    # --- TAB 4: RESEÑAS ---
    with tabs[3]:
        st.subheader("⭐ Danos tu calificación")
        with st.form("resena"):
            est = st.slider("Estrellas", 1, 5, 5)
            com = st.text_area("Tu experiencia")
            if st.form_submit_button("Publicar"):
                conn = sqlite3.connect('jm_asociados.db')
                conn.cursor().execute("INSERT INTO resenas (cliente, comentario, estrellas, fecha) VALUES (?,?,?,?)",
                             (st.session_state.user_name, com, est, date.today()))
                conn.commit()
                conn.close()
                st.rerun()
        
        st.divider()
        conn = sqlite3.connect('jm_asociados.db')
        re_df = pd.read_sql_query("SELECT * FROM resenas ORDER BY id DESC", conn)
        conn.close()
        for _, r in re_df.iterrows():
            st.markdown(f"**{r['cliente']}** {'⭐'*r['estrellas']}")
            st.write(r['comentario'])
            st.caption(f"Fecha: {r['fecha']}")
            st.divider()

    # --- TAB 5: ADMIN FINANCIERO ---
    if st.session_state.role == "admin":
        with tabs[4]:
            st.title("📊 Panel Financiero")
            conn = sqlite3.connect('jm_asociados.db')
            df_ad = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Ingresos Totales", f"R$ {df_ad['total'].sum():,}")
            c2.metric("Nº Reservas", len(df_ad))
            c3.metric("Ticket Promedio", f"R$ {df_ad['total'].mean():.2f}" if not df_ad.empty else 0)
            
            st.subheader("Registro General")
            st.dataframe(df_ad, use_container_width=True)
            if st.button("LIMPIAR REGISTROS"):
                conn.cursor().execute("DELETE FROM reservas")
                conn.commit()
                st.rerun()
            conn.close()
