# core/response_generator.py
from db.conversation_db import (
    get_missing_fields, is_confirmed, get_conversation,
    update_conversation_field
)
from db.database import (
    verificar_disponibilidad, obtener_propiedad_por_id,
    crear_reserva_con_detalles
)


class ResponseGenerator:
    def __init__(self):
        self.faq_responses = {
            'fumar': "No se permite fumar dentro de las propiedades. Existen áreas designadas para fumadores en el exterior.",
            'mascotas': "No se permiten mascotas en nuestras propiedades, salvo que se indique lo contrario en la descripción.",
            'cancelacion': "Nuestra política de cancelación es de 48 horas antes del check-in para obtener reembolso completo.",
            'checkin': "El check-in es a partir de las 15:00 horas. Si necesitas un horario especial, por favor avísanos con anticipación.",
            'checkout': "El check-out es antes de las 11:00 horas.",
            'wifi': "Todas nuestras propiedades incluyen WiFi de alta velocidad gratuito.",
            'estacionamiento': "El estacionamiento es gratuito y está disponible para nuestros huéspedes."
        }

    # Busca esta función en core/response_generator.py y mejórala:

    def generate_response(self, analysis):
        """Genera respuesta basada en el análisis"""
        conversation_id = analysis['conversation_id']
        context = analysis['context']

        if not context:
            return self._generate_general_response()

        conversation_data = context['data']
        faltantes = context['faltantes']
        confirmada = context['confirmada']

        print(f"\n=== GENERATING RESPONSE DEBUG ===")
        print(f"Conversation ID: {conversation_id}")
        print(f"Conversation Data: {conversation_data}")
        print(f"Faltantes: {faltantes}")
        print(f"Confirmada: {confirmada}")

        # Mostrar datos específicos
        for key in ['nombre_cliente', 'propiedad', 'check_in', 'check_out', 'numero_huespedes', 'correo_cliente']:
            if key in conversation_data:
                print(f"  {key}: {conversation_data[key]}")
            else:
                print(f"  {key}: NO PRESENTE")

        # Verificar si ya está confirmada
        if confirmada:
            return "Su reserva ya ha sido confirmada. Pronto recibirá los detalles por correo."

        # Verificar si tenemos todos los datos para confirmar
        if not faltantes:
            return self._suggest_confirmation(conversation_data)
        else:
            return self._request_missing_fields(faltantes)

    def _request_missing_fields(self, faltantes):
        """Solicita campos faltantes"""
        print(f"Solicitando campos faltantes: {faltantes}")

        if len(faltantes) == 1:
            field = faltantes[0]
            messages = {
                'nombre_cliente': "Para proceder con la reserva, necesito saber su nombre completo.",
                'propiedad': "¿Qué propiedad le interesa reservar?",
                'check_in': "¿Para qué fecha desea comenzar su estadía?",
                'check_out': "¿Hasta qué fecha desea su estadía?",
                'numero_huespedes': "¿Cuántas personas se alojarán?",
                'correo_cliente': "¿Cuál es su correo electrónico para enviar la confirmación?"
            }
            return messages.get(field, f"Necesito que me indique {field.replace('_', ' ')}.")
        else:
            fields_text = []
            for field in faltantes:
                if field == 'nombre_cliente':
                    fields_text.append('su nombre')
                elif field == 'propiedad':
                    fields_text.append('la propiedad')
                elif field == 'check_in':
                    fields_text.append('la fecha de inicio')
                elif field == 'check_out':
                    fields_text.append('la fecha de fin')
                elif field == 'numero_huespedes':
                    fields_text.append('el número de huéspedes')
                elif field == 'correo_cliente':
                    fields_text.append('su correo')

            return f"Para confirmar su reserva, necesito que me indique: {', '.join(fields_text)}. ¿Podría proporcionar esa información?"

    def _suggest_confirmation(self, conversation_data):
        """Sugiere confirmación cuando se tienen todos los datos"""
        return f"""¡Excelente! Ya tenemos todos los datos necesarios para su reserva:

Propiedad: {conversation_data.get('propiedad', 'No especificada')}
Fechas: Del {conversation_data.get('check_in', 'No especificado')} al {conversation_data.get('check_out', 'No especificado')}
Huéspedes: {conversation_data.get('numero_huespedes', 'No especificado')} personas
Cliente: {conversation_data.get('nombre_cliente', 'No especificado')}

¿Desea confirmar esta reserva? Simplemente responda "confirmo" y procederé con la confirmación."""

    def _confirm_reservation(self, conversation_id, conversation_data):
        """Confirma la reserva definitivamente"""
        try:
            # Verificar disponibilidad antes de confirmar
            propiedad_id = int(conversation_data.get('propiedad_id', 1))
            check_in = conversation_data.get('check_in', '')
            check_out = conversation_data.get('check_out', '')

            print(f"Verificando disponibilidad propiedad {propiedad_id} del {check_in} al {check_out}")

            if verificar_disponibilidad(propiedad_id, check_in, check_out):
                # Registrar reserva en base de datos principal
                reservation_id = crear_reserva_con_detalles(
                    propiedad_id,
                    check_in,
                    check_out,
                    conversation_data.get('nombre_cliente', 'Cliente'),
                    conversation_data.get('correo_cliente', ''),
                    conversation_data.get('telefono_cliente', ''),
                    estado='confirmada'
                )

                if reservation_id:
                    # Marcar conversación como confirmada
                    update_conversation_field(conversation_id, 'confirmacion', 'sí')
                    update_conversation_field(conversation_id, 'estado', 'confirmada')

                    propiedad = obtener_propiedad_por_id(propiedad_id)
                    nombre_propiedad = propiedad[1] if propiedad else "la propiedad"

                    return f"""¡Perfecto! Su reserva ha sido confirmada exitosamente.

Detalles de la reserva:
- Propiedad: {nombre_propiedad}
- Fecha de ingreso: {check_in}
- Fecha de salida: {check_out}
- Huésped: {conversation_data.get('nombre_cliente', 'Cliente')}

Hemos registrado su reserva en nuestro sistema. Pronto recibirá un correo con los detalles de pago y check-in.

¡Gracias por elegirnos!

Atentamente,
Equipo de Reservas"""
                else:
                    return "Lo sentimos, hubo un error al registrar su reserva. Por favor, inténtelo nuevamente."
            else:
                return f"""Lamentablemente, la propiedad {conversation_data.get('propiedad', 'seleccionada')} no está disponible para las fechas del {check_in} al {check_out}.

¿Le interesa consultar disponibilidad para otras fechas?"""

        except Exception as e:
            print(f"Error confirmando reserva: {e}")
            return "Lo sentimos, hubo un error al registrar su reserva. Por favor, inténtelo nuevamente."

    def _generate_general_response(self):
        """Genera respuesta general"""
        return """Gracias por su mensaje. Hemos recibido su consulta y la revisaremos a la brevedad.

Normalmente respondemos dentro de las próximas 24 horas.

¡Gracias por su paciencia!"""

# Instancia global
response_generator = ResponseGenerator()