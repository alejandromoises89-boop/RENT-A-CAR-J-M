import streamlit as st
import sqlite3
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, date, timedelta, time
import urllib.parse
import calendar
import locale
import styles

# Intentar forzar español para que el calendario no use "Tue, Wed"
try:
    locale.setlocale(locale.LC_ALL, 'es_PY.UTF-8') # Específico de Paraguay
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        pass # Si el servidor no lo soporta, no rompe el programa

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JM ASOCIADOS",layout="wide",
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png")

try:
    st.markdown(styles.aplicar_estilo_premium(), unsafe_allow_html=True)
except:
    pass

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
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/rGJHxvbm/Tucson-sin-fondo.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/VpSpSJ9Q/voxy.png", "Disponible", "AAUG465", "Gris")
    ]
    for a in autos:
        c.execute("INSERT OR IGNORE INTO flota VALUES (?,?,?,?,?,?)", a)
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES DE VALIDACIÓN ---
def obtener_fechas_ocupadas(auto):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT inicio, fin FROM reservas WHERE auto = ?", conn, params=(auto,))
    conn.close()
    bloqueadas = set()
    for _, row in df.iterrows():
        try:
            start = pd.to_datetime(row['inicio']).date()
            end = pd.to_datetime(row['fin']).date()
            for i in range((end - start).days + 1): bloqueadas.add(start + timedelta(days=i))
        except: continue
    return bloqueadas

def esta_disponible(auto, t_ini, t_fin):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT estado FROM flota WHERE nombre=?", (auto,))
    res = c.fetchone()
    if res and res[0] == "En Taller": return False
    q = "SELECT COUNT(*) FROM reservas WHERE auto = ? AND NOT (fin <= ? OR inicio >= ?)"
    c.execute(q, (auto, t_ini.strftime('%Y-%m-%d %H:%M:%S'), t_fin.strftime('%Y-%m-%d %H:%M:%S')))
    disponible = c.fetchone()[0] == 0
    conn.close()
    return disponible

# --- INTERFAZ ---
st.markdown("<h1>JM ASOCIADOS</h1>", unsafe_allow_html=True)
t_res, t_ubi, t_adm = st.tabs(["📋 RESERVAS", "📍 UBICACIÓN", "🛡️ ADMINISTRADOR"])

