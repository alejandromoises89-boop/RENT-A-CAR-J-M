import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

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
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion()
DB_NAME = 'jm_corporativo_permanente.db'

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

# --- FUNCIONES DE SOPORTE ---
def parse_date(dt):
    if isinstance(dt, str):
        try: return datetime.fromisoformat(dt)
        except: return datetime.now()
    return dt

def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    flota_res = c.fetchone()
    if flota_res and flota_res[0] != "Disponible":
        conn.close(); return False, "Vehículo en Taller/No Disponible"
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio.isoformat(), t_fin.isoformat()))
    ocupado = c.fetchone()[0]
    conn.close()
    return (ocupado == 0), "Fechas ocupadas"

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
ARRENDATARIO: {res['cliente']} | CI/RG: {res['ci']}
DOMICILIO: {res['domicilio']} | CELULAR: {res['celular']}

VEHÍCULO: {v['marca']} {v['nombre']} | CHASIS: {v['chasis']}
COLOR: {v['color']} | PLACA: {v['placa']}

DURACIÓN: {dias} días
DESDE: {ini.strftime('%d/%m/%Y %H:%M')} hs
HASTA: {fin.strftime('%d/%m/%Y %H:%M')} hs

PRECIO TOTAL: R$ {res['total']} | Gs. {total_gs:,.0f}
--------------------------------------------------------------
EL ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL 
VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR.

FIRMA CLIENTE: {res['firma']}
FECHA: {datetime.now().strftime('%d/%m/%Y')}"""

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS | SISTEMA CORPORATIVO</h1>", unsafe_allow_html=True)
t_res, t_adm = st.tabs(["📋 RESERVAS Y PAGO", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="180"><p>R$ {v["precio"]} / día</p></div>', unsafe_allow_html=True)
            with st.expander(f"RESERVAR {v['nombre']}"):
                c1, c2 = st.columns(2)
                f_ini = c1.date_input("Fecha Inicio", key=f"fi{v['nombre']}")
                h_ini = c1.time_input("Hora Inicio", time(9,0), key=f"hi{v['nombre']}")
                f_fin = c2.date_input("Fecha Fin", key=f"ff{v['nombre']}")
                h_fin = c2.time_input("Hora Fin", time(10,0), key=f"hf{v['nombre']}")
                
                dt_i = datetime.combine(f_ini, h_ini)
                dt_f = datetime.combine(f_fin, h_fin)
                
                disp, motivo = esta_disponible(v['nombre'], dt_i, dt_f)
                if not disp:
                    st.error(f"❌ {motivo}")
                else:
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("Documento / CPF", key=f"ci{v['nombre']}")
                    c_dom = st.text_input("Domicilio", key=f"d{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t{v['nombre']}")
                    c_fir = st.text_input("Firma Digital (Escriba su nombre)", key=f"f{v['nombre']}")
                    
                    dias_calc = max(1, (f_fin - f_ini).days)
                    monto_total = dias_calc * v['precio']
                    
                    if c_n and c_ci and c_fir:
                        res_temp = {'cliente':c_n, 'ci':c_ci, 'domicilio':c_dom, 'celular':c_tel, 'inicio':dt_i, 'fin':dt_f, 'total':monto_total, 'firma':c_fir}
                        st.subheader("1. Previsualizar Contrato")
                        st.text_area("Términos:", obtener_texto_contrato(res_temp, v), height=150)
                        
                        st.subheader("2. Pago PIX")
                        st.info(f"Monto: R$ {monto_total} | Llave PIX: 24510861818")
                        foto = st.file_uploader("Subir Comprobante", type=['jpg','png','jpeg'], key=f"foto{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                                        (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), monto_total, foto.read(), c_fir, c_dom))
                            conn.commit(); conn.close()
                            
                            # MENSAJE WHATSAPP EXACTO
                            mensaje = (f"Hola JM, soy {c_n.upper()}.\n\n"
                                      f"📄 Mis datos:\nDocumento/CPF: {c_ci}\n\n"
                                      f"🚗 Detalles del Alquiler:\nVehículo: {v['nombre']}\n"
                                      f"📅 Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                      f"📅 Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                      f"💰 Monto Pagado: R$ {monto_total}\n\n"
                                      f"Aquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!")
                            
                            url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(mensaje)}"
                            st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 ENVIAR COMPROBANTE WHATSAPP</a>', unsafe_allow_html=True)
                            st.success("✅ Reserva registrada correctamente.")

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # --- BLOQUEO TALLER ---
        st.subheader("🛠️ Gestión de Flota (Taller)")
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"**{f['nombre']}** - Estado: {f['estado']}")
            if c2.button("CAMBIAR ESTADO", key=f"block_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # --- GASTOS / EGRESOS CON OPCIÓN DE BORRAR ---
        st.subheader("💸 Registro de Egresos")
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        # Mostrar gastos actuales con botón de borrar
        for _, eg in egr_df.iterrows():
            col_e1, col_e2 = st.columns([4, 1])
            col_e1.write(f"📌 {eg['concepto']} - R$ {eg['monto']} ({eg['fecha']})")
            if col_e2.button("🗑️", key=f"del_eg_{eg['id']}"):
                conn.execute("DELETE FROM egresos WHERE id=?", (eg['id'],))
                conn.commit(); st.rerun()

        with st.expander("➕ Cargar Gasto Nuevo"):
            concepto = st.text_input("Concepto")
            monto_eg = st.number_input("Monto R$", min_value=0.0)
            if st.button("Guardar Gasto"):
                conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (concepto, monto_eg, date.today().isoformat()))
                conn.commit(); st.rerun()

        # --- ESTADÍSTICAS ---
        st.subheader("📊 Balance de Ingresos y Egresos")
        df_in = pd.read_sql_query("SELECT total as monto, inicio as fecha FROM reservas", conn)
        df_eg = pd.read_sql_query("SELECT monto, fecha FROM egresos", conn)
        
        if not df_in.empty:
            df_in['Tipo'] = 'Ingreso'; df_eg['Tipo'] = 'Egreso'
            df_balance = pd.concat([df_in, df_eg])
            df_balance['mes'] = pd.to_datetime(df_balance['fecha']).dt.strftime('%b')
            fig = px.bar(df_balance, x='mes', y='monto', color='Tipo', barmode='group', 
                         color_discrete_map={'Ingreso':'#D4AF37', 'Egreso':'#4A0404'})
            st.plotly_chart(fig, use_container_width=True)

        # --- RESERVAS CON OPCIÓN DE BORRAR ---
        st.subheader("📑 Reservas y Contratos PDF")
        res_all = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in res_all.iterrows():
            # Usamos columnas para poner el botón de borrar al lado del expander
            col_r1, col_r2 = st.columns([5, 1])
            with col_r1:
                with st.expander(f"ID: {r['id']} | Cliente: {r['cliente']} - {r['auto']}"):
                    v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    txt = obtener_texto_contrato(r, v_res).encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, txt)
                    st.download_button(f"Descargar PDF {r['id']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_JM_{r['id']}.pdf")
            
            # Botón de borrar reserva
            if col_r2.button("❌ Borrar", key=f"del_res_{r['id']}"):
                conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                conn.commit(); st.rerun()
        
        st.download_button("📥 Descargar Reporte CSV", res_all.to_csv().encode('utf-8'), "reporte_jm.csv")
        conn.close()
