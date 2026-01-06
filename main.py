import streamlit as st
import sqlite3
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURACIÓN Y ESTILO JM (BORDO Y DORADO) ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main { background-color: #000000; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'Georgia', serif; }
    
    /* Estilo de las Pestañas */
    .stTabs [data-baseweb="tab-list"] { background-color: #4A0404; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
    .stTabs [data-baseweb="tab"]:hover { color: #D4AF37 !important; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: #4A0404 !important; border-radius: 5px; }

    /* Tarjetas de Autos */
    .card-auto { 
        background: linear-gradient(135deg, #4A0404 0%, #2D0202 100%); 
        padding: 25px; border-radius: 20px; border: 2px solid #D4AF37; 
        margin-bottom: 25px; color: white; text-align: center;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    /* Botones de Streamlit */
    .stButton>button { 
        background-color: #D4AF37 !important; color: #4A0404 !important; 
        font-weight: bold; border-radius: 10px; border: none; width: 100%;
    }
    .stButton>button:hover { background-color: #f1c40f !important; transform: scale(1.02); }

    /* Botón de WhatsApp */
    .whatsapp-btn {
        background-color: #25D366; color: white !important; padding: 15px; 
        border-radius: 12px; text-align: center; font-weight: bold; 
        text-decoration: none; display: block; margin-top: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- LÓGICA DE NEGOCIO ---
def obtener_texto_contrato(res, v):
    ini_str = res['inicio'].strftime('%d/%m/%Y %H:%M') if isinstance(res['inicio'], datetime) else str(res['inicio'])
    fin_str = res['fin'].strftime('%d/%m/%Y %H:%M') if isinstance(res['fin'], datetime) else str(res['fin'])
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO - JM ASOCIADOS
--------------------------------------------------------------
ARRENDADOR: JM ASOCIADOS (RUC 1.702.076-0)
ARRENDATARIO: {res['cliente']} | CI/RG: {res['ci']}
DOMICILIO: {res['domicilio']} | TEL: {res['celular']}

VEHÍCULO: {v['marca']} {v['nombre']} | PLACA: {v['placa']}
CHASIS: {v['chasis']} | COLOR: {v['color']} | AÑO: {v['anio']}

ALQUILER DESDE: {ini_str}
ALQUILER HASTA: {fin_str}

TOTAL A PAGAR: R$ {res['total']}
--------------------------------------------------------------
AUTORIZADO PARA CIRCULAR EN TODO EL MERCOSUR.
FIRMA: {res['firma']}
"""

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    autos = [
        ("Hyundai Tucson", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Gris", "KMHJU81VBAU040691", "2010", "HYUNDAI"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", "NSP1352032141", "2015", "TOYOTA"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", "NSP1302097964", "2012", "TOYOTA"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris", "ZRR700415383", "2011", "TOYOTA")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- INTERFAZ ---
st.title("JM ASOCIADOS | RENT-A-CAR")
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMINISTRACIÓN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f"""<div class="card-auto">
                <h3>{v['nombre']}</h3>
                <img src="{v['img']}" width="220">
                <p style="font-size: 20px; color: #D4AF37;"><b>R$ {v['precio']} / día</b></p>
                </div>""", unsafe_allow_html=True)
            
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller":
                    st.error("🚫 VEHÍCULO EN Mantenimiento (Taller)")
                else:
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Fecha Inicio", key=f"fi_{v['nombre']}")
                    h_i = c1.time_input("Hora Inicio", time(9,0), key=f"hi_{v['nombre']}")
                    f_f = c2.date_input("Fecha Fin", key=f"ff_{v['nombre']}")
                    h_f = c2.time_input("Hora Fin", time(10,0), key=f"hf_{v['nombre']}")
                    
                    c_n = st.text_input("Nombre Completo", key=f"n_{v['nombre']}")
                    c_ci = st.text_input("CI / CPF", key=f"ci_{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t_{v['nombre']}")
                    c_fir = st.text_input("Firma Digital", key=f"f_{v['nombre']}")
                    
                    dt_i = datetime.combine(f_i, h_i)
                    dt_f = datetime.combine(f_f, h_f)
                    total = max(1, (f_f - f_i).days) * v['precio']
                    
                    if c_n and c_ci and c_fir:
                        res_temp = {'cliente': c_n, 'ci': c_ci, 'domicilio': 'A definir', 'celular': c_tel, 'inicio': dt_i, 'fin': dt_f, 'total': total, 'firma': c_fir}
                        st.markdown("### 📄 Previsualización del Contrato")
                        txt = obtener_texto_contrato(res_temp, v)
                        st.text_area("Contrato:", txt, height=180)
                        
                        st.markdown(f'<div style="background:#4A0404; color:#D4AF37; padding:10px; border-radius:5px; border:1px solid #D4AF37"><b>PIX Llave: 24510861818</b><br>Monto: R$ {total}</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Subir Comprobante", type=['jpg','png','jpeg'], key=f"p_{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA", key=f"btn_{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma) VALUES (?,?,?,?,?,?,?,?,?)",
                                        (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir))
                            conn.commit(); conn.close()
                            
                            msg = f"Hola JM, soy {c_n}.\nReserva de {v['nombre']}\nMonto: R$ {total}.\nAdjunto comprobante."
                            url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 ENVIAR COMPROBANTE AL CORPORATIVO</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        st.subheader("🛠️ ESTADO DE FLOTA")
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{f['nombre']}** | Estado: {f['estado']}")
            if c2.button("DISP / TALLER", key=f"sw_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        st.subheader("📥 CONTRATOS GENERADOS")
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in res_df.iterrows():
            with st.expander(f"ID {r['id']} - {r['cliente']}"):
                v_pdf = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                txt_pdf = obtener_texto_contrato(r, v_pdf)
                pdf.multi_cell(0, 8, txt_pdf.encode('latin-1', 'replace').decode('latin-1'))
                
                st.download_button(f"Descargar PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['cliente']}.pdf", mime="application/pdf", key=f"dl_{r['id']}")
                if st.button("Borrar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
