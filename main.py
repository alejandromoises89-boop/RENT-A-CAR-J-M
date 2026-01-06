import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
from fpdf import FPDF
import urllib.parse
import styles

# 1. Datos exactos de tu flota
FLOTA = {
    "Hyundai Tucson": {"chasis": "KMHJU81VBAU040691", "año": "2010", "color": "BLANCO", "chapa": "AAVI502"},
    "Toyota Vitz Blanco": {"chasis": "NSP1352032141", "año": "2015", "color": "PERLA", "chapa": "PROV-VITZ-B"},
    "Toyota Vitz Negro": {"chasis": "NSP1302097964", "año": "2012", "color": "NEGRO", "chapa": "PROV-VITZ-N"},
    "Toyota Voxy": {"chasis": "ZRR700415383", "año": "2011", "color": "GRIS", "chapa": "PROV-VOXY"}
}

if 'paso_app' not in st.session_state:
    st.session_state.paso_app = 'edicion'

# --- INTERFAZ DE ENTRADA ---
if st.session_state.paso_app == 'edicion':
    st.subheader("🛠️ Configuración de Reserva")
    with st.form("form_reserva"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Cliente")
            cedula = st.text_input("Cédula / RG / CPF")
            auto = st.selectbox("Vehículo", list(FLOTA.keys()))
        with col2:
            f_inicio = st.date_input("Fecha Inicio")
            h_inicio = st.time_input("Hora Inicio")
            total_dias = st.number_input("Total de Días", min_value=1)
            precio = st.number_input("Precio por Día (Gs.)", value=250000)

        if st.form_submit_button("Generar Previsualización del Contrato"):
            st.session_state.datos = {
                "n": nombre, "c": cedula, "auto": auto, "dias": total_dias,
                "f_i": f_inicio, "h_i": h_inicio, "p": precio, "t": total_dias * precio,
                "chasis": FLOTA[auto]['chasis'], "año": FLOTA[auto]['año'], "color": FLOTA[auto]['color']
            }
            st.session_state.paso_app = 'preview'
            st.rerun()

# --- VISTA PREVIA DEL CONTRATO (SIN TOCAR NI UNA COMA) ---
elif st.session_state.paso_app == 'preview':
    d = st.session_state.datos
    
    st.info("🔎 Previsualización: Verifique que no falte ningún dato antes de pagar.")

    # El cuadro de texto del contrato
    with st.container(border=True):
        st.markdown(f"""
        ### CONTRATO DE ALQUILER DE VEHÍCULO Y AUTORIZACIÓN PARA CONDUCIR
        **ARRENDADOR:** JM ASOCIADOS | R.U.C. 1.702.076-0 | Tel: +595983635573  
        **ARRENDATARIO:** {d['n']} | Cédula/RG: {d['c']}
        
        ---
        **PRIMERA - Objeto del Contrato.** El arrendador otorga en alquiler:
        * Marca/Modelo: {d['auto'].upper()}
        * Año: {d['anio']} | Color: {d['color']}
        * Chasis: **{d['chasis']}**
        
        **SEGUNDA - Duración.** {d['dias']} días, iniciando el {d['f_i']} a las {d['h_i']} hs.
        
        **TERCERA - Pago.** {d['p']:,} Gs. por día. **TOTAL: {d['t']:,} Gs.**
        
        [... El resto de tus cláusulas legales aquí ...]
        
        **DÉCIMA SEGUNDA - Firma.** Ciudad del Este, {datetime.now().strftime('%d/%m/%Y')}.
        """)
        
        # Simulación visual de las firmas al final
        c1, c2 = st.columns(2)
        c1.write("__________________________")
        c1.write("JM ASOCIADOS (Arrendador)")
        c2.write("__________________________")
        c2.write(f"{d['n']} (Arrendatario)")

    # Acciones finales
    firma_digital = st.text_input("ESCRIBA SU NOMBRE PARA FIRMAR")
    
    col_acc1, col_acc2 = st.columns(2)
    if col_acc1.button("⬅️ Editar Datos"):
        st.session_state.paso_app = 'edicion'
        st.rerun()
        
    if col_acc2.button("💳 PROCEDER AL PAGO", type="primary"):
        if firma_digital.lower() == d['n'].lower():
            st.success("Redirigiendo a la pasarela de pago...")
        else:
            st.error("La firma debe coincidir con el nombre del cliente.")
