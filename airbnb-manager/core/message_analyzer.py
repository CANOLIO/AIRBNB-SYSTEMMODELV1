# core/message_analyzer.py
from core.conversation_manager import conversation_manager

class MessageAnalyzer:
    def __init__(self):
        pass

    # En core/message_analyzer.py, en la función analyze_message:

    def analyze_message(self, message):
        """Analiza mensaje y devuelve contexto completo"""
        # Procesar mensaje con el gestor de conversaciones
        conversation_id = conversation_manager.process_message(message)

        # DEBUG: Ver qué se está procesando
        cuerpo = message.get('cuerpo', '')
        remitente = message.get('remitente', '')
        conversation_manager.debug_message_processing(cuerpo, remitente)

        # Obtener contexto de la conversación
        context = conversation_manager.get_conversation_context(conversation_id)

        return {
            'conversation_id': conversation_id,
            'context': context
        }

# Instancia global
message_analyzer = MessageAnalyzer()