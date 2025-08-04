# core/conversation_flow.py
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import re


class ConversationFlow:
    def __init__(self):
        self.conversations_file = Path("data/conversations.json")
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def get_conversation_id(self, client_email, subject):
        """Genera ID único para conversación"""
        clean_subject = re.sub(r'^(re|fw|fwd):\s*', '', subject.lower().strip())
        conversation_key = f"{client_email.lower()}|{clean_subject}"
        return hashlib.md5(conversation_key.encode()).hexdigest()[:12]

    def get_conversation_context(self, conversation_id):
        """Obtiene contexto completo de la conversación"""
        conversations = self._load_conversations()
        return conversations.get(conversation_id, self._create_new_context())

    def update_conversation_context(self, conversation_id, message_data, message_type):
        """Actualiza contexto de conversación"""
        conversations = self._load_conversations()

        if conversation_id not in conversations:
            conversations[conversation_id] = self._create_new_context()

        # Agregar mensaje al historial
        conversations[conversation_id]['messages'].append({
            'timestamp': datetime.now().isoformat(),
            'data': message_data,
            'type': message_type
        })

        # Extraer y actualizar datos clave
        self._extract_and_update_data(conversations[conversation_id], message_data)

        # Actualizar timestamp
        conversations[conversation_id]['last_updated'] = datetime.now().isoformat()

        # Limpiar conversaciones antiguas
        self._cleanup_old_conversations(conversations)

        self._save_conversations(conversations)
        return conversations[conversation_id]

    def get_reservation_status(self, conversation_id):
        """Obtiene estado de reserva de la conversación"""
        context = self.get_conversation_context(conversation_id)
        data = context.get('data', {})

        # Verificar datos completos
        required_fields = ['property_id', 'check_in', 'check_out', 'guest_name']
        has_all_data = all(field in data for field in required_fields)

        return {
            'complete': has_all_data,
            'missing_fields': [field for field in required_fields if field not in data],
            'data': data
        }

    def _create_new_context(self):
        """Crea nuevo contexto de conversación"""
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'data': {},
            'messages': [],
            'state': 'new'
        }

    def _extract_and_update_data(self, context, message_data):
        """Extrae y actualiza datos del mensaje"""
        data = context['data']

        # Actualizar datos con nueva información
        if 'property_id' in message_data and message_data['property_id']:
            data['property_id'] = message_data['property_id']

        if 'check_in' in message_data and message_data['check_in']:
            data['check_in'] = message_data['check_in']

        if 'check_out' in message_data and message_data['check_out']:
            data['check_out'] = message_data['check_out']

        if 'guest_name' in message_data and message_data['guest_name']:
            data['guest_name'] = message_data['guest_name']

        if 'capacity' in message_data and message_data['capacity']:
            data['capacity'] = message_data['capacity']

        if 'city' in message_data and message_data['city']:
            data['city'] = message_data['city']

        if 'client_email' in message_data and message_data['client_email']:
            data['client_email'] = message_data['client_email']

        if 'phone' in message_data and message_data['phone']:
            data['phone'] = message_data['phone']

    def _load_conversations(self):
        """Carga conversaciones desde archivo"""
        if self.conversations_file.exists():
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_conversations(self, conversations):
        """Guarda conversaciones en archivo"""
        try:
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando conversaciones: {e}")

    def _cleanup_old_conversations(self, conversations):
        """Limpia conversaciones antiguas"""
        cutoff = datetime.now() - timedelta(hours=48)
        old_convs = []

        for conv_id, conv in conversations.items():
            created = datetime.fromisoformat(conv.get('created_at', datetime.now().isoformat()))
            if created < cutoff:
                old_convs.append(conv_id)

        for conv_id in old_convs:
            del conversations[conv_id]


conversation_flow = ConversationFlow()