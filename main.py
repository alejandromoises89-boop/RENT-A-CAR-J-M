import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
try:
    import styles
except:
    pass

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("""<style>
    .card-auto { background: #1e1e1e; padding: 20px; border-radius: 15px; border: 1px solid #D4AF37; margin-bottom: 20px; }
    .pix-box { background: #f0f2f6; color: black; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 10px 0; }
    </style>""", unsafe_allow_html=True)

# --- LÓGICA DE COTIZACIÓN ---
def obtener_cotizacion_real_guarani():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        data = requests.get(url, timeout=5).json()
        return round(data['rates']['PYG'], 0)
    except:
        return 1450.0

COTIZACION_DIA = obtener_cotizacion_real_guarani()
DB_NAME = 'jm_corporativo_permanente.db'

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, firma TEXT, domicilio TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT, chasis TEXT, anio TEXT, marca TEXT)')
    
    # Datos actualizados de los autos
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

# --- VALIDACIÓN DE DISPONIBILIDAD ---
def esta_disponible(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    flota_res = c.fetchone()
    if flota_res and flota_res[0] == "No Disponible":
        conn.close(); return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_inicio.isoformat(), t_fin.isoformat()))
    ocupado = c.fetchone()[0]
    conn.close(); return ocupado == 0

# --- TEXTO DEL CONTRATO LEGAL ---
def obtener_texto_contrato(res, v):
    dias = max(1, (res['fin'] - res['inicio']).days)
    total_gs = float(res['total']) * COTIZACION_DIA
    precio_dia_gs = total_gs / dias
    return f"""CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR
Entre: 
ARRENDADOR:
Nombre: J&M ASOCIADOS 
Cédula de Identidad: 1.702.076-0
Domicilio: CURUPAYTU ESQUINA FARID RAHAL
Teléfono: +595983635573
Y, ARRENDATARIO
Nombre: {res['cliente']}
Cédula de Identidad: RG/CPF. {res['ci']}
Domicilio: {res['domicilio']}
Teléfono: {res['celular']}

Se acuerda lo siguiente:
 PRIMERA - Objeto del Contrato.
El arrendador otorga en alquiler al arrendatario el siguiente vehículo:
* *Marca: {v['marca']}. 
* *Modelo: {v['nombre'].upper()}.
* *Año de fabricación: {v['anio']}.
* *Color: {v['color'].upper()}.
* *Número de chasis: {v['chasis']}.
* *Número de CHAPA: {v['placa']}.
* *Patente: {v['placa']}.

El vehículo se encuentra en perfecto estado de funcionamiento y libre de cargas o gravámenes. El arrendatario confirma la recepción del vehículo en buen estado, tras realizar una inspección visual y técnica con soporte Técnico VIDEO del Vehículo. El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. ------------------------------------------------------------------------------------

SEGUNDA - *Duración del Contrato
El presente contrato tendrá una duración de ( {dias} ) días, comenzando el {res['inicio'].strftime('%d/%m/%Y')} a las {res['inicio'].strftime('%H:%M')} hs y finalizando el {res['fin'].strftime('%d/%m/%Y')} a las {res['fin'].strftime('%H:%M')} hs. de entrega, salvo que se acuerde otra cosa por ambas partes mediante una extensión o terminación anticipada. ------------------------------------------------------

TERCERA - Precio y Forma de Pago
El arrendatario se compromete a pagar al arrendador la cantidad de {int(precio_dia_gs/1000)} mil guaraníes ({precio_dia_gs:,.0f}) por cada día de alquiler X DIÁS TOTAL DE: {total_gs:,.0f}Gs.------------------------------------------------------------
El pago se realizará de la siguiente manera:
 Forma de pago: En Transferencia Electrónica, El monto total será pagado por adelantado, en caso de exceder el tiempo se pagará a la entrega del vehículo lo excedido de acuerdo a lo que corresponda. ------------------------

CUARTA - Depósito de Seguridad.
El arrendatario pagara cinco millones de guaraníes (Gs. 5.000.000) en caso de siniestro (accidente) para cubrir los daños al vehículo durante el periodo de alquiler. --------------------------------------------------------------------------------------

 QUINTA - Condiciones de Uso del Vehículo.
1.	El vehículo será utilizado exclusivamente para fines personales dentro del territorio nacional. ---------------------------------------------------------------
2.	El ARRENDATARIO es responsable PENAL y CIVIL, de todo lo ocurrido dentro del vehículo y/o encontrado durante el alquiler. --------------------
3.	 El arrendatario se compromete a no subarrendar el vehículo ni permitir que terceros lo conduzcan sin autorización previa del arrendador. -----------------------------------------------------------------------------
4.	El uso del vehículo fuera de los límites del país deberá ser aprobado por el arrendador. ---------------------------------------------------------------------

SEXTA - Kilometraje y Excesos
El alquiler incluye un límite de 200 kilómetros por día. En caso de superar este límite, el arrendatario pagará 100.000 guaraníes adicionales por los kilómetros excedente. ------------------------------------------------------------------------  

 SÉPTIMA - Seguro.
•	El vehículo cuenta con un seguro básico que cubre---------------------------
•	Responsabilidad CIVIL en caso de daños a terceros. -------------------------
•	Cobertura en caso de accidentes. -------------------------------------------------
•	Servicio de rastreo satelital. --------------------------------------------------------
•	El arrendatario será responsable de los daños que no estén cubiertos por el seguro, tales como daños por negligencia o uso inapropiado del vehículo. ---------------------------------------------------------------------------------

 OCTAVA - Mantenimiento y Reparaciones
El arrendatario se compromete a mantener el vehículo en buen estado de funcionamiento. (Agua, combustible, limpieza) ---------------------------------------En caso de desperfectos técnicos o accidentes, el arrendatario deberá notificar inmediatamente al arrendador. ------------------------------------------------
Las reparaciones necesarias debido al desgaste normal del vehículo serán responsabilidad del arrendador, mientras que las reparaciones debido a uso indebido o negligente serán responsabilidad del arrendatario. --------------------

NOVENA - Devolución del Vehículo.
El arrendatario devolverá el vehículo en la misma condición en la que lo recibió, excepto por el desgaste normal. Si el vehículo no se devuelve en la fecha y hora acordada, el arrendatario pagará una penalización de media diaria y/o una diaria completa por cada día adicional. -------------------------------

DÉCIMA – Incumplimiento.
En caso de incumplimiento de alguna de las cláusulas de este contrato, el arrendador podrá rescindir el mismo de manera inmediata, sin perjuicio de reclamar daños y perjuicios. ----------------------------------------------------------------

UNDÉCIMA - Jurisdicción y Ley Aplicable.
Para cualquier disputa derivada de este contrato, las partes se someten a la jurisdicción de los tribunales del Alto Paraná, Paraguay, y se regirán por la legislación vigente en el país. ---------------------------------------------------------------

DÉCIMA SEGUNDA - Firma de las Partes.
Ambas partes firman el presente contrato en señal de conformidad, en Ciudad del este el {datetime.now().strftime('%d/%m/%Y')}. ----------------------------------------------------
El ARRENDADOR AUTORIZA AL ARRENDATARIO A CONDUCIR EL VEHÍCULO EN TODO EL TERRITORIO PARAGUAYO Y EL MERCOSUR. 

J&M ASOCIADOS                     FIRMA CLIENTE: {res['firma']}
R.U.C. 1.702.076-0                RG/CPF: {res['ci']}
Arrendador                        Arrendatario
"""

