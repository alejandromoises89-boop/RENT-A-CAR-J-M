import streamlit as st
import sqlite3
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="JM ASOCIADOS", layout="wide", page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

DB_NAME = 'jm_corporativo_permanente.db'

# --- TEXTO LEGAL DEL CONTRATO ---
def obtener_texto_contrato(res, v):
    # Aseguramos formato de fechas para el texto
    ini_str = res['inicio'].strftime('%d/%m/%Y %H:%M') if isinstance(res['inicio'], datetime) else str(res['inicio'])
    fin_str = res['fin'].strftime('%d/%m/%Y %H:%M') if isinstance(res['fin'], datetime) else str(res['fin'])
    
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO - JM ASOCIADOS
--------------------------------------------------------------
ARRENDADOR: JM ASOCIADOS (RUC 1.702.076-0)
ARRENDATARIO: {res['cliente']} | CI/RG: {res['ci']}
DOMICILIO: {res['domicilio']} | TEL: {res['celular']}

DETALLES DEL VEHÍCULO:
MARCA: {v['marca']} | MODELO: {v['nombre'].upper()}
AÑO: {v['anio']} | COLOR: {v['color'].upper()}
CHASIS: {v['chasis']} | PLACA: {v['placa']}

DURACIÓN Y ENTREGA:
FECHA/HORA RECOGIDA: {ini_str}
FECHA/HORA DEVOLUCIÓN: {fin_str}

MONTO TOTAL DE LA OPERACIÓN: R$ {res['total']}
--------------------------------------------------------------
* El arrendatario se hace responsable civil y penalmente del vehículo.
* El ARRENDADOR autoriza la conducción en Paraguay y MERCOSUR.
* El vehículo debe ser devuelto en las mismas condiciones.

FIRMA DEL CLIENTE: {res['firma']}
FECHA DE EMISIÓN: {datetime.now().strftime('%d/%m/%Y')}
"""

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    # RESTAURACIÓN DE LA FLOTA COMPLETA
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
st.title("JM ASOCIADOS | SISTEMA DE GESTIÓN")
t_res, t_adm = st.tabs(["📋 RESERVAS", "🛡️ PANEL ADMINISTRATIVO"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f"### {v['nombre']}")
            st.image(v['img'], width=250)
            st.write(f"**Precio:** R$ {v['precio']} / día")
            
            with st.expander(f"RESERVAR {v['nombre']}"):
                if v['estado'] == "Taller":
                    st.error("⚠️ Este vehículo no está disponible (EN TALLER).")
                else:
                    c1, c2 = st.columns(2)
                    f_i = c1.date_input("Fecha Inicio", key=f"fi_{v['nombre']}")
                    h_i = c1.time_input("Hora Inicio", time(9,0), key=f"hi_{v['nombre']}")
                    f_f = c2.date_input("Fecha Fin", key=f"ff_{v['nombre']}")
                    h_f = c2.time_input("Hora Fin", time(10,0), key=f"hf_{v['nombre']}")
                    
                    c_n = st.text_input("Nombre Completo", key=f"n_{v['nombre']}")
                    c_ci = st.text_input("Documento (CI/CPF)", key=f"ci_{v['nombre']}")
                    c_tel = st.text_input("WhatsApp", key=f"t_{v['nombre']}")
                    c_dom = st.text_input("Domicilio", key=f"d_{v['nombre']}")
                    c_fir = st.text_input("Firma Digital (Escriba su nombre)", key=f"f_{v['nombre']}")
                    
                    dt_i = datetime.combine(f_i, h_i)
                    dt_f = datetime.combine(f_f, h_f)
                    total = max(1, (f_f - f_i).days) * v['precio']
                    
                    # PREVISUALIZACIÓN AUTOMÁTICA
                    if c_n and c_ci and c_fir:
                        res_temp = {'cliente': c_n, 'ci': c_ci, 'domicilio': c_dom, 'celular': c_tel, 'inicio': dt_i, 'fin': dt_f, 'total': total, 'firma': c_fir}
                        st.subheader("📝 Previsualización del Contrato")
                        txt_pre = obtener_texto_contrato(res_temp, v)
                        st.text_area("Verifique sus datos:", txt_pre, height=200)
                        
                        st.success(f"Monto a pagar vía PIX: R$ {total}")
                        st.code("Llave PIX: 24510861818", language="text")
                        
                        foto = st.file_uploader("Subir Comprobante de Pago", type=['jpg','png','jpeg'], key=f"p_{v['nombre']}")
                        
                        if st.button("CONFIRMAR Y FINALIZAR", key=f"btn_{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                        (c_n, c_ci, c_tel, v['nombre'], dt_i.isoformat(), dt_f.isoformat(), total, foto.read(), c_fir, c_dom))
                            conn.commit(); conn.close()
                            
                            # MENSAJE DE WHATSAPP
                            msg = (f"Hola JM, soy {c_n.upper()}.\n\n"
                                   f"📄 Mis datos:\nDocumento/CPF: {c_ci}\n\n"
                                   f"🚗 Detalles:\nVehículo: {v['nombre']}\n"
                                   f"📅 Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                   f"📅 Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                   f"💰 Monto Pagado: R$ {total}\n\n"
                                   f"Envío mi comprobante adjunto. ¡Gracias!")
                            
                            url_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msg)}"
                            st.markdown(f'<a href="{url_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR COMPROBANTE AL CORPORATIVO</a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Acceso Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        
        # GESTIÓN DE ESTADO (TALLER / DISPONIBLE)
        st.subheader("🛠️ ESTADO DE LA FLOTA")
        f_adm = pd.read_sql_query("SELECT nombre, estado FROM flota", conn)
        for _, f in f_adm.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{f['nombre']}** | Estado: {f['estado']}")
            if c2.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # DESCARGA Y ELIMINACIÓN DE RESERVAS
        st.subheader("📥 GESTIÓN DE RESERVAS Y CONTRATOS")
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        
        for _, r in res_df.iterrows():
            with st.expander(f"ID {r['id']} | {r['cliente']} - {r['auto']}"):
                # Obtener datos del auto para este contrato
                v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                
                # Crear el PDF para descarga
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                txt_pdf = obtener_texto_contrato(r, v_res)
                pdf.multi_cell(0, 8, txt_pdf.encode('latin-1', 'replace').decode('latin-1'))
                
                c_d1, c_d2 = st.columns(2)
                c_d1.download_button(
                    label=f"📥 Descargar PDF {r['cliente']}",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name=f"Contrato_{r['cliente']}.pdf",
                    mime="application/pdf",
                    key=f"dl_{r['id']}"
                )
                
                if c_d2.button("🗑️ Borrar Reserva", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        
        conn.close()
