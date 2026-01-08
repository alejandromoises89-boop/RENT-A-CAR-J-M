import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import styles

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="JM ASOCIADOS",
    layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

# Aplicación de Estilo Premium
try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: white; }
        .card-auto { border: 1px solid #D4AF37; padding: 20px; border-radius: 15px; background: #1a1c23; margin-bottom: 20px; }
        .stButton>button { background-color: #D4AF37; color: black; font-weight: bold; border-radius: 10px; }
        .stExpander { border: 1px solid #333 !important; border-radius: 10px; background: #1a1c23; }
        </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE NEGOCIO ---
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
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, ci TEXT, celular TEXT, 
                 auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB, contrato_firmado TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/cK92Y5Hf/tucson-Photoroom.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES AUXILIARES ---
def obtener_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    dias = set()
    for _, row in df.iterrows():
        start, end = pd.to_datetime(row['inicio']).date(), pd.to_datetime(row['fin']).date()
        for i in range((end - start).days + 1): dias.add(start + timedelta(days=i))
    return dias

def verificar_disponibilidad(auto, t_i, t_f):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    if c.fetchone()[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_i.strftime('%Y-%m-%d %H:%M:%S'), t_f.strftime('%Y-%m-%d %H:%M:%S')))
    res = c.fetchone()[0] == 0
    conn.close()
    return res

# --- INTERFAZ PRINCIPAL ---
st.markdown("<h1 style='text-align:center; color:#D4AF37;'>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto">
                <h3 style="color:#D4AF37;">{v["nombre"]}</h3>
                <img src="{v["img"]}" width="100%" style="border-radius:10px;">
                <p style="font-size:22px; font-weight:bold; margin-top:10px;">R$ {v["precio"]} / día</p>
                <p style="color:#28a745;">Gs. {v["precio"]*COTIZACION_DIA:,.0f} / día</p>
            </div>''', unsafe_allow_html=True)
            
            with st.expander("RESERVAR Y VER CONTRATO"):
                # Calendario Estilo Airbnb
                ocupadas = obtener_ocupadas(v['nombre'])
                st.write("📅 **Disponibilidad:**")
                c_cal1, c_cal2 = st.columns(2)
                d_i = c_cal1.date_input("Fecha Inicio", key=f"di_{v['nombre']}")
                d_f = c_cal2.date_input("Fecha Fin", key=f"df_{v['nombre']}")
                dt_i, dt_f = datetime.combine(d_i, time(10,0)), datetime.combine(d_f, time(12,0))

                if verificar_disponibilidad(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre y Apellido", key=f"n_{v['nombre']}")
                    c_ci = st.text_input("Cédula / RG / CPF", key=f"ci_{v['nombre']}")
                    c_wa = st.text_input("WhatsApp (con código de país)", key=f"wa_{v['nombre']}")
                    
                    dias_total = max(1, (d_f - d_i).days)
                    precio_total_r = dias_total * v['precio']
                    
                    if c_n and c_ci:
                        # --- CONTRATO DE 12 CLÁUSULAS ---
                        texto_contrato = f"""CONTRATO DE LOCACIÓN DE VEHÍCULO - JM ASOCIADOS
--------------------------------------------------
ARRENDADOR: JM ASOCIADOS
ARRENDATARIO: {c_n.upper()} | DOC: {c_ci}
VEHÍCULO: {v['nombre']} | PLACA: {v['placa']}
PERIODO: {d_i} al {d_f} ({dias_total} días)
VALOR TOTAL: R$ {precio_total_r}

CLÁUSULAS LEGALES:
1. OBJETO: El Arrendador cede el uso del vehículo en perfecto estado.
2. RESPONSABILIDAD: El Arrendatario asume responsabilidad civil y penal total.
3. KILOMETRAJE: Límite de 200km diarios. Excedente: Gs. 10.000 por km.
4. ÁMBITO: Autorizado para circular en Paraguay y MERCOSUR.
5. SINIESTROS: En caso de accidente, el deducible es de Gs. 5.000.000.
6. MULTAS: Cualquier infracción durante el periodo es cargo del cliente.
7. COMBUSTIBLE: Se entrega y recibe con el mismo nivel.
8. PROHIBICIONES: No se permite subarrendar ni conductores no declarados.
9. LIMPIEZA: El vehículo debe devolverse en condiciones óptimas de higiene.
10. MANTENIMIENTO: El Arrendador cubre fallas mecánicas propias del uso.
11. MORA: La demora en la entrega generará multas por hora extra.
12. JURISDICCIÓN: Tribunales de Ciudad del Este, Paraguay.

FIRMA DIGITAL: Aceptado mediante validación electrónica JM-{c_ci[-3:]}
FECHA DE FIRMA: {date.today()}"""
                        
                        st.markdown(f'<div style="background:#f0f0f0; color:#222; padding:15px; border-radius:10px; height:250px; overflow-y:scroll; font-family:monospace; font-size:12px; border:2px solid #D4AF37;">{texto_contrato.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                        
                        acepto = st.checkbox("HE LEÍDO, ACEPTO LAS 12 CLÁUSULAS Y FIRMO EL CONTRATO", key=f"chk_{v['nombre']}")
                        
                        st.info(f"💳 PAGO VIA PIX: R$ {precio_total_r} | Llave: 24510861818")
                        comprobante = st.file_uploader("Adjuntar Comprobante de Pago", type=['jpg', 'png', 'pdf'], key=f"file_{v['nombre']}")
                        
                        if st.button("CONFIRMAR RESERVA Y ENVIAR", key=f"btn_{v['nombre']}", disabled=not acepto):
                            if comprobante:
                                conn = sqlite3.connect(DB_NAME)
                                conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante, contrato_firmado) VALUES (?,?,?,?,?,?,?,?,?)",
                                             (c_n, c_ci, c_wa, v['nombre'], dt_i, dt_f, precio_total_r, comprobante.read(), texto_contrato))
                                conn.commit(); conn.close()
                                
                                # WhatsApp con mensaje profesional completo
                                wa_msg = f"Hola JM ASOCIADOS! Soy {c_n}.\nConfirmó la reserva del {v['nombre']}.\n✅ He leído y FIRMADO el contrato de 12 cláusulas.\n💰 Total: R$ {precio_total_r}\n🗓️ Periodo: {d_i} al {d_f}.\nAdjunto mi comprobante de pago."
                                wa_url = f"https://wa.me/595991681191?text={urllib.parse.quote(wa_msg)}"
                                st.markdown(f'<a href="{wa_url}" target="_blank" style="background:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">✅ ENVIAR COMPROBANTE POR WHATSAPP</a>', unsafe_allow_html=True)
                                st.success("¡Reserva procesada con éxito!")
                            else:
                                st.error("Por favor, suba la foto del comprobante.")
                else:
                    st.error("Vehículo no disponible en estas fechas o se encuentra en taller.")

with t_ubi:
    st.markdown("<h3 style='text-align:center;'>Nuestra Base en Ciudad del Este</h3>", unsafe_allow_html=True)
    st.markdown('<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3601.447551408846!2d-54.6111!3d-25.51!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjXCsDMwJzM2LjAiUyA1NMKwMzYnNDAuMCJX!5e0!3m2!1ses!2spy!4v1625680000000!5m2!1ses!2spy" width="100%" height="450" style="border:2px solid #D4AF37; border-radius:15px;"></iframe>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave Maestra", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        # Dashboard Financiero
        st.title("📊 PANEL ESTRATÉGICO")
        c1, c2, c3 = st.columns(3)
        total_ing = res_df['total'].sum() if not res_df.empty else 0
        total_egr = egr_df['monto'].sum() if not egr_df.empty else 0
        c1.metric("INGRESOS (R$)", f"{total_ing:,.2f}", f"Gs. {total_ing*COTIZACION_DIA:,.0f}")
        c2.metric("GASTOS (R$)", f"{total_egr:,.2f}")
        c3.metric("UTILIDAD", f"R$ {total_ing - total_egr:,.2f}")

        # Gráfico Plotly
        if not res_df.empty:
            res_df['f_inicio'] = pd.to_datetime(res_df['inicio']).dt.date
            fig = px.bar(res_df.groupby('f_inicio')['total'].sum().reset_index(), x='f_inicio', y='total', title="Ventas Diarias", color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("📥 Descargar Reporte CSV", res_df.to_csv(index=False), "reporte_jm.csv")

        st.divider()
        
        # Gestión de Flota Uniforme
        st.subheader("🚗 GESTIÓN DE VEHÍCULOS")
        for _, f in flota_adm.iterrows():
            with st.container():
                col_x, col_y, col_z = st.columns([2,1,1])
                col_x.write(f"**{f['nombre']}** ({f['placa']})")
                new_price = col_y.number_input("Precio R$", value=float(f['precio']), key=f"p_adm_{f['nombre']}")
                if col_z.button(f"{'🔴 TALLER' if f['estado']=='Disponible' else '🟢 HABILITAR'}", key=f"btn_st_{f['nombre']}"):
                    conn.execute("UPDATE flota SET estado=?, precio=? WHERE nombre=?", 
                                 ("En Taller" if f['estado']=="Disponible" else "Disponible", new_price, f['nombre']))
                    conn.commit(); st.rerun()

        st.divider()

        # Visualización de Contratos y Comprobantes
        st.subheader("📑 REGISTRO DE CONTRATOS FIRMADOS")
        for _, r in res_df.iterrows():
            with st.expander(f"RESERVA #{r['id']} - {r['cliente']}"):
                st.write(f"**Auto:** {r['auto']} | **Periodo:** {r['inicio']} al {r['fin']}")
                
                # Visualizar Contrato con Firma
                if st.button("VER CONTRATO FIRMADO", key=f"v_con_{r['id']}"):
                    st.text_area("Contrato Legal:", r['contrato_firmado'], height=200)
                    st.download_button("📥 Descargar Contrato Legal", r['contrato_firmado'], f"Contrato_{r['cliente']}.txt")
                
                # Comprobante
                if r['comprobante']:
                    st.image(r['comprobante'], caption="Comprobante de Pago (PIX)", width=350)
                
                if st.button("BORRAR RESERVA", key=f"del_{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
