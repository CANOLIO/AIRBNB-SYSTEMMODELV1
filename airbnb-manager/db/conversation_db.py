# db/conversation_db.py
import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib


def init_conversation_db():
    """Inicializa la base de datos de conversaciones"""
    db_path = Path("data/conversations.db")
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    # Tabla de conversaciones con estructura semántica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            asunto TEXT NOT NULL,
            remitente TEXT NOT NULL,
            nombre_cliente TEXT,
            propiedad TEXT,
            propiedad_id INTEGER,
            check_in DATE,
            check_out DATE,
            numero_huespedes INTEGER,
            correo_cliente TEXT,
            telefono_cliente TEXT,
            confirmacion TEXT,  -- "sí", "no", o NULL
            estado TEXT DEFAULT 'en_progreso',  -- en_progreso, confirmada, cancelada
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de mensajes para historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            message_id INTEGER,
            sender TEXT,
            subject TEXT,
            body TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_type TEXT,
            processed BOOLEAN DEFAULT 0,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos de conversaciones inicializada")


def get_conversation_id(remitente, asunto):
    """Genera ID único para conversación basado en remitente y asunto"""
    # Limpiar asunto de prefijos comunes
    import re
    clean_subject = re.sub(r'^(re|fw|fwd):\s*', '', asunto.lower().strip())
    conversation_key = f"{remitente.lower()}|{clean_subject}"
    return hashlib.md5(conversation_key.encode()).hexdigest()[:12]


def create_or_update_conversation(remitente, asunto):
    """Crea o actualiza una conversación"""
    conversation_id = get_conversation_id(remitente, asunto)

    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    # Verificar si ya existe
    cursor.execute('SELECT id FROM conversations WHERE id = ?', (conversation_id,))
    exists = cursor.fetchone()

    if exists:
        # Actualizar timestamp
        cursor.execute('''
            UPDATE conversations 
            SET updated_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), conversation_id))
    else:
        # Crear nueva conversación
        cursor.execute('''
            INSERT INTO conversations (id, asunto, remitente)
            VALUES (?, ?, ?)
        ''', (conversation_id, asunto, remitente))

    conn.commit()
    conn.close()
    return conversation_id


def get_conversation(conversation_id):
    """Obtiene una conversación completa"""
    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
    result = cursor.fetchone()

    if result:
        # Convertir a diccionario
        columns = [description[0] for description in cursor.description]
        conversation = dict(zip(columns, result))
        conn.close()
        return conversation

    conn.close()
    return None


def update_conversation_field(conversation_id, field, value):
    """Actualiza un campo específico de la conversación"""
    allowed_fields = [
        'nombre_cliente', 'propiedad', 'propiedad_id', 'check_in', 'check_out',
        'numero_huespedes', 'correo_cliente', 'telefono_cliente', 'confirmacion', 'estado'
    ]

    if field not in allowed_fields:
        raise ValueError(f"Campo no válido: {field}")

    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    cursor.execute(f'''
        UPDATE conversations 
        SET {field} = ?, updated_at = ?
        WHERE id = ?
    ''', (value, datetime.now().isoformat(), conversation_id))

    conn.commit()
    conn.close()


def get_missing_fields(conversation_id):
    """Obtiene los campos que faltan en una conversación"""
    conversation = get_conversation(conversation_id)
    if not conversation:
        return [
            'nombre_cliente', 'propiedad', 'check_in', 'check_out',
            'numero_huespedes', 'correo_cliente'
        ]

    faltantes = []

    if not conversation.get('nombre_cliente'):
        faltantes.append('nombre_cliente')

    if not conversation.get('propiedad'):
        faltantes.append('propiedad')

    if not conversation.get('check_in'):
        faltantes.append('check_in')

    if not conversation.get('check_out'):
        faltantes.append('check_out')

    if not conversation.get('numero_huespedes'):
        faltantes.append('numero_huespedes')

    if not conversation.get('correo_cliente'):
        faltantes.append('correo_cliente')

    return faltantes


def is_confirmed(conversation_id):
    """Verifica si la conversación ya está confirmada"""
    conversation = get_conversation(conversation_id)
    if conversation:
        return conversation.get('confirmacion') == 'sí'
    return False


def add_message_to_conversation(conversation_id, message_data):
    """Agrega un mensaje a la conversación"""
    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO conversation_messages 
        (conversation_id, message_id, sender, subject, body, message_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        conversation_id,
        message_data.get('message_id'),
        message_data.get('sender'),
        message_data.get('subject'),
        message_data.get('body'),
        message_data.get('message_type', 'desconocido')
    ))

    conn.commit()
    conn.close()


def get_conversation_messages(conversation_id):
    """Obtiene todos los mensajes de una conversación"""
    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sender, subject, body, received_at, message_type
        FROM conversation_messages 
        WHERE conversation_id = ?
        ORDER BY received_at
    ''', (conversation_id,))

    messages = cursor.fetchall()
    conn.close()
    return messages


# Inicializar base de datos al importar
init_conversation_db()