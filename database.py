import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL)''')
    conn.commit()
    conn.close()

def obtener_flota():
    return [
        {"id": "TUCSON_W", "nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
        {"id": "VITZ_W", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://a0.anyrgb.com/pngimg/1498/1242/2014-toyota-yaris-hatchback-2014-toyota-yaris-2018-toyota-yaris-toyota-yaris-yaris-toyota-vitz-fuel-economy-in-automobiles-hybrid-vehicle-frontwheel-drive-minivan.png"},
        {"id": "VITZ_N", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
        {"id": "VOXY_G", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
    ]

def verificar_disponibilidad(auto_id, inicio, fin):
    conn = sqlite3.connect('jm_asociados.db')
    query = f"SELECT * FROM reservas WHERE auto='{auto_id}' AND NOT (fin < '{inicio}' OR inicio > '{fin}')"
    res = pd.read_sql_query(query, conn)
    conn.close()
    return res.empty

def guardar_reserva(cliente, auto, inicio, fin, monto):
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cliente, auto, inicio, fin, monto) VALUES (?,?,?,?,?)",
              (cliente, auto, str(inicio), str(fin), monto))
    conn.commit()
    conn.close()
