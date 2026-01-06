import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# --- ESTILO PREMIUM BORDO Y DORADO ---
st.markdown("""
    <style>
    .main { background-color: #000000; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'Georgia', serif; }
    .stTabs [data-baseweb="tab-list"] { background-color: #4A0404; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    .card-auto { 
        background: linear-gradient(135deg, #4A0404 0%, #2D0202 100%); 
        padding: 20px; border-radius: 15px; border: 2px solid #D4AF37; 
        margin-bottom: 20px; color: white; text-align: center;
    }
    .insta-btn {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        color: white !important; padding: 12px; border-radius: 10px; text-align: center; 
        text-decoration: none; display: block; font-weight: bold; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE SOPORTE ---
def obtener_cotizacion():
    try:
        data = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion()
DB_NAME = 'jm_corporativo_permanente.db'

def parse_date(dt):
    if isinstance(dt, str):
        try: return datetime.fromisoformat(dt)
        except: return datetime.now()
    return dt

# --- CONTRATO LEGAL CORREGIDO ---
def obtener_texto_contrato(res, v):
    # Aseguramos que las fechas sean objetos datetime para usar strftime
    ini = parse_date(res['inicio'])
    fin = parse_date(res['fin'])
    dias = max(1, (fin - ini).days)
    total_gs = float(res['total']) * COTIZACION_DIA
    precio_dia_gs = total_gs / dias
    
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR

ARRENDADOR: JM ASOCIADOS (C.I. 1.702.076-0)
Domicilio: Curupayty esq. Farid Rahal | Tel: +595983635573

ARRENDATARIO: {res['cliente']}
Documento: RG/CPF {res['ci']} | Tel: {res['celular']}
Domicilio: {res['domicilio']}

1. OBJETO: Alquiler de {v['marca']} {v['nombre'].upper()} ({v['anio']})
Color: {v['color'].upper()} | Chapa: {v['placa']} | Chasis: {v['chasis']}

2. DURACIÓN: {dias} días.
Desde: {ini.strftime('%d/%m/%Y %H:%M')} hs.
Hasta: {fin.strftime('%d/%m/%Y %H:%M')} hs.

3. PRECIO: R$ {res['total']} (Gs. {total_gs:,.0f})
Costo Diario: Gs. {precio_dia_gs:,.0f}

4. DEPÓSITO: Gs. 5.000.000 en caso de siniestro.

5. CONDICIONES: Uso personal, responsabilidad penal/civil del arrendatario.
6. KILOMETRAJE: Límite 200km/día (Excedente: Gs. 100.000).
7. SEGURO: Responsabilidad civil y rastreo satelital.
8. MANTENIMIENTO: Agua, aceite y limpieza a cargo del arrendatario.
9. DEVOLUCIÓN: En las mismas condiciones. Penalidad por demora.

El ARRENDADOR autoriza la conducción en Paraguay y MERCOSUR.

CIUDAD DEL ESTE, {datetime.now().strftime('%d/%m/%Y')}

JM ASOCIADOS (Arrendador)             FIRMA CLIENTE: {res['firma']}
"""

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Gris", "KMHJU81VBAU040691", "2010", "HYUNDAI"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", "NSP1352032141", "2015", "TOYOTA"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", "NSP1302097964", "2012", "TOYOTA"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris", "ZRR700415383", "2011", "TOYOTA")
    ]
    for a in autos:
        c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- INTERFAZ ---
st.title("JM ASOCIADOS | CORPORATIVO")
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p>R$ {v["precio"]} / Gs. {v["precio"]*COTIZACION_DIA:,.0f}</p></div>', unsafe_allow_html=True)
            if v['estado'] == "Disponible":
                with st.expander("RESERVAR"):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("CI / RG / CPF", key=f"ci{v['nombre']}")
                    c_dom = st.text_input("Domicilio", key=f"d{v['nombre']}")
                    c_tel = st.text_input("Teléfono (WhatsApp)", key=f"t{v['nombre']}")
                    c_i = st.date_input("Fecha Inicio", key=f"i{v['nombre']}")
                    c_f = st.date_input("Fecha Fin", key=f"f{v['nombre']}")
                    
                    dias_res = (c_f - c_i).days
                    total = max(1, dias_res) * v['precio']
                    
                    if c_n and c_ci:
                        st.write(f"**Total Est.: R$ {total}**")
                        firma = st.text_input("Firma Digital (Escriba su Nombre)", key=f"fir{v['nombre']}")
                        foto = st.file_uploader("Subir Comprobante PIX", key=f"p{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto and firma:
                                dt_i = datetime.combine(c_i, time(9,0)).isoformat()
                                dt_f = datetime.combine(c_f, time(10,0)).isoformat()
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", (c_n, c_ci, c_tel, v['nombre'], dt_i, dt_f, total, foto.read(), firma, c_dom))
                                conn.commit(); conn.close()
                                st.success("✅ ¡Reserva guardada con éxito!")
                            else:
                                st.warning("Por favor, suba el comprobante y firme.")
            else:
                st.error(f"⚠️ {v['estado']}")

with t_ubi:
    st.markdown('<a href="https://instagram.com/jm_asociados_consultoria" class="insta-btn">📸 INSTAGRAM OFICIAL</a>', unsafe_allow_html=True)
    st.info("📍 Ubicación: Curupayty Esquina Farid Rahal, Ciudad del Este.")

with t_adm:
    if st.text_input("Clave Administrador", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # 1. Bloqueo de Taller
        st.subheader("🛠️ GESTIÓN DE FLOTA (BLOQUEO)")
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"**{f['nombre']}** - Estado actual: {f['estado']}")
            if c2.button("ALTERNAR TALLER", key=f"block_{f['nombre']}"):
                nuevo = "Disponible" if f['estado'] == "Taller" else "Taller"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # 2. Estadísticas (Gráfica)
        st.subheader("📈 PROYECCIÓN DE INGRESOS")
        res_df = pd.read_sql_query("SELECT total, inicio FROM reservas", conn)
        if not res_df.empty:
            res_df['mes'] = pd.to_datetime(res_df['inicio']).dt.strftime('%m - %b')
            proy = res_df.groupby('mes')['total'].sum().reset_index()
            fig = px.bar(proy, x='mes', y='total', title="Ingresos (R$)", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)

        # 3. Contratos y Descargas
        st.subheader("📑 REGISTRO DE CONTRATOS")
        reservas = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in reservas.iterrows():
            with st.expander(f"Cliente: {r['cliente']} | Auto: {r['auto']}"):
                try:
                    v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=9)
                    # Limpieza para el PDF
                    texto_pdf = obtener_texto_contrato(r, v_res).encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, texto_pdf)
                    
                    st.download_button(f"📥 Descargar PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_JM_{r['id']}.pdf")
                except:
                    st.error("Error al generar este contrato.")
        
        st.download_button("📊 DESCARGAR BASE DE DATOS (EXCEL/CSV)", reservas.to_csv().encode('utf-8'), "datos_jm_asociados.csv")
        conn.close()
