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
    .whatsapp-btn {
        background-color: #25D366; color: white !important; padding: 15px; 
        border-radius: 10px; text-align: center; font-weight: bold; text-decoration: none; display: block;
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

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verificar si el auto está en taller
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res_f = c.fetchone()
    if res_f and res_f[0] == "Taller":
        conn.close(); return False, "El vehículo está en Mantenimiento/Taller."
    
    # Verificar si hay choques de fechas
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio.isoformat(), t_fin.isoformat()))
    ocupado = c.fetchone()[0]
    conn.close()
    if ocupado > 0:
        return False, "El vehículo ya está reservado en estas fechas."
    return True, ""

# --- CONTRATO LEGAL ---
def obtener_texto_contrato(res, v):
    ini = parse_date(res['inicio'])
    fin = parse_date(res['fin'])
    dias = max(1, (fin - ini).days)
    total_gs = float(res['total']) * COTIZACION_DIA
    precio_dia_gs = total_gs / dias
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO - JM ASOCIADOS
--------------------------------------------------------------
ARRENDADOR: JM ASOCIADOS (RUC 1.702.076-0)
ARRENDATARIO: {res['cliente']} | CI: {res['ci']}
DOMICILIO: {res['domicilio']} | TEL: {res['celular']}

VEHÍCULO: {v['marca']} {v['nombre']} | PLACA: {v['placa']}
CHASIS: {v['chasis']} | COLOR: {v['color']}

DURACIÓN: {dias} días.
RECOGIDA: {ini.strftime('%d/%m/%Y %H:%M')} hs.
DEVOLUCIÓN: {fin.strftime('%d/%m/%Y %H:%M')} hs.

MONTO TOTAL: R$ {res['total']} (Gs. {total_gs:,.0f})
--------------------------------------------------------------
* El arrendatario es responsable penal y civil del vehículo.
* Autorizado para conducir en Paraguay y MERCOSUR.
* Depósito de seguridad en caso de siniestro: Gs. 5.000.000.

FIRMA CLIENTE: {res['firma']}
FECHA: {datetime.now().strftime('%d/%m/%Y')}"""

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    conn.commit(); conn.close()

init_db()

# --- INTERFAZ ---
st.title("JM ASOCIADOS | SISTEMA DE ALQUILER")
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="180"><p>R$ {v["precio"]} / día</p></div>', unsafe_allow_html=True)
            with st.expander(f"RESERVAR {v['nombre']}"):
                # 1. FECHAS Y HORAS
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"fi{v['nombre']}")
                h_ini = c1.time_input("Hora Inicio", time(9,0), key=f"hi{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"ff{v['nombre']}")
                h_fin = c2.time_input("Hora Fin", time(10,0), key=f"hf{v['nombre']}")
                
                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                # VALIDACIÓN DE BLOQUEO
                disponible, motivo = esta_disponible(v['nombre'], dt_i, dt_f)
                
                if not disponible:
                    st.error(f"❌ {motivo}")
                else:
                    st.success("✅ Disponible en estas fechas")
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("CI / RG / CPF", key=f"ci{v['nombre']}")
                    c_dom = st.text_input("Domicilio", key=f"d{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t{v['nombre']}")
                    c_fir = st.text_input("Firma Digital (Escriba su Nombre)", key=f"f{v['nombre']}")
                    
                    dias = max(1, (f_fin - f_ini).days)
                    total = dias * v['precio']
                    
                    if c_n and c_ci and c_fir:
                        res_temp = {'cliente':c_n, 'ci':c_ci, 'domicilio':c_dom, 'celular':c_tel, 'inicio':dt_i, 'fin':dt_f, 'total':total, 'firma':c_fir}
                        
                        st.subheader("📝 Previsualización del Contrato")
                        st.text_area("Lea los términos:", obtener_texto_contrato(res_temp, v), height=150)
                        
                        st.markdown(f'<div style="background:#f0f2f6; padding:15px; border-radius:10px; color:black; border-left:5px solid #D4AF37;"><b>DATOS PARA PAGO PIX</b><br>Monto: R$ {total}<br>Llave PIX: 24510861818</div>', unsafe_allow_html=True)
                        
                        foto = st.file_uploader("Subir foto del comprobante", type=['jpg','png','pdf'], key=f"foto{v['nombre']}")
                        
                        if st.button("CONFIRMAR Y FINALIZAR", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir, c_dom))
                                conn.commit(); conn.close()
                                st.balloons()
                                
                                # BOTÓN DE WHATSAPP
                                texto_wa = f"Hola JM ASOCIADOS, realicé una reserva.\nCliente: {c_n}\nAuto: {v['nombre']}\nTotal: R$ {total}"
                                url_wa = f"https://wa.me/595983635573?text={urllib.parse.quote(texto_wa)}"
                                st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 ENVIAR COMPROBANTE AL CORPORATIVO</a>', unsafe_allow_html=True)
                            else:
                                st.warning("⚠️ Debe subir el comprobante para confirmar.")

with t_adm:
    if st.text_input("Acceso Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        st.subheader("🛠️ Gestión de Flota (Taller)")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            col1, col2 = st.columns([3,1])
            col1.write(f"**{f['nombre']}** ({f['estado']})")
            if col2.button("TALLER / DISP", key=f"tk{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📈 Estadísticas")
        res_df = pd.read_sql_query("SELECT total, inicio FROM reservas", conn)
        if not res_df.empty:
            res_df['mes'] = pd.to_datetime(res_df['inicio']).dt.strftime('%m-%b')
            fig = px.bar(res_df.groupby('mes')['total'].sum().reset_index(), x='mes', y='total', title="Ingresos R$", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig)
        conn.close()
