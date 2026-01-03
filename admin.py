import streamlit as st
import pandas as pd
import sqlite3
import os

def panel_control():
    st.markdown('<div style="color:black;">', unsafe_allow_html=True)
    st.title("⚙️ Panel de Control - J&M")
    
    conn = sqlite3.connect('jm_asociados.db')
    df = pd.read_sql_query("SELECT * FROM reservas", conn)
    
    st.subheader("Análisis Financiero Diario")
    st.dataframe(df)

    st.subheader("Análisis FODA / Presentación")
    st.info("Fortalezas: Flota nueva | Debilidades: Alta demanda")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Exportar Estadísticas (Excel)"):
            if not os.path.exists('Estadisticas'): os.makedirs('Estadisticas')
            df.to_excel("Estadisticas/Reporte_Finanzas.xlsx", index=False)
            st.success("Guardado en carpeta /Estadisticas")
            
    with col2:
        st.download_button("📥 Descargar Reporte PDF", data="Contenido PDF...", file_name="Reporte_FODA_JM.pdf")
    
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)
