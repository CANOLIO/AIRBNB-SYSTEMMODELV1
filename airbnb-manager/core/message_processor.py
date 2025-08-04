# core/message_processor.py
from core.message_analyzer import message_analyzer
from core.response_generator import response_generator
from core.gmail_handler import GmailHandler
from db.database import marcar_mensaje_respondido
from utils.logger import MessageLogger


class MessageProcessor:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.gmail_handler = GmailHandler(email, password)
        self.logger = MessageLogger()
        print("MessageProcessor inicializado")

    def procesar_mensajes_nuevos(self):
        """Procesa mensajes nuevos y genera respuestas automáticas"""
        try:
            print("Iniciando procesamiento de mensajes...")
            mensajes_nuevos = self.gmail_handler.leer_mensajes_para_procesar()

            print(f"Mensajes nuevos para procesar: {len(mensajes_nuevos)}")

            resultados = {
                'respondidos_auto': 0,
                'requieren_revision': 0,
                'errores': 0
            }

            if not mensajes_nuevos:
                print("No hay mensajes nuevos para procesar")
                return resultados

            for mensaje in mensajes_nuevos:
                try:
                    print(f"\nProcesando mensaje ID: {mensaje['id']}")
                    resultado = self.procesar_mensaje_individual(mensaje)

                    if resultado['accion'] == 'respondido':
                        resultados['respondidos_auto'] += 1
                    elif resultado['accion'] == 'revision_manual':
                        resultados['requieren_revision'] += 1

                    self.logger.log_message_processed(
                        mensaje['id'],
                        mensaje['remitente'],
                        resultado['tipo'],
                        resultado['accion'],
                        resultado.get('detalles', '')
                    )
                    print(f"Mensaje procesado: {resultado}")

                except Exception as e:
                    resultados['errores'] += 1
                    self.logger.log_error(mensaje['id'], str(e))
                    print(f"Error procesando mensaje {mensaje['id']}: {e}")

            return resultados

        except Exception as e:
            self.logger.log_error('GENERAL', f"Error general procesando mensajes: {e}")
            print(f"Error general: {e}")
            return None

    def procesar_mensaje_individual(self, mensaje):
        """Procesa un mensaje individual"""
        try:
            # Analizar mensaje
            analisis = message_analyzer.analyze_message(mensaje)

            # Generar respuesta
            respuesta = response_generator.generate_response(analisis)

            # Enviar respuesta
            if self.enviar_respuesta(mensaje, respuesta):
                marcar_mensaje_respondido(mensaje['id'], respuesta)
                return {
                    'tipo': 'respuesta_automatica',
                    'accion': 'respondido',
                    'detalles': 'Respuesta automática generada'
                }
            else:
                return {
                    'tipo': 'respuesta_automatica',
                    'accion': 'error_envio',
                    'detalles': 'Error enviando respuesta'
                }

        except Exception as e:
            self.logger.log_error(mensaje['id'], str(e))
            marcar_mensaje_respondido(mensaje['id'], "Requiere revisión manual", str(e))
            return {
                'tipo': 'error',
                'accion': 'revision_manual',
                'detalles': f"Error: {str(e)}"
            }

    def enviar_respuesta(self, mensaje_original, respuesta):
        """Envía respuesta automática"""
        try:
            destinatario = self.extraer_email_remitente(mensaje_original['remitente'])
            asunto = mensaje_original['asunto']

            print(f"Enviando respuesta a {destinatario}")
            return self.gmail_handler.enviar_respuesta(destinatario, asunto, respuesta)
        except Exception as e:
            print(f"Error enviando respuesta: {e}")
            return False

    def extraer_email_remitente(self, remitente_str):
        """Extrae email del string del remitente"""
        import re
        email_pattern = r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        matches = re.findall(email_pattern, remitente_str)

        for match in matches:
            email = match[0] if match[0] else match[1]
            if email:
                print(f"Email extraído: {email}")
                return email

        print(f"No se pudo extraer email, usando: {remitente_str}")
        return remitente_str


# Mantener compatibilidad con versión anterior
MessageProcessor.analizar_mensaje = MessageProcessor.procesar_mensaje_individual