import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse

# --- 1. CONFIGURACIÓN Y ESTÉTICA (COLORES ANTERIORES) ---
st.set_page_config(page_title="JM ALQUILER DE VEHÍCULOS", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #4A0404 0%, #2B0202 100%); color: #D4AF37; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #000000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; width: 100%; }
    .card-auto { background-color: rgba(0,0,0,0.4); padding: 20px; border-left: 4px solid #D4AF37; border-radius: 10px; margin-bottom: 20px; text-align: center; }
    .btn-contact { display: block; width: 100%; padding: 12px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; border: 1px solid #D4AF37; }
    .wa { background-color: #25D366; color: white !important; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. BASE DE DATOS PROFESIONAL ---
DB_NAME = 'jm_corporativo_v11.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, correo TEXT PRIMARY KEY, password TEXT, celular TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, tipo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT)') # Estado: 'Disponible' o 'Taller'
    
    autos_iniciales = [
        ("Hyundai Tucson", 260.0, "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/", "Disponible"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible"),
        ("Toyota Vitz Negro", 195.0, "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png", "Disponible"),
        ("Toyota Voxy", 240.0, "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png", "Disponible")
    ]
    for a in autos_iniciales:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- 3. LÓGICA DE BLOQUEO Y DISPONIBILIDAD ---
def verificar_disponibilidad(auto, t_inicio, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 1. Verificar si el auto está en el taller
    estado = c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,)).fetchone()[0]
    if estado == "Taller":
        conn.close()
        return False, "El vehículo se encuentra actualmente en mantenimiento (Taller)."
    
    # 2. Verificar si hay reservas en esas fechas
    query = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(query, (auto, t_inicio, t_fin))
    ocupado = c.fetchone()[0]
    conn.close()
    if ocupado > 0:
        return False, "El vehículo ya está reservado para las fechas seleccionadas."
    return True, ""

# --- 4. CONTROL DE SESIÓN ---
if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'u_nombre' not in st.session_state: st.session_state.u_nombre = ""
if 'pagina' not in st.session_state: st.session_state.pagina = "login"

# --- 5. INTERFAZ DE ACCESO ---
if not st.session_state.logueado:
    if st.session_state.pagina == "login":
        st.markdown("<h1 style='text-align:center;'>JM ALQUILER</h1>", unsafe_allow_html=True)
        u_correo = st.text_input("Correo")
        u_pass = st.text_input("Contraseña", type="password")
        if st.button("INGRESAR"):
            if u_correo == "admin@jm.com" and u_pass == "8899":
                st.session_state.logueado, st.session_state.u_nombre = True, "admin"
                st.rerun()
            else:
                conn = sqlite3.connect(DB_NAME)
                res = conn.execute("SELECT nombre FROM usuarios WHERE correo=? AND password=?", (u_correo, u_pass)).fetchone()
                conn.close()
                if res:
                    st.session_state.logueado, st.session_state.u_nombre = True, res[0]
                    st.rerun()
                else: st.error("Datos incorrectos")
        if st.button("Crear Cuenta Nueva"):
            st.session_state.pagina = "registro"; st.rerun()

    elif st.session_state.pagina == "registro":
        st.title("Registro de Cliente")
        with st.form("reg"):
            n = st.text_input("Nombre Completo"); e = st.text_input("Correo"); p = st.text_input("Contraseña", type="password"); c = st.text_input("Celular")
            if st.form_submit_button("Registrar y Guardar"):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n, e, p, c))
                    conn.commit(); conn.close()
                    st.success("¡Registrado! Ya puede iniciar sesión."); st.session_state.pagina = "login"
                except: st.error("El correo ya existe.")
        if st.button("Volver"): st.session_state.pagina = "login"; st.rerun()

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    tabs = st.tabs(["🚗 Flota y Reservas", "📍 Ubicación", "🛡️ Panel Máster"])

    with tabs[0]:
        st.write(f"Sesión activa: {st.session_state.u_nombre}")
        conn = sqlite3.connect(DB_NAME)
        flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
        
        for _, v in flota.iterrows():
            with st.container():
                # Mostrar si está en taller de forma visual
                taller_msg = "⚠️ EN TALLER" if v['estado'] == "Taller" else "✅ DISPONIBLE"
                st.markdown(f'''<div class="card-auto">
                    <h3>{v["nombre"]}</h3>
                    <p>{taller_msg}</p>
                    <img src="{v["img"]}" width="250">
                </div>''', unsafe_allow_html=True)
                
                with st.expander(f"RESERVAR {v['nombre']}"):
                    c1, c2 = st.columns(2)
                    d1 = c1.date_input("Entrega", key=f"d1{v['nombre']}")
                    h1 = c1.time_input("Hora Entrega", time(9,0), key=f"h1{v['nombre']}")
                    d2 = c2.date_input("Devolución", key=f"d2{v['nombre']}")
                    h2 = c2.time_input("Hora Devolución", time(9,0), key=f"h2{v['nombre']}")
                    
                    dt1, dt2 = datetime.combine(d1, h1), datetime.combine(d2, h2)

                    if st.button(f"Confirmar Alquiler {v['nombre']}"):
                        disponible, msg_error = verificar_disponibilidad(v['nombre'], dt1, dt2)
                        if disponible:
                            total = max(1, (dt2-dt1).days) * v['precio']
                            conn = sqlite3.connect(DB_NAME)
                            conn.execute("INSERT INTO reservas (cliente, auto, inicio, fin, total, tipo) VALUES (?,?,?,?,?,?)",
                                         (st.session_state.u_nombre, v['nombre'], dt1, dt2, total, 'Ingreso'))
                            conn.commit(); conn.close()
                            
                            st.success("✅ Reserva bloqueada con éxito.")
                            
                            # WhatsApp Empresarial
                            texto = (f"*JM ASOCIADOS - SALUDO EMPRESARIAL*\n\n"
                                     f"Estimado/a {st.session_state.u_nombre}, un placer saludarle.\n"
                                     f"Su reserva ha sido procesada correctamente:\n"
                                     f"🚗 Auto: {v['nombre']}\n"
                                     f"📅 Periodo: {dt1.strftime('%d/%m/%y %H:%M')} al {dt2.strftime('%d/%m/%y %H:%M')}\n"
                                     f"💰 Importe: R$ {total}\n\n"
                                     f"🔑 *LLAVE PIX:* 24510861818\n\n"
                                     f"Por favor, adjunte su comprobante aquí mismo para la entrega del vehículo.")
                            st.markdown(f'<a href="https://wa.me/595991681191?text={urllib.parse.quote(texto)}" class="btn-contact wa">📲 ENVIAR COMPROBANTE AL 0991681191</a>', unsafe_allow_html=True)
                        else:
                            st.error(msg_error)

    with tabs[1]:
        st.subheader("Ubicación y Contacto")
        st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d14402.34863391702!2d-54.6366032!3d-25.5188371!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f69083e5f8f4ed%3A0x336570e64fc7f1b6!2sJ%26M%20ASOCIADOS%20Consultoria!5e0!3m2!1ses!2spy!4v1704480000000!5m2!1ses!2spy" width="100%" height="450" style="border:1px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://www.instagram.com/jm_asociados_consultoria?igsh=djBzYno0MmViYzBo" class="btn-contact">📸 Ver Instagram Oficial</a>', unsafe_allow_html=True)

    with tabs[2]:
        if st.session_state.u_nombre == "admin":
            st.title("🛡️ PANEL DE CONTROL Y FINANZAS")
            
            # --- FINANZAS ---
            conn = sqlite3.connect(DB_NAME)
            df_r = pd.read_sql_query("SELECT * FROM reservas", conn)
            
            c1, c2, c3 = st.columns(3)
            total_in = df_r[df_r['tipo'] == 'Ingreso']['total'].sum()
            c1.metric("Ingresos Totales", f"R$ {total_in:,.2f}")
            c2.metric("Total Reservas", len(df_r))
            
            # Gráfica de Ingresos
            if not df_r.empty:
                fig = px.bar(df_r, x='auto', y='total', color='auto', title="Ingresos por Vehículo", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Gestión de Flota (Taller)")
            for idx, row in flota.iterrows():
                col_n, col_acc = st.columns([3, 1])
                col_n.write(f"**{row['nombre']}** - Estado actual: {row['estado']}")
                nuevo_estado = "Disponible" if row['estado'] == "Taller" else "Taller"
                if col_acc.button(f"Mover a {nuevo_estado}", key=f"st_{row['nombre']}"):
                    conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo_estado, row['nombre']))
                    conn.commit(); st.rerun()

            st.divider()
            pin_borrar = st.text_input("PIN para limpiar datos", type="password")
            if st.button("🚨 LIMPIAR TODAS LAS RESERVAS"):
                if pin_borrar == "0000":
                    conn.execute("DELETE FROM reservas")
                    conn.commit(); st.success("Datos borrados"); st.rerun()
                else: st.error("PIN incorrecto")
            
            st.markdown("### Exportar Datos")
            csv = df_r.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Excel/CSV", data=csv, file_name="finanzas_jm.csv", mime="text/csv")
            conn.close()
        else:
            st.warning("Acceso exclusivo para administradores.")
