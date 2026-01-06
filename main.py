import streamlit as st
import sqlite3
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURACIÓN Y ESTILO JM (TODO BORDO CON LETRAS DORADAS) ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

st.markdown("""
    <style>
    /* Fondo General de la página */
    .stApp {
        background-color: #4A0404;
    }
    
    /* Títulos y textos generales */
    h1, h2, h3, p, span, label { 
        color: #D4AF37 !important; 
        font-family: 'Georgia', serif; 
    }

    /* Estilo de las Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #310202; 
        border-radius: 5px; 
    }
    .stTabs [data-baseweb="tab"] { 
        color: #D4AF37 !important; 
    }
    .stTabs [aria-selected="true"] { 
        border-bottom: 2px solid #D4AF37 !important;
        background-color: #5a0505 !important;
    }

    /* Tarjetas de Autos */
    .card-auto { 
        background-color: #4A0404; 
        padding: 25px; 
        border-radius: 15px; 
        border: 2px solid #D4AF37; 
        margin-bottom: 25px; 
        text-align: center;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
    }
    
    /* Botones Estilo Bordo con Letras Doradas */
    .stButton>button { 
        background-color: #4A0404 !important; 
        color: #D4AF37 !important; 
        font-weight: bold; 
        border: 2px solid #D4AF37 !important;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #D4AF37 !important; 
        color: #4A0404 !important; 
    }

    /* Entradas de texto (Inputs) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #310202 !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Botón de WhatsApp */
    .whatsapp-btn {
        background-color: #4A0404; 
        color: #D4AF37 !important; 
        padding: 15px; 
        border-radius: 10px; 
        border: 2px solid #D4AF37;
        text-align: center; 
        font-weight: bold; 
        text-decoration: none; 
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- LÓGICA DE CONTRATO ---
def obtener_texto_contrato(res, v):
    ini_str = res['inicio'].strftime('%d/%m/%Y %H:%M') if isinstance(res['inicio'], datetime) else str(res['inicio'])
    fin_str = res['fin'].strftime('%d/%m/%Y %H:%M') if isinstance(res['fin'], datetime) else str(res['fin'])
    return f"""CONTRATO DE ALQUILER - JM ASOCIADOS
--------------------------------------------------------------
CLIENTE: {res['cliente']} | CI/RG: {res['ci']}
VEHÍCULO: {v['marca']} {v['nombre']} | PLACA: {v['placa']}
CHASIS: {v['chasis']} | COLOR: {v['color']}

ALQUILER DESDE: {ini_str}
ALQUILER HASTA: {fin_str}

TOTAL: R$ {res['total']}
--------------------------------------------------------------
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
st.title("JM ASOCIADOS | CORPORATIVO")
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f"""<div class="card-auto">
                <h3>{v['nombre']}</h3>
                <img src="{v['img']}" width="220">
                <p><b>R$ {v['precio']} / día</b></p>
                </div>""", unsafe_allow_html=True)
            
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller":
                    st.error("VEHÍCULO EN TALLER")
                else:
                    c1, c2 = st.columns(2)
                    dt_i = datetime.combine(c1.date_input("Inicio", key=f"fi_{v['nombre']}"), c1.time_input("Hora I", time(9,0), key=f"hi_{v['nombre']}"))
                    dt_f = datetime.combine(c2.date_input("Fin", key=f"ff_{v['nombre']}"), c2.time_input("Hora F", time(10,0), key=f"hf_{v['nombre']}"))
                    
                    c_n = st.text_input("Nombre", key=f"n_{v['nombre']}")
                    c_ci = st.text_input("Documento", key=f"ci_{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t_{v['nombre']}")
                    c_fir = st.text_input("Firma Digital", key=f"f_{v['nombre']}")
                    
                    dias = max(1, (dt_f - dt_i).days)
                    total = dias * v['precio']
                    
                    if c_n and c_ci and c_fir:
                        res_temp = {'cliente': c_n, 'ci': c_ci, 'domicilio': 'CDE', 'celular': c_tel, 'inicio': dt_i, 'fin': dt_f, 'total': total, 'firma': c_fir}
                        st.text_area("Previsualización:", obtener_texto_contrato(res_temp, v), height=150)
                        
                        st.markdown(f"**Monto: R$ {total} | PIX: 24510861818**")
                        foto = st.file_uploader("Comprobante", type=['jpg','png'], key=f"p_{v['nombre']}")
                        
                        if st.button("CONFIRMAR", key=f"btn_{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma) VALUES (?,?,?,?,?,?,?,?,?)",
                                        (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir))
                            conn.commit(); conn.close()
                            
                            # MENSAJE SOLICITADO
                            msg = (f"Hola JM, soy {c_n.upper()}.\n\n📄 Mis datos:\nDocumento/CPF: {c_ci}\n\n"
                                   f"🚗 Detalles del Alquiler:\nVehículo: {v['nombre']}\n"
                                   f"📅 Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n📅 Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                   f"💰 Monto Pagado: R$ {total}\n\nAquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!")
                            
                            url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        # Gestión Taller
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{f['nombre']}** ({f['estado']})")
            if c2.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # Descargas
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        for _, r in res_df.iterrows():
            with st.expander(f"ID {r['id']} - {r['cliente']}"):
                v_pdf = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 10, obtener_texto_contrato(r, v_pdf).encode('latin-1', 'replace').decode('latin-1'))
                st.download_button(f"Descargar PDF {r['cliente']}", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['id']}.pdf", key=f"dl_{r['id']}")
                if st.button("Eliminar", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
