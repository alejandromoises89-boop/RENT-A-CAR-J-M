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
    page_icon="https://i.ibb.co/PzsvxYrM/JM-Asociados-Logotipo-02.png" 
)

# Intentar aplicar los estilos premium si el archivo existe
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

# --- NUEVO CSS PARA CALENDARIO FIJO (REEMPLAZAR EN EL BLOQUE DE STYLE) ---
st.markdown("""
    <style>
    .cal-header { 
        font-size: 16px; font-weight: bold; text-align: center; 
        margin: 15px 0 5px 0; color: #333;
    }
    /* Contenedor que obliga a 7 columnas siempre */
    .cal-grid-fijo { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 0px; 
        max-width: 320px; 
        margin: 0 auto; /* Centra el calendario */
        border: 0.2px solid #eee;
    }
    .cal-box-fijo { 
        aspect-ratio: 1/1; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 12px; 
        position: relative; 
        background: white; 
        color: #222;
        border: 0.1px solid #f7f7f7;
    }
    .cal-day-name-fijo {
        text-align: center;
        font-size: 10px;
        color: #717171;
        font-weight: bold;
        padding-bottom: 5px;
    }
    .ocupado { color: #ccc !important; background-color: #fafafa; }
    .raya-roja-h { 
        position: absolute; width: 80%; height: 1.5px; 
        background-color: #ff385c; z-index: 1; top: 50%;
    }
    </style>
""", unsafe_allow_html=True)

