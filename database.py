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
        {"id": "TUC", "nombre": "Hyundai Tucson", "color": "Blanco", import sqlite3
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
        {"id": "TUC", "nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260,  "img": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400"},
        {"id": "VITZW", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195, "img": "https://images.unsplash.com/photo-1619682817481-e994891cd1f5?w=400"},
        {"id": "VITZB", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195, "img": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400"},
        {"id": "VOXYG", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240, "img": "https://images.unsplash.com/photo-1517524008697-84bbe3c3fd98?w=400"}
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
    conn.close() "img": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400"},
        {"id": "VITZW", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://images.unsplash.com/photo-1619682817481-e994891cd1f5?w=400"},
        {"id": "VITZB", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400"},
        {"id": "VOXYG", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://images.unsplash.com/photo-1517524008697-84bbe3c3fd98?w=400"}
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
