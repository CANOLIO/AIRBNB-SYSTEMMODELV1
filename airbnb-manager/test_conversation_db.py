# test_conversation_db.py
from db.conversation_db import *


def test_nueva_estructura():
    """Prueba la nueva estructura de base de datos"""
    print("=== PRUEBA DE NUEVA ESTRUCTURA ===")

    # Crear una conversación de prueba
    conversation_id = "test123"
    asunto = "Reserva Depa Isla Teja"

    # Crear conversación
    create_or_update_conversation(conversation_id, asunto)
    print("Conversación creada")

    # Verificar datos iniciales
    print("Datos iniciales:", verificar_datos_conversacion(conversation_id))
    print("Datos faltantes:", datos_faltantes(conversation_id))

    # Actualizar datos
    actualizar_dato(conversation_id, 'nombre_cliente', 'Juan Pérez')
    actualizar_dato(conversation_id, 'propiedad', 'Depa Isla Teja')
    actualizar_dato(conversation_id, 'check_in', '2024-10-15')
    actualizar_dato(conversation_id, 'check_out', '2024-10-20')
    actualizar_dato(conversation_id, 'numero_huespedes', 2)
    actualizar_dato(conversation_id, 'correo_cliente', 'juan@ejemplo.com')

    # Verificar datos actualizados
    print("Datos actualizados:", verificar_datos_conversacion(conversation_id))
    print("Datos faltantes:", datos_faltantes(conversation_id))

    # Confirmar reserva
    if confirmar_reserva(conversation_id):
        print("Reserva confirmada")
    else:
        print("No se puede confirmar: faltan datos")

    # Verificar estado de confirmación
    print("¿Está confirmada?", esta_confirmada(conversation_id))

    # Mostrar conversación completa
    debug_conversation(conversation_id)


if __name__ == "__main__":
    test_nueva_estructura()