# --- DENTRO DEL EXPANDER DE RESERVAS (REEMPLAZAR LA LÓGICA DEL CALENDARIO) ---
with st.expander(f"Ver Disponibilidad"):
    ocupadas = obtener_fechas_ocupadas(v['nombre'])
    hoy = date.today()
    meses = [(hoy.month, hoy.year), ((hoy.month % 12) + 1, hoy.year if hoy.month < 12 else hoy.year + 1)]
    
    # Creamos dos columnas en PC, pero dentro usamos el Grid Fijo para los días
    col_izq, col_der = st.columns(2)
    
    for idx, (m, a) in enumerate(meses):
        target_col = col_izq if idx == 0 else col_der
        with target_col:
            st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
            
            # Encabezado de días L M M J V S D
            dias_html = "".join([f'<div class="cal-day-name-fijo">{d}</div>' for d in ["L","M","M","J","V","S","D"]])
            
            # Generar los cuadros de los días
            cal_data = calendar.monthcalendar(a, m)
            dias_grid_html = ""
            for semana in cal_data:
                for dia in semana:
                    if dia == 0:
                        dias_grid_html += '<div class="cal-box-fijo" style="background:transparent; border:none;"></div>'
                    else:
                        f_act = date(a, m, dia)
                        es_ocu = f_act in ocupadas
                        clase = "cal-box-fijo ocupado" if es_ocu else "cal-box-fijo"
                        raya = '<div class="raya-roja-h"></div>' if es_ocu else ""
                        dias_grid_html += f'<div class="{clase}">{dia}{raya}</div>'
            
            # Renderizamos todo el mes en un solo bloque HTML
            st.markdown(f"""
                <div class="cal-grid-fijo">
                    {dias_html}
                    {dias_grid_html}
                </div>
            """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reservas (id INTEGER PRIMARY KEY, cliente TEXT, ci TEXT, celular TEXT, auto TEXT, inicio TIMESTAMP, fin TIMESTAMP, total REAL, comprobante BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS egresos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, fecha DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (nombre TEXT PRIMARY KEY, precio REAL, img TEXT, estado TEXT, placa TEXT, color TEXT)')
    
    # Inserción de flota inicial con la Tucson sin fondo
    autos = [
        ("Hyundai Tucson Blanco", 260.0, "https://i.ibb.co/7J0m4yH/tucson-png.png", "Disponible", "AAVI502", "Blanco"),
        ("Toyota Vitz Blanco", 195.0, "https://i.ibb.co/Y7ZHY8kX/pngegg.png", "Disponible", "AAVP719", "Blanco"),
        ("Toyota Vitz Negro", 195.0, "https://i.ibb.co/rKFwJNZg/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel.png", "Disponible", "AAOR725", "Negro"),
        ("Toyota Voxy Gris", 240.0, "https://i.ibb.co/7hYR0RC/BG160258-2427f0-Photoroom-1.png", "Disponible", "AAUG465", "Gris")
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
    if c.fetchone()[0] == "En Taller": return False
    # Evitar solapamiento de fechas
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
                ocupadas = obtener_fechas_ocupadas(v['nombre'])
                # CALENDARIO AIRBNB HORIZONTAL
                c_m1, c_m2 = st.columns(2)
                meses = [(date.today().month, date.today().year), ((date.today().month % 12) + 1, date.today().year if date.today().month < 12 else date.today().year + 1)]
                
                for idx, (m, a) in enumerate(meses):
                    with [c_m1, c_m2][idx]:
                        st.markdown(f'<div class="cal-header">{calendar.month_name[m]} {a}</div>', unsafe_allow_html=True)
                        cd = st.columns(7)
                        for d_n in ["L","M","M","J","V","S","D"]: cd[["L","M","M","J","V","S","D"].index(d_n)].markdown(f'<div class="cal-day-name">{d_n}</div>', unsafe_allow_html=True)
                        
                        cal_data = calendar.monthcalendar(a, m)
                        for semana in cal_data:
                            cdi = st.columns(7)
                            for d_idx, dia in enumerate(semana):
                                if dia != 0:
                                    f_act = date(a, m, dia)
                                    es_ocu = f_act in ocupadas
                                    style = "ocupado" if es_ocu else ""
                                    raya = '<div class="raya-roja-h"></div>' if es_ocu else ""
                                    cdi[d_idx].markdown(f'<div class="cal-box {style}">{dia}{raya}</div>', unsafe_allow_html=True)
                
                st.divider()
                # FORMULARIO
                c1, c2 = st.columns(2)
                dt_i = datetime.combine(c1.date_input("Inicio", key=f"d1{v['nombre']}"), c1.time_input("Hora 1", time(9,0), key=f"h1{v['nombre']}"))
                dt_f = datetime.combine(c2.date_input("Fin", key=f"d2{v['nombre']}"), c2.time_input("Hora 2", time(10,0), key=f"h2{v['nombre']}"))
                
                if esta_disponible(v['nombre'], dt_i, dt_f):
                    c_n = st.text_input("Nombre Completo", key=f"n{v['nombre']}")
                    c_d = st.text_input("CI / Documento", key=f"d{v['nombre']}")
                    c_w = st.text_input("WhatsApp", key=f"w{v['nombre']}")
                    dias = max(1, (dt_f - dt_i).days); total_r = dias * v['precio']; total_gs = total_r * COTIZACION_DIA
                    
                    if c_n and c_d and c_w:
                        st.markdown(f'<div style="background-color:#2b0606; color:#f1f1f1; padding:20px; border:1px solid #D4AF37; border-radius:10px; height:250px; overflow-y:scroll; font-size:13px;"><b>CONTRATO JM ASOCIADOS</b><br>Arrendatario: {c_n.upper()}<br>Vehículo: {v["nombre"]}<br>Total: Gs. {total_gs:,.0f}<br><br>Al confirmar, usted acepta todos los términos y condiciones de uso y responsabilidad civil/penal.</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="pix-box"><b>PAGO PIX: R$ {total_r}</b><br>Llave: 24510861818<br>Marina Baez</div>', unsafe_allow_html=True)
                        foto = st.file_uploader("Adjuntar Comprobante", key=f"f{v['nombre']}")
                        if st.button("CONFIRMAR RESERVA", key=f"btn{v['nombre']}") and foto:
                            conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO reservas (cliente, ci, celular, auto, inicio, fin, total, comprobante) VALUES (?,?,?,?,?,?,?,?)", (c_n, c_d, c_w, v['nombre'], dt_i, dt_f, total_r, foto.read())); conn.commit(); conn.close()
                            st.success("¡Reserva Guardada!"); st.rerun()
                else:
                    st.error("No disponible en esas fechas.")

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
        ing = res_df['total'].sum() if not res_df.empty else 0
        egr = egr_df['monto'].sum() if not egr_df.empty else 0
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("INGRESOS TOTALES", f"R$ {ing:,.2f}")
        c_m2.metric("GASTOS", f"R$ {egr:,.2f}")
        c_m3.metric("UTILIDAD NETA", f"R$ {ing - egr:,.2f}")

        cg1, cg2 = st.columns(2)
        with cg1:
            if not res_df.empty:
                fig1 = px.pie(res_df, values='total', names='auto', hole=0.4, color_discrete_sequence=['#D4AF37', '#B8860B', '#FFD700'])
                st.plotly_chart(fig1, use_container_width=True)
        with cg2:
            fig2 = px.bar(x=["Ingresos", "Gastos"], y=[ing, egr], color=["Ingresos", "Gastos"], color_discrete_map={"Ingresos": "#D4AF37", "Gastos": "#800020"})
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("💸 CARGAR GASTO"):
            with st.form("g"):
                c_g = st.text_input("Concepto"); m_g = st.number_input("Monto R$")
                if st.form_submit_button("Guardar"):
                    conn.execute("INSERT INTO egresos (concepto, monto, fecha) VALUES (?,?,?)", (c_g, m_g, date.today())); conn.commit(); st.rerun()

        st.subheader("🛠️ ESTADO DE FLOTA")
        for _, f in flota_adm.iterrows():
            ca1, ca2, ca3 = st.columns([2,1,1])
            ca1.write(f"**{f['nombre']}** ({f['placa']})")
            ca2.write("🟢 Disponible" if f['estado'] == "Disponible" else "🔴 Taller")
            if ca3.button("CAMBIAR", key=f"sw_{f['nombre']}"):
                nuevo = "En Taller" if f['estado'] == "Disponible" else "Disponible"
                conn.execute("UPDATE flota SET estado=? WHERE nombre=?", (nuevo, f['nombre'])); conn.commit(); st.rerun()

        st.subheader("📑 REGISTRO DE RESERVAS")
        for _, r in res_df.iterrows():
            with st.expander(f"Reserva #{r['id']} - {r['cliente']}"):
                st.write(f"Auto: {r['auto']} | Periodo: {r['inicio']} al {r['fin']} | Total: R$ {r['total']}")
                if r['comprobante']: st.image(r['comprobante'], width=200)
                if st.button("🗑️ BORRAR", key=f"del{r['id']}"):
                    conn.execute("DELETE FROM reservas WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()