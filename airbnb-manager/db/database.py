# db/database.py
import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()

    # Crear tabla de propiedades con estructura básica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT NOT NULL,
            capacidad INTEGER NOT NULL,
            precio_noche REAL DEFAULT 0
        )
    ''')

    # Actualizar tabla de propiedades para agregar nuevas columnas (si no existen)
    try:
        cursor.execute("ALTER TABLE propiedades ADD COLUMN sector TEXT")
    except sqlite3.OperationalError:
        pass  # Columna ya existe

    try:
        cursor.execute("ALTER TABLE propiedades ADD COLUMN ciudad TEXT DEFAULT 'Valdivia'")
    except sqlite3.OperationalError:
        pass  # Columna ya existe

    # Tabla de reservas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            propiedad_id INTEGER,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            huesped TEXT NOT NULL,
            correo TEXT,
            telefono TEXT,
            estado TEXT DEFAULT 'pendiente',
            precio_total REAL,
            FOREIGN KEY(propiedad_id) REFERENCES propiedades(id)
        )
    ''')

    # Tabla de mensajes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remitente TEXT,
            asunto TEXT,
            cuerpo TEXT,
            fecha_recibido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            respondido BOOLEAN DEFAULT 0,
            respuesta TEXT,
            motivo_no_respuesta TEXT
        )
    ''')

    conn.commit()
    conn.close()


def agregar_propiedad(nombre, direccion, capacidad, precio_noche=0, sector=None, ciudad='Valdivia'):
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO propiedades (nombre, direccion, capacidad, precio_noche, sector, ciudad) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, direccion, capacidad, precio_noche, sector, ciudad))
    conn.commit()
    propiedad_id = cursor.lastrowid
    conn.close()
    return propiedad_id


def obtener_propiedades():
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM propiedades")
    data = cursor.fetchall()
    conn.close()
    return data


def obtener_propiedad_por_id(propiedad_id):
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM propiedades WHERE id = ?", (propiedad_id,))
    data = cursor.fetchone()
    conn.close()
    return data


def verificar_disponibilidad(propiedad_id, fecha_inicio, fecha_fin):
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM reservas
        WHERE propiedad_id = ? 
        AND estado IN ('confirmada', 'pendiente')
        AND NOT (fecha_fin < ? OR fecha_inicio > ?)
    ''', (propiedad_id, fecha_inicio, fecha_fin))
    data = cursor.fetchall()
    conn.close()
    return len(data) == 0


def crear_reserva(propiedad_id, fecha_inicio, fecha_fin, huesped, correo=None, telefono=None):
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()

    # Calcular precio total
    cursor.execute("SELECT precio_noche FROM propiedades WHERE id = ?", (propiedad_id,))
    precio_noche = cursor.fetchone()[0]

    from datetime import datetime
    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    noches = (fin - inicio).days
    precio_total = noches * precio_noche if precio_noche else 0

    cursor.execute("""
        INSERT INTO reservas 
        (propiedad_id, fecha_inicio, fecha_fin, huesped, correo, telefono, precio_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (propiedad_id, fecha_inicio, fecha_fin, huesped, correo, telefono, precio_total))

    reserva_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reserva_id


def obtener_reservas():
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.nombre as propiedad_nombre 
        FROM reservas r 
        JOIN propiedades p ON r.propiedad_id = p.id
        ORDER BY r.fecha_inicio DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def obtener_calendario_ocupacion():
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre, r.fecha_inicio, r.fecha_fin, r.huesped, r.estado
        FROM reservas r
        JOIN propiedades p ON r.propiedad_id = p.id
        WHERE r.estado IN ('confirmada', 'pendiente')
        ORDER BY r.fecha_inicio
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def guardar_mensaje(remitente, asunto, cuerpo):
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mensajes (remitente, asunto, cuerpo)
        VALUES (?, ?, ?)
    """, (remitente, asunto, cuerpo))
    mensaje_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mensaje_id


def obtener_mensajes_no_respondidos():
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mensajes 
        WHERE respondido = 0 
        ORDER BY fecha_recibido DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def obtener_mensajes_que_requieren_atencion():
    """Obtiene mensajes que requieren atención humana"""
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mensajes 
        WHERE respondido = 0 AND motivo_no_respuesta IS NOT NULL
        ORDER BY fecha_recibido DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def marcar_mensaje_respondido(mensaje_id, respuesta, motivo_no_respuesta=None):
    """Marca mensaje como respondido con opción de motivo"""
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    if motivo_no_respuesta:
        cursor.execute("""
            UPDATE mensajes 
            SET respondido = 1, respuesta = ?, motivo_no_respuesta = ?
            WHERE id = ?
        """, (respuesta, motivo_no_respuesta, mensaje_id))
    else:
        cursor.execute("""
            UPDATE mensajes 
            SET respondido = 1, respuesta = ?
            WHERE id = ?
        """, (respuesta, mensaje_id))
    conn.commit()
    conn.close()


def buscar_propiedades_por_criterios(capacidad_min=None, sector=None, ciudad=None):
    """Busca propiedades según criterios"""
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()

    query = "SELECT * FROM propiedades WHERE 1=1"
    params = []

    if capacidad_min:
        query += " AND capacidad >= ?"
        params.append(capacidad_min)

    if sector:
        query += " AND sector LIKE ?"
        params.append(f"%{sector}%")

    if ciudad:
        query += " AND ciudad LIKE ?"
        params.append(f"%{ciudad}%")

    query += " ORDER BY capacidad"

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data


# Asegúrate de tener este método en db/database.py

def crear_reserva_con_detalles(propiedad_id, fecha_inicio, fecha_fin, huesped, correo=None, telefono=None,
                               estado='confirmada'):
    """Crea una reserva con estado específico"""
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()

    # Calcular precio total
    cursor.execute("SELECT precio_noche FROM propiedades WHERE id = ?", (propiedad_id,))
    precio_noche_row = cursor.fetchone()
    precio_noche = precio_noche_row[0] if precio_noche_row else 0

    if precio_noche:
        from datetime import datetime
        try:
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            noches = (fin - inicio).days
            precio_total = noches * precio_noche if noches > 0 else 0
        except:
            precio_total = 0
    else:
        precio_total = 0

    cursor.execute("""
        INSERT INTO reservas 
        (propiedad_id, fecha_inicio, fecha_fin, huesped, correo, telefono, estado, precio_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (propiedad_id, fecha_inicio, fecha_fin, huesped, correo, telefono, estado, precio_total))

    reserva_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reserva_id

def obtener_ultima_respuesta_sistema():
    """Obtiene la última respuesta enviada por el sistema"""
    conn = sqlite3.connect('data/reservas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mensajes 
        WHERE respuesta IS NOT NULL 
        ORDER BY fecha_recibido DESC 
        LIMIT 1
    """)
    data = cursor.fetchone()
    conn.close()
    return data