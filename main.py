import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ALQUILER PREMIUM",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png"
)

# --- ESTILOS CSS PROFESIONALES (LUXURY DARK THEME) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a;
    }

    .main {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Título Luxury */
    .luxury-header {
        text-align: center;
        padding: 40px 0;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
        border-radius: 20px;
        margin-bottom: 30px;
    }

    .luxury-header h1 {
        color: #D4AF37;
        font-weight: 800;
        letter-spacing: -1px;
        text-transform: uppercase;
        margin: 0;
    }

    /* Card de Vehículo */
    .card-auto {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 25px;
        padding: 25px;
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }

    .card-auto:hover {
        transform: translateY(-10px);
        border-color: #D4AF37;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    /* Badge de Disponibilidad */
    .badge-disp {
        background-color: #25D366;
        color: white;
        padding: 4px 12px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
    }

    /* Botones Premium */
    .stButton>button {
        background: linear-gradient(90deg, #D4AF37, #C49B2D);
        color: #0f172a !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        border: none !important;
        width: 100%;
        padding: 12px !important;
        transition: all 0.3s !important;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(212, 175, 55, 0.3);
    }

    /* Contrato Visual */
    .contrato-box {
        background: #f8fafc;
        color: #334155;
        padding: 30px;
        border-radius: 15px;
        border-left: 10px solid #D4AF37;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Calendario Airbnb Style */
    .cal-container {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding: 10px;
    }
    .cal-day {
        min-width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        background: rgba(255,255,255,0.05);
        font-size: 12px;
    }
    .cal-day.occupied {
        background: #ef4444;
        text-decoration: line-through;
        opacity: 0.5;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
DB_NAME = 'jm_corporativo_v2.db'

def obtener_cotizacion():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, 
                 inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465")
    ]
    c.executemany("INSERT OR IGNORE INTO flota (nombre, precio, img, estado, placa) VALUES (?,?,?,?,?)", autos)
    conn.commit()
    conn.close()

def obtener_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

init_db()

# --- INTERFAZ DE USUARIO ---
st.markdown('<div class="luxury-header"><h1>JM Alquiler de Vehículos</h1><p style="color:#888;">Executive Fleet Management • Ciudad del Este</p></div>', unsafe_allow_html=True)

tab_res, tab_ubi, tab_adm = st.tabs(["💎 RESERVAR AHORA", "📍 UBICACIÓN", "🔐 ADMINISTRACIÓN"])

with tab_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()

    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            precio_gs = v['precio'] * COTIZACION_DIA
            st.markdown(f"""
                <div class="card-auto">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="badge-disp">{v['estado']}</span>
                        <span style="color:#888; font-size:12px;">Placa: {v['placa']}</span>
                    </div>
                    <h3 style="color:white; margin: 15px 0 5px 0;">{v['nombre']}</h3>
                    <img src="{v['img']}" style="width:100%; height:200px; object-fit:contain; margin:10px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <p style="color:#D4AF37; font-size:24px; font-weight:800; margin:0;">R$ {v['precio']}</p>
                            <p style="color:#25D366; font-size:14px; margin:0;">Gs. {precio_gs:,.0f} / día</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            with st.expander("RESERVAR ESTE VEHÍCULO"):
                ocupadas = obtener_ocupadas(v['nombre'])
                
                # Selector de Fechas y Horas
                c1, c2 = st.columns(2)
                f_i = c1.date_input("Recogida", min_value=date.today(), key=f"fi_{v['nombre']}")
                f_f = c2.date_input("Devolución", min_value=f_i, key=f"ff_{v['nombre']}")
                
                h_i = c1.time_input("Hora Entrega", time(8, 0), key=f"hi_{v['nombre']}")
                h_f = c2.time_input("Hora Retorno", time(17, 0), key=f"hf_{v['nombre']}")

                # Validación de Disponibilidad
                conflictos = [d for d in pd.date_range(f_i, f_f) if d.date() in ocupadas]
                
                if conflictos:
                    st.error("⚠️ Vehículo no disponible en esas fechas.")
                else:
                    st.info("✅ Disponible para las fechas seleccionadas.")
                    nombre = st.text_input("Nombre y Apellido", key=f"nom_{v['nombre']}")
                    doc = st.text_input("Documento (CI / RG / CPF)", key=f"doc_{v['nombre']}")
                    tel = st.text_input("WhatsApp (con código de país)", key=f"tel_{v['nombre']}")
                    
                    dias = max(1, (f_f - f_i).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    st.markdown(f"""
                    <div class="contrato-box">
                        <center><b>CONTRATO DE ALQUILER DIGITAL</b></center><br>
                        <b>CLIENTE:</b> {nombre.upper() if nombre else '---'}<br>
                        <b>DOC:</b> {doc.upper() if doc else '---'}<br>
                        <b>VEHÍCULO:</b> {v['nombre']}<br>
                        <b>DURACIÓN:</b> {dias} días ({f_i} al {f_f})<br>
                        <b>TOTAL:</b> R$ {total_r:,.2f} / Gs. {total_gs:,.0f}<br><br>
                        <i>* Al confirmar, usted acepta responsabilidad civil y penal del vehículo. Depósito de garantía requerido: Gs. 5.000.000.</i>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    pago_ok = st.checkbox("Acepto los términos y he realizado el pago PIX", key=f"chk_{v['nombre']}")
                    foto = st.file_uploader("Adjuntar Comprobante", type=['png', 'jpg', 'pdf'], key=f"foto_{v['nombre']}")
                    
                    if st.button("CONFIRMAR Y ENVIAR WHATSAPP", key=f"btn_{v['nombre']}"):
                        if pago_ok and foto and nombre and doc:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", 
                                         (nombre, doc, tel, v['nombre'], f"{f_i} {h_i}", f"{f_f} {h_f}", total_r, foto.read()))
                            conn.commit()
                            conn.close()
                            
                            # Link de WhatsApp
                            msg = f"Hola JM! Reserva Confirmada.\n👤 Cliente: {nombre}\n🚗 Auto: {v['nombre']}\n📅 {f_i} al {f_f}\n💰 Total: R$ {total_r}"
                            link = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.success("¡Reserva guardada con éxito!")
                            st.markdown(f'<a href="{link}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">ABRIR WHATSAPP</a>', unsafe_allow_html=True)
                        else:
                            st.warning("Complete todos los campos y adjunte el comprobante.")

with tab_ubi:
    st.markdown("""
        <div style="background:rgba(30,41,59,0.5); padding:40px; border-radius:30px; border:1px solid #D4AF37; text-align:center;">
            <h2 style="color:#D4AF37;">Nuestra Ubicación Estratégica</h2>
            <p style="color:white;">Avda. San José - Ciudad del Este, Paraguay</p>
            <div style="border-radius:20px; overflow:hidden; border:5px solid rgba(255,255,255,0.1);">
                <iframe width="100%" height="450" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy"></iframe>
            </div>
        </div>
    """, unsafe_allow_html=True)

with tab_adm:
    clave = st.text_input("Password de Administrador", type="password")
    if clave == "8899":
        st.title("📊 Business Intelligence")
        
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_df = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        ingresos = res_df['total'].sum() if not res_df.empty else 0
        gastos = egr_df['monto'].sum() if not egr_df.empty else 0
        m1.metric("INGRESOS (R$)", f"{ingresos:,.2f}")
        m2.metric("EGRESOS (R$)", f"{gastos:,.2f}")
        m3.metric("UTILIDAD (R$)", f"{(ingresos - gastos):,.2f}")
        
        # Gráfico de Ventas
        if not res_df.empty:
            res_df['inicio'] = pd.to_datetime(res_df['inicio'])
            fig = px.line(res_df.sort_values('inicio'), x='inicio', y='total', title="Evolución de Ventas", template="plotly_dark", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)

        # Gestión de Flota
        st.subheader("🚗 Estado de Flota")
        for _, car in flota_df.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{car['nombre']}** ({car['placa']})")
            c2.write(f"R$ {car['precio']}")
            if c3.button("⚙️ Cambiar Estado", key=f"st_{car['nombre']}"):
                nuevo = "En Taller" if car['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado = ? WHERE nombre = ?", (nuevo, car['nombre']))
                conn.commit()
                st.rerun()
        
        # Gestión de Gastos
        st.subheader("💸 Cargar Gasto")
        with st.form("gasto_form"):
            concepto = st.text_input("Detalle del gasto")
            monto_r = st.number_input("Monto en R$", min_value=0.0)
            if st.form_submit_button("Guardar"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (concepto, monto_r, date.today()))
                conn.commit()
                st.success("Gasto registrado")
                st.rerun()

        # Visualizar Comprobantes
        st.subheader("📑 Reservas Recientes")
        if not res_df.empty:
            for _, r in res_df.iterrows():
                with st.expander(f"Reserva {r['id']} - {r['cliente']} - {r['auto']}"):
                    st.write(f"WhatsApp: {r['celular']}")
                    st.write(f"Periodo: {r['inicio']} a {r['fin']}")
                    if r['comprobante']:
                        st.image(r['comprobante'], width=300)
                    if st.button("Eliminar", key=f"del_{r['id']}"):
                        conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()
        
        conn.close()
    elif clave:
        st.error("Acceso denegado")