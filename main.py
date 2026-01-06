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
    .whatsapp-btn {
        background-color: #25D366; color: white !important; padding: 15px; 
        border-radius: 10px; text-align: center; font-weight: bold; text-decoration: none; display: block; margin-top: 10px;
    }
    .stButton>button { background-color: #D4AF37 !important; color: #4A0404 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE BASE DE DATOS Y COTIZACIÓN ---
DB_NAME = 'jm_corporativo_permanente.db'

def obtener_cotizacion():
    try:
        data = requests.get("https://open.er-api.com/v6/latest/BRL", timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except: return 1450.0

COTIZACION_DIA = obtener_cotizacion()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE LÓGICA ---
def parse_date(dt):
    if isinstance(dt, str):
        try: return datetime.fromisoformat(dt)
        except: return datetime.now()
    return dt

def obtener_texto_contrato(res, v):
    ini = parse_date(res['inicio'])
    fin = parse_date(res['fin'])
    total_gs = float(res['total']) * COTIZACION_DIA
    return f"""CONTRATO DE ALQUILER - JM ASOCIADOS
--------------------------------------------------
ARRENDADOR: JM ASOCIADOS (RUC 1.702.076-0)
ARRENDATARIO: {res['cliente']} | CI: {res['ci']}
VEHÍCULO: {v['marca']} {v['nombre']} | PLACA: {v['placa']}
INICIO: {ini.strftime('%d/%m/%Y %H:%M')}
FIN: {fin.strftime('%d/%m/%Y %H:%M')}
MONTO: R$ {res['total']} (Gs. {total_gs:,.0f})
FIRMA: {res['firma']}
--------------------------------------------------"""

# --- INTERFAZ ---
st.title("JM ASOCIADOS | CORPORATIVO")
t_res, t_adm = st.tabs(["📋 RESERVAS Y PAGO", "🛡️ PANEL DE CONTROL"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="200"><p>R$ {v["precio"]} / día</p></div>', unsafe_allow_html=True)
            
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller":
                    st.error("⚠️ Este vehículo está bloqueado por mantenimiento en Taller.")
                else:
                    c1, c2 = st.columns(2)
                    f_ini = c1.date_input("Fecha Inicio", key=f"fi{v['nombre']}")
                    h_ini = c1.time_input("Hora Inicio", time(9,0), key=f"hi{v['nombre']}")
                    f_fin = c2.date_input("Fecha Fin", key=f"ff{v['nombre']}")
                    h_fin = c2.time_input("Hora Fin", time(10,0), key=f"hf{v['nombre']}")
                    
                    dt_i = datetime.combine(f_ini, h_ini)
                    dt_f = datetime.combine(f_fin, h_fin)
                    
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("Documento / CPF", key=f"ci{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t{v['nombre']}")
                    c_fir = st.text_input("Firma (Nombre)", key=f"f{v['nombre']}")
                    
                    dias = max(1, (f_fin - f_ini).days)
                    total = dias * v['precio']
                    
                    if c_n and c_ci:
                        st.info(f"Monto a pagar: R$ {total}")
                        st.subheader("1. Previsualizar Contrato")
                        res_temp = {'cliente':c_n, 'ci':c_ci, 'inicio':dt_i, 'fin':dt_f, 'total':total, 'firma':c_fir, 'celular':c_tel, 'domicilio':''}
                        st.text_area("Términos:", obtener_texto_contrato(res_temp, v), height=100)
                        
                        st.subheader("2. Pago PIX")
                        st.code("Llave PIX: 24510861818", language="text")
                        foto = st.file_uploader("Subir Comprobante", type=['jpg','png','jpeg'], key=f"foto{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}"):
                            if foto:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma) VALUES (?,?,?,?,?,?,?,?,?)", 
                                            (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir))
                                conn.commit(); conn.close()
                                
                                # MENSAJE DE WHATSAPP FORMATEADO
                                msg = (f"Hola JM, soy {c_n.upper()}.\n\n"
                                       f"📄 Mis datos:\nDocumento/CPF: {c_ci}\n\n"
                                       f"🚗 Detalles del Alquiler:\nVehículo: {v['nombre']}\n"
                                       f"📅 Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                       f"📅 Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                       f"💰 Monto Pagado: R$ {total}\n\n"
                                       f"Aquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!")
                                
                                url_wa = f"https://wa.me/595983635573?text={urllib.parse.quote(msg)}"
                                st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva registrada! Use el botón de arriba para avisar por WhatsApp.")
                            else:
                                st.warning("Por favor suba el comprobante.")

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # --- BLOQUEO DE AUTOS ---
        st.subheader("🛠️ Gestión de Flota (Bloqueo Taller)")
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"**{f['nombre']}** - Estado: {f['estado']}")
            if c2.button("CAMBIAR", key=f"bk{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # --- ESTADÍSTICAS ---
        st.subheader("📈 Proyección de Ingresos y Egresos")
        
        # Formulario de Egresos
        with st.expander("➕ Registrar Gasto (Egreso)"):
            con_eg = st.text_input("Concepto")
            mon_eg = st.number_input("Monto R$", min_value=0.0)
            if st.button("Guardar Egreso"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (con_eg, mon_eg, date.today().isoformat()))
                conn.commit(); st.rerun()

        # Gráfica
        df_in = pd.read_sql_query("SELECT total as monto, inicio as fecha FROM reservas", conn)
        df_eg = pd.read_sql_query("SELECT monto, fecha FROM egresos", conn)
        
        if not df_in.empty:
            df_in['Tipo'] = 'Ingreso'
            df_eg['Tipo'] = 'Egreso'
            df_total = pd.concat([df_in, df_eg])
            df_total['mes'] = pd.to_datetime(df_total['fecha']).dt.strftime('%b')
            fig = px.bar(df_total, x='mes', y='monto', color='Tipo', barmode='group',
                         color_discrete_map={'Ingreso':'#D4AF37', 'Egreso':'#4A0404'}, title="Balance Mensual R$")
            st.plotly_chart(fig, use_container_width=True)

        # --- DESCARGAS ---
        st.subheader("📑 Descargar Contratos y Datos")
        res_all = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in res_all.iterrows():
            v_info = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, obtener_texto_contrato(r, v_info).encode('latin-1', 'replace').decode('latin-1'))
            st.download_button(f"📥 PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['id']}.pdf")
        
        st.download_button("📊 Descargar Reporte Excel (CSV)", res_all.to_csv().encode('utf-8'), "reporte_jm.csv")
        conn.close()