with t_res:
    conn = sqlite3.connect(DB_NAME); flota = pd.read_sql_query("SELECT * FROM flota", conn); conn.close()
    cols = st.columns(2)
    for i, (_, v) in enumerate(flota.iterrows()):
        precio_gs = v['precio'] * COTIZACION_DIA
        with cols[i % 2]:
            st.markdown(f'''<div class="card-auto"><h3>{v["nombre"]}</h3><img src="{v["img"]}" width="100%"><p style="font-weight:bold; font-size:20px; color:#D4AF37; margin-bottom:2px;">R$ {v["precio"]} / día</p><p style="color:#28a745; margin-top:0px;">Gs. {precio_gs:,.0f} / día</p></div>''', unsafe_allow_html=True)
            
            with st.expander(f"Ver Disponibilidad"):
                # --- CALENDARIO TIPO AIRBNB (INTACTO) ---
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                meses_display = [
                    (date.today().month, date.today().year), 
                    ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)
                ]

                html_cal = """
                <style>
                    .airbnb-container { display: flex; flex-direction: row; gap: 25px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }
                    .airbnb-month { min-width: 200px; flex: 1; font-family: sans-serif; }
                    .airbnb-header { font-weight: 600; font-size: 15px; margin-bottom: 12px; color: white; text-transform: capitalize; }
                    .airbnb-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; text-align: center; }
                    .airbnb-day-name { font-size: 11px; color: #888; padding-bottom: 5px; }
                    .airbnb-cell { position: relative; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 500; color: white; }
                    .airbnb-raya { position: absolute; width: 100%; height: 2px; background-color: #ff385c; top: 50%; left: 0; z-index: 1; }
                    .airbnb-ocupado { color: #555 !important; }
                </style>
                <div class="airbnb-container">
                """
                for m, a in meses_display:
                    nombre_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][m-1]
                    html_cal += f'<div class="airbnb-month"><div class="airbnb-header">{nombre_mes} {a}</div><div class="airbnb-grid">'
                    for d_nom in ["L","M","M","J","V","S","D"]:
                        html_cal += f'<div class="airbnb-day-name">{d_nom}</div>'
                    for semana in calendar.monthcalendar(a, m):
                        for dia in semana:
                            if dia == 0: html_cal += '<div></div>'
                            else:
                                f_act = date(a, m, dia)
                                es_ocu = f_act in ocupadas
                                raya = '<div class="airbnb-raya"></div>' if es_ocu else ""
                                html_cal += f'<div class="airbnb-cell {"airbnb-ocupado" if es_ocu else ""}">{dia}{raya}</div>'
                    html_cal += '</div></div>'
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)

                st.divider()
                # --- DATOS DEL CLIENTE ---
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(10,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(12,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", placeholder="Ej: Guillerme Oliveira", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Cédula / RG", key=f"d{v['nombre']}")
                    c_w = st.text_input("Número de WhatsApp", key=f"w{v['nombre']}")
                    c_pais = st.text_input("País / Domicilio", key=f"p{v['nombre']}")
                    
                    dias = max(1, (dt_f.date() - dt_i.date()).days)
                    total_r = dias * v['precio']
                    total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        # Texto profesional y corregido
texto_legal = f"""CONTRATO DE LOCACIÓN DE VEHÍCULO - J&M ASOCIADOS

1. OBJETO: El Arrendador entrega al Arrendatario {nombre} el vehículo {auto} en perfecto estado de funcionamiento.
2. RESPONSABILIDAD: El Arrendatario asume la responsabilidad civil y penal por cualquier evento ocurrido durante la vigencia del contrato.
3. KILOMETRAJE: Se establece un límite de 200 km diarios. El excedente tendrá un costo de Gs. 100.000 por cada 10 km.
4. DEPÓSITO DE GARANTÍA: El Arrendatario acepta un compromiso de pago de Gs. 5.000.000 en caso de siniestro o daños.
5. TERRITORIO: El uso del vehículo está autorizado exclusivamente en territorio de Paraguay y países del MERCOSUR.
6. DOCUMENTACIÓN: El Arrendatario declara que los datos proporcionados (Doc/CPF: {cedula}) son verídicos.

--------------------------------------------------
ACEPTACIÓN DIGITAL:
Yo, {nombre}, con documento N° {cedula}, acepto los términos y condiciones del presente contrato de forma digital.
FECHA: {date.today().strftime('%d/%m/%Y')}
ID DE REGISTRO: JM-DIGITAL-CONFIRMED
--------------------------------------------------"""

# El scroll para el cliente
st.text_area("Lea atentamente el contrato antes de reservar:", value=texto_legal, height=300, disabled=True)

                        from streamlit_drawable_canvas import st_canvas
                        st.write("✍️ FIRME AQUÍ (Use su dedo):")
                        canvas_result = st_canvas(
                            stroke_width=3,
                            stroke_color="#000000",
                            background_color="#ffffff",
                            height=150,
                            width=300,
                            drawing_mode="freedraw",
                            key=f"canvas_{v['nombre']}",)

                        st.info(f"PAGO PIX: R$ {total_r} (Llave: 24510861818)")
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        
                        # EL BOTÓN DEBE ESTAR AQUÍ ADENTRO
                       if st.button("Reservar Ahora"):
            if nombre and cedula and celular:
                # --- NIVEL 3: TODO ESTO DEBE TENER MÁS SANGRÍA ---
                import urllib.parse
                
                texto_legal = f"""CONTRATO DE LOCACIÓN DE VEHÍCULO - J&M ASOCIADOS

1. OBJETO: El Arrendador entrega al Arrendatario Sr./Sra. {nombre} el vehículo {auto} en perfecto estado.
2. RESPONSABILIDAD: El Arrendatario asume la responsabilidad civil y penal por el uso del vehículo.
3. KILOMETRAJE: Límite de 200 km diarios. El excedente costará Gs. 100.000 por cada 10 km adicionales.
4. DEPÓSITO DE GARANTÍA: Se establece un compromiso de pago de Gs. 5.000.000 en caso de daños o siniestros.
5. TERRITORIO: El uso está autorizado exclusivamente en Paraguay y países del MERCOSUR.
6. VERACIDAD: El Arrendatario declara que su documento N° {cedula} es auténtico.

--------------------------------------------------
ACEPTACIÓN DIGITAL Y FIRMA:
Yo, {nombre}, con documento N° {cedula}, acepto los términos y condiciones del presente contrato de forma digital.
FECHA DE OPERACIÓN: {date.today().strftime('%d/%m/%Y')}
ID DE SEGURIDAD: JM-CONFIRMED-{cedula[-3:]}
--------------------------------------------------"""

                # Mostrar contrato
                st.subheader("📝 Contrato de Locación Generado")
                st.text_area("Documento de Aceptación:", value=texto_legal, height=300, disabled=True)
                
                # Procesar imagen
                img_byte = None
                if comprobante:
                    img_byte = comprobante.read()

                # Guardar en DB
                conn = sqlite3.connect(DB_NAME)
                conn.execute('''INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) 
                             VALUES (?,?,?,?,?,?,?,?)''', 
                             (nombre, cedula, celular, auto, fecha_i, fecha_f, total, img_byte))
                conn.commit()
                conn.close()
                
                # Link de WhatsApp
                texto_wa = f"Hola J&M ASOCIADOS, soy {nombre}.\nHe realizado una reserva y acepto el contrato digital.\n🚗 Vehículo: {auto}\n🗓️ Periodo: {fecha_i.strftime('%d/%m/%Y')} al {fecha_f.strftime('%d/%m/%Y')}\n💰 Total: R$ {total:.2f}\nDocumento: {cedula}"
                link_wa = f"https://wa.me/595991681191?text={urllib.parse.quote(texto_wa)}"
                
                # Botón de WhatsApp
                st.markdown(f'''
                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; font-size:18px; margin-top:20px;">
                            ✅ ENVIAR COMPROBANTE POR WHATSAPP
                        </div>
                    </a>
                ''', unsafe_allow_html=True)
                
                st.success(f"¡Reserva confirmada para {nombre}!")
                st.balloons()
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios.")
                
                # --- 4. PREPARAR Y MOSTRAR BOTÓN DE WHATSAPP ---
                import urllib.parse
                texto_wa = (
                    f"Hola J&M ASOCIADOS, soy {nombre}.\n"
                    f"He realizado una reserva y acepto el contrato digital.\n"
                    f"🚗 Vehículo: {auto}\n"
                    f"🗓️ Periodo: {fecha_i.strftime('%d/%m/%Y')} al {fecha_f.strftime('%d/%m/%Y')}\n"
                    f"💰 Total: R$ {total:.2f}\n"
                    f"Documento: {cedula}"
                )
                mensaje_encoded = urllib.parse.quote(texto_wa)
                link_wa = f"https://wa.me/595991681191?text={mensaje_encoded}"
                
                st.markdown(f'''
                    <a href="{link_wa}" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#25D366; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; font-size:18px; margin-top:20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
                            ✅ ENVIAR COMPROBANTE POR WHATSAPP
                        </div>
                    </a>
                ''', unsafe_allow_html=True)
                
                st.success(f"¡Reserva confirmada para {nombre}!")
                st.balloons()
            else:
                st.error("⚠️ Por favor, complete todos los campos obligatorios (Nombre, Documento y Celular).")
                    
# --- PESTAÑAS UBICACIÓN Y ADM (SIN CAMBIOS) ---
with t_ubi:
    st.markdown("<h3 style='text-align: center; color: #D4AF37;'>NUESTRA UBICACIÓN</h3>", unsafe_allow_html=True)
    st.markdown('<div style="border: 2px solid #D4AF37; border-radius: 15px; overflow: hidden;"><iframe width="100%" height="400" src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d57604.246417743!2d-54.67759567832031!3d-25.530374699999997!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94f68595fe36b1d1%3A0xce33cb9eeec10b1e!2sCiudad%20del%20Este!5e0!3m2!1ses!2spy!4v1709564821000!5m2!1ses!2spy"></iframe></div>', unsafe_allow_html=True)
    cs1, cs2 = st.columns(2)
    cs1.markdown('<a href="https://instagram.com/jm_asociados_consultoria" target="_blank"><div style="background: linear-gradient(45deg, #f09433, #bc1888); color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">📸 INSTAGRAM</div></a>', unsafe_allow_html=True)
    cs2.markdown('<a href="https://wa.me/595991681191" target="_blank"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">💬 WHATSAPP</div></a>', unsafe_allow_html=True)

with t_adm:
    if st.text_input("Clave de Acceso", type="password") == "8899":
        conn = sqlite3.connect(DB_NAME)
        res_df = pd.read_sql_query("SELECT * FROM reservas", conn)
        egr_df = pd.read_sql_query("SELECT * FROM egresos", conn)
        flota_adm = pd.read_sql_query("SELECT * FROM flota", conn)
        
        st.title("📊 PANEL DE CONTROL ESTRATÉGICO")

        # --- SECCIÓN 1: MÉTRICAS FINANCIERAS DUALES ---
        ing_r = res_df['total'].sum() if not res_df.empty else 0
        egr_r = egr_df['monto'].sum() if not egr_df.empty else 0
        util_r = ing_r - egr_r

        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.metric("INGRESOS TOTALES", f"R$ {ing_r:,.2f}")
            st.caption(f"Gs. {ing_r * COTIZACION_DIA:,.0f}")
        with c_m2:
            st.metric("GASTOS TOTALES", f"R$ {egr_r:,.2f}")
            st.caption(f"Gs. {egr_r * COTIZACION_DIA:,.0f}")
        with c_m3:
            st.metric("UTILIDAD NETA", f"R$ {util_r:,.2f}")
            st.caption(f"Gs. {util_r * COTIZACION_DIA:,.0f}")

        # --- SECCIÓN 2: GRÁFICOS Y REPORTES ---
        if not res_df.empty:
            st.subheader("📈 ANÁLISIS DE VENTAS")
            res_df['inicio_dt'] = pd.to_datetime(res_df['inicio'])
            df_plot = res_df.sort_values('inicio_dt')
            fig_l = px.line(df_plot, x='inicio_dt', y='total', color='auto', markers=True, title="Evolución R$")
            st.plotly_chart(fig_l, use_container_width=True)
            csv_data = df_plot.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Excel (CSV)", csv_data, "reporte_jm.csv", "text/csv")

        # --- SECCIÓN 3: AJUSTE DE PRECIOS POR DÍA ---
        st.subheader("💰 PRECIOS DE ALQUILER")
        with st.expander("Editar precios por día"):
            for _, f in flota_adm.iterrows():
                cp1, cp2 = st.columns([3, 1])
                cp1.write(f"*{f['nombre']}* ({f['placa']})")
                nuevo_p = cp2.number_input(f"R$/día", value=float(f['precio']), key=f"p_{f['nombre']}")
                if nuevo_p != f['precio']:
                    conn.execute("UPDATE flota SET precio=? WHERE nombre=?", (nuevo_p, f['nombre']))
                    conn.commit(); st.rerun()

        # --- SECCIÓN 4: DISPONIBILIDAD ---
        st.subheader("🛠️ ESTADO DE FLOTA")
        with st.expander("Gestionar Taller / Disponible"):
            for _, f in flota_adm.iterrows():
                ca1, ca2, ca3 = st.columns([2, 1, 1])
                ca1.write(f"*{f['nombre']}*")
                ca2.write("🟢 Disp." if f['estado'] == "Disponible" else "🔴 Taller")
                if ca3.button("CAMBIAR", key=f"s_{f['nombre']}"):
                    nuevo_est = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                    conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo_est, f['nombre']))
                    conn.commit(); st.rerun()

                        # --- SECCIÓN 6: REGISTRO Y PREVISUALIZACIÓN DE CONTRATO ---
        st.subheader("📑 RESERVAS Y PREVISUALIZACIÓN")
        
        with st.expander("📅 BLOQUEO MANUAL"):
            with st.form("f_man"):
                c_n = st.text_input("Cliente")
                c_d = st.text_input("DOC/CPF")
                c_a = st.selectbox("Auto", flota_adm['nombre'].tolist())
                fi = st.date_input("Inicio")
                ff = st.date_input("Fin")
                m_r = st.number_input("Monto R$")
                if st.form_submit_button("Bloquear"):
                    conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total) VALUES (?,?,?,?,?,?,?)",
                                 (f"[M] {c_n}", c_d, "000", c_a, fi, ff, m_r))
                    conn.commit()
                    st.rerun()

        # AQUÍ EMPIEZA EL BUCLE (Asegúrate que esté alineado con el 'with' de arriba)
                for _, r in res_df.iterrows():
            unique_key = f"res_{r['id']}_{r['cliente'][:3]}"
            
            with st.expander(f"Reserva #{r['id']} - {r['cliente']} (DOC: {r['ci']})"):
                
                # Redacción corregida y formal del contrato
                contrato_final = f"""CONTRATO DE ALQUILER - J&M ASOCIADOS
========================================
DATOS DEL ARRENDATARIO:
CLIENTE: {r['cliente']}
DOCUMENTO/CPF: {r['ci']}
VEHÍCULO: {r['auto']}
FECHAS: Desde {r['inicio']} hasta {r['fin']}
MONTO TOTAL: R$ {r['total']} (Gs. {r['total']*COTIZACION_DIA:,.0f})

CLÁUSULAS CONTRACTUALES:
1. ESTADO DEL VEHÍCULO: Se entrega en óptimas condiciones de uso y limpieza.
2. RESPONSABILIDAD LEGAL: El cliente es el único responsable civil y penal por el uso del vehículo.
3. LÍMITE DE USO: 200 km por día. El excedente se cobrará a Gs. 100.000 por fracción.
4. SEGURO Y DAÑOS: Cobertura con deducible de Gs. 5.000.000 a cargo del arrendatario.
5. TERRITORIALIDAD: Autorizado para circular en Paraguay y países del MERCOSUR.
6. DEVOLUCIÓN: El vehículo debe devolverse en el mismo estado en que fue recibido.

----------------------------------------
FIRMA Y ACEPTACIÓN DIGITAL:
Este documento ha sido aceptado digitalmente por el cliente {r['cliente']} 
con número de documento {r['ci']} en la fecha de reserva.

ID DE TRANSACCIÓN: JM-{r['id']}
FECHA DE EMISIÓN: {date.today().strftime('%d/%m/%Y')}
----------------------------------------
Firmado en Ciudad del Este, Paraguay."""

                # Mostrar el contrato corregido en pantalla
                st.code(contrato_final, language="markdown")
                
                # Botón de descarga con el mismo texto corregido
                st.download_button(
                    label=f"📥 Descargar Contrato PDF/TXT #{r['id']}", 
                    data=contrato_final, 
                    file_name=f"Contrato_JM_{r['cliente']}.txt",
                    key=f"dl_{unique_key}"
                )
                
                if r['comprobante']: 
                    st.image(r['comprobante'], width=250, caption="Comprobante adjunto")
                
                if st.button("🗑️ Eliminar Registro", key=f"del_{unique_key}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()
