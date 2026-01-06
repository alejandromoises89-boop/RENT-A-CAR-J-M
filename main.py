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
    </style>
    """, unsafe_allow_html=True)

DB_NAME = 'jm_corporativo_permanente.db'

# --- LÓGICA DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    # Datos iniciales de la flota
    autos = [
        ("Hyundai Tucson", 260.0, "https://i.ibb.co/23tKv88L/Whats-App-Image-2026-01-06-at-14-12-35-1.png", "Disponible", "AAVI502", "Gris", "KMHJU81VBAU040691", "2010", "HYUNDAI"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco", "NSP1352032141", "2015", "TOYOTA"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro", "NSP1302097964", "2012", "TOYOTA"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris", "ZRR700415383", "2011", "TOYOTA")
    ]
    for a in autos:
        # Usamos INSERT IGNORE o similar para no sobreescribir el estado 'Taller' si ya existe
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE SOPORTE ---
def esta_disponible(auto_nombre, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 1. Verificar si el admin lo puso en Taller
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto_nombre,))
    res_estado = c.fetchone()
    if res_estado and res_estado[0] == "Taller":
        conn.close()
        return False, "⚠️ VEHÍCULO EN TALLER / MANTENIMIENTO"
    
    # 2. Verificar si hay choques de fechas con otras reservas
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto_nombre, t_inicio.isoformat(), t_fin.isoformat()))
    ocupado = c.fetchone()[0]
    conn.close()
    if ocupado > 0:
        return False, "❌ YA RESERVADO EN ESAS FECHAS"
    return True, ""

def obtener_texto_contrato(res, v):
    # Asegurar que las fechas sean objetos datetime
    ini = datetime.fromisoformat(res['inicio']) if isinstance(res['inicio'], str) else res['inicio']
    fin = datetime.fromisoformat(res['fin']) if isinstance(res['fin'], str) else res['fin']
    return f"CONTRATO JM ASOCIADOS\nCliente: {res['cliente']}\nAuto: {v['nombre']}\nDesde: {ini}\nHasta: {fin}\nFirma: {res['firma']}"

# --- INTERFAZ ---
st.title("JM ASOCIADOS | SISTEMA 2026")
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ ADMIN"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn)
    conn.close()
    
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="180"><p><b>{v["estado"]}</b></p></div>', unsafe_allow_html=True)
            
            with st.expander(f"RESERVAR {v['nombre']}"):
                c1, c2 = st.columns(2)
                f_i = c1.date_input("Inicio", key=f"fi_{v['nombre']}")
                h_i = c1.time_input("Hora", time(9,0), key=f"hi_{v['nombre']}")
                f_f = c2.date_input("Fin", key=f"ff_{v['nombre']}")
                h_f = c2.time_input("Hora", time(10,0), key=f"hf_{v['nombre']}")
                
                dt_i, dt_f = datetime.combine(f_i, h_i), datetime.combine(f_f, h_f)
                
                # VALIDACIÓN DE ESTADO REAL
                disponible, motivo = esta_disponible(v['nombre'], dt_i, dt_f)
                
                if not disponible:
                    st.error(motivo)
                else:
                    st.success("✅ Disponible")
                    nombre = st.text_input("Nombre", key=f"n_{v['nombre']}")
                    ci = st.text_input("Documento", key=f"ci_{v['nombre']}")
                    firma = st.text_input("Firma Digital", key=f"f_{v['nombre']}")
                    foto = st.file_uploader("Comprobante PIX", type=['jpg','png'], key=f"p_{v['nombre']}")
                    
                    if st.button("CONFIRMAR RESERVA", key=f"b_{v['nombre']}") and foto:
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("INSERT INTO reservas (cliente, ci, auto, inicio, fin, total, comprobante, firma) VALUES (?,?,?,?,?,?,?,?)",
                                    (nombre, ci, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), v['precio'], foto.read(), firma))
                        conn.commit()
                        conn.close()
                        
                        # WHATSAPP
                        msg = f"Hola JM, soy {nombre}.\nVehículo: {v['nombre']}\nDesde: {dt_i}\nHasta: {dt_f}\nComprobante adjunto."
                        st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(msg)}" target="_blank" class="whatsapp-btn">📲 ENVIAR A WHATSAPP</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Password", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        st.subheader("🛠️ GESTIÓN DE FLOTA (BLOQUEO TALLER)")
        # Forzar lectura fresca de la DB
        flota_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        
        for _, f in flota_adm.iterrows():
            c1, c2 = st.columns([3, 1])
            color_estado = "🔴" if f['estado'] == "Taller" else "🟢"
            c1.write(f"{color_estado} **{f['nombre']}** - Actualmente: {f['estado']}")
            
            # El secreto es usar el nombre del auto en la clave del botón y disparar rerun
            if c2.button(f"CAMBIAR A {'DISPONIBLE' if f['estado'] == 'Taller' else 'TALLER'}", key=f"btn_flip_{f['nombre']}"):
                nuevo_estado = "Disponible" if f['estado'] == "Taller" else "Taller"
                conn.execute("UPDATE flota SET estado = ? WHERE nombre = ?", (nuevo_estado, f['nombre']))
                conn.commit()
                conn.close() # Cerrar antes de recargar
                st.rerun() # RECARGA LA PÁGINA PARA MOSTRAR EL CAMBIO

        st.divider()
        st.subheader("📑 ELIMINAR REGISTROS")
        
        # Eliminar Reservas
        res_df = pd.read_sql_query("SELECT id, cliente, auto FROM reservas", conn)
        for _, r in res_df.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"Reserva {r['id']}: {r['cliente']} ({r['auto']})")
            if col2.button("Borrar", key=f"del_res_{r['id']}"):
                conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                conn.commit(); conn.close(); st.rerun()
        
        conn.close()