# --- INTERFAZ PRINCIPAL ---
st.markdown("<h1>J&M ASOCIADOS 🚗</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME)
    flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p><b>R$ {v['precio']} | Gs. {precio_gs:,.0f} por día</b></p></div>''', unsafe_allow_html=True)
            with st.expander(f"RESERVAR {v['nombre']}"):
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"di{v['nombre']}"), c1.time_input("Hora Inicio", time(9,0), key=f"hi{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"df{v['nombre']}"), c2.time_input("Hora Fin", time(10,0), key=f"hf{v['nombre']}"))
                
                if not esta_disponible(v['nombre'], dt_i, dt_f):
                    st.error("❌ El vehículo ya está reservado o bloqueado en esas fechas.")
                else:
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_ci = st.text_input("RG / CPF / CI", key=f"ci{v['nombre']}")
                    c_dom = st.text_input("Domicilio", key=f"dom{v['nombre']}")
                    c_w = st.text_input("Teléfono WhatsApp", key=f"w{v['nombre']}")
                    total = max(1, (dt_f - dt_i).days) * v['precio']
                    
                    if c_n and c_ci:
                        st.subheader("📄 PREVISUALIZACIÓN DEL CONTRATO")
                        res_prev = {'cliente':c_n, 'ci':c_ci, 'domicilio':c_dom, 'celular':c_w, 'inicio':dt_i, 'fin':dt_f, 'total':total, 'firma':'[PENDIENTE FIRMA]'}
                        st.text_area("Lea atentamente", obtener_texto_contrato(res_prev, v), height=250)
                        
                        firma = st.text_input("Escriba su Nombre para FIRMAR DIGITALMENTE", key=f"f{v['nombre']}")
                        
                        if firma:
                            st.markdown(f'<div class="pix-box"><b>Monto: R$ {total}</b><br>Llave PIX: 24510861818 (Marina Baez)</div>', unsafe_allow_html=True)
                            foto = st.file_uploader("Adjuntar Comprobante", type=['jpg', 'png'], key=f"foto{v['nombre']}")
                            
                            if st.button("CONFIRMAR RESERVA Y ENVIAR", key=f"btn{v['nombre']}"):
                                if foto:
                                    conn = sqlite3.connect(DB_NAME)
                                    conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, firma, domicilio) VALUES (?,?,?,?,?,?,?,?,?,?)", 
                                                 (c_n, c_ci, c_w, v['nombre'], dt_i, dt_f, total, foto.read(), firma, c_dom))
                                    conn.commit(); conn.close()
                                    st.success("¡Reserva procesada!")

                                    # BOTÓN WHATSAPP CON TU MENSAJE EXACTO
                                    msj_wa = (
                                        f"Hola JM, soy {c_n}.\n\n"
                                        f"📄 Mis datos:\nDocumento/CPF: {c_ci}\n\n"
                                        f"🚗 Detalles del Alquiler:\nVehículo: {v['nombre']}\n"
                                        f"🗓️ Desde: {dt_i.strftime('%d/%m/%Y %H:%M')}\n"
                                        f"🗓️ Hasta: {dt_f.strftime('%d/%m/%Y %H:%M')}\n\n"
                                        f"💰 Monto Pagado: R$ {total}\n\n"
                                        f"Aquí mi comprobante de pago. Favor confirmar recepción. ¡Muchas gracias!"
                                    )
                                    link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(msj_wa)}"
                                    st.markdown(f'<a href="{link_wa}" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">📲 ENVIAR COMPROBANTE POR WHATSAPP</div></a>', unsafe_allow_html=True)

with t_ubi:
    st.markdown('<h3>UBICACIÓN Y REDES</h3>', unsafe_allow_html=True)
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.3732450419316!2d-54.6133!3d-25.5133!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzQ3LjkiUyA1NMKwMzYnNDcuOSJX!5e0!3m2!1ses!2spy!4v1640000000000" width="100%" height="400" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
    st.markdown(f'<br><a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" target="_blank"><div style="background-color:#E1306C; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📸 VISITAR INSTAGRAM OFICIAL</div></a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Admin", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        
        # FINANZAS
        st.subheader("📊 BALANCE FINANCIERO")
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        c_f1, c_f2, c_f3 = st.columns(3)
        c_f1.metric("INGRESOS", f"R$ {ing:,.2f}")
        c_f2.metric("EGRESOS", f"R$ {egr:,.2f}")
        c_f3.metric("NETO", f"R$ {ing-egr:,.2f}")

        # GESTIÓN DE FLOTA Y BLOQUEO
        st.subheader("🛠️ GESTIÓN DE FLOTA (Bloquear/Desbloquear)")
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        for _, f in flota_adm.iterrows():
            ca, cb = st.columns([3,1])
            ca.write(f"{f['nombre']} - Estado: **{f['estado']}**")
            if cb.button("CAMBIAR ESTADO", key=f"st{f['nombre']}"):
                nuevo = "No Disponible" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre']))
                conn.commit(); st.rerun()

        # RESERVAS ACTIVAS
        st.subheader("📑 RESERVAS Y CONTRATOS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva {r['id']} - {r['cliente']}"):
                col_i, col_d = st.columns(2)
                if r['comprobante']: col_i.image(r['comprobante'], caption="Comprobante", width=250)
                v_res = pd.read_sql_query(f"SELECT * FROM flota WHERE nombre='{r['auto']}'", conn).iloc[0]
                
                # Función para generar PDF del contrato
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=8)
                pdf.multi_cell(0, 4, obtener_texto_contrato(r, v_res).encode('latin-1', 'replace').decode('latin-1'))
                
                col_d.download_button("📥 DESCARGAR CONTRATO PDF", pdf.output(dest='S').encode('latin-1'), f"Contrato_{r['cliente']}.pdf")
                if col_d.button("🗑️ ELIMINAR RESERVA", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()
