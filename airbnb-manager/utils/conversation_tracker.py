import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path


class ConversationTracker:
    def __init__(self):
        self.conversations_file = Path("data/conversations.json")
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def generate_conversation_id(self, client_email, subject):
        """Genera ID único para conversación"""
        # Limpiar subject de prefijos comunes
        clean_subject = re.sub(r'^(re|fw|fwd):\s*', '', subject.lower().strip())
        conversation_key = f"{client_email.lower()}|{clean_subject}"
        return hashlib.md5(conversation_key.encode()).hexdigest()[:12]

    def get_conversation(self, conversation_id):
        """Obtiene conversación completa"""
        conversations = self._load_conversations()
        return conversations.get(conversation_id, self._create_empty_conversation(conversation_id))

    def update_conversation_data(self, conversation_id, data_dict):
        """Actualiza datos de conversación"""
        conversations = self._load_conversations()

        if conversation_id not in conversations:
            conversations[conversation_id] = self._create_empty_conversation(conversation_id)

        # Actualizar datos manteniendo los existentes
        conversations[conversation_id]['data'].update(data_dict)
        conversations[conversation_id]['updated_at'] = datetime.now().isoformat()

        self._save_conversations(conversations)
        return conversations[conversation_id]['data']

    def get_conversation_data(self, conversation_id):
        """Obtiene solo los datos de la conversación"""
        conversation = self.get_conversation(conversation_id)
        return conversation.get('data', {})

    def set_conversation_state(self, conversation_id, state):
        """Establece estado de conversación"""
        conversations = self._load_conversations()
        if conversation_id in conversations:
            conversations[conversation_id]['state'] = state
            conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
            self._save_conversations(conversations)

    def get_conversation_state(self, conversation_id):
        """Obtiene estado de conversación"""
        conversation = self.get_conversation(conversation_id)
        return conversation.get('state', 'new')

    def has_complete_reservation_data(self, conversation_id):
        """Verifica si tiene datos completos para reserva"""
        data = self.get_conversation_data(conversation_id)
        required = ['property_id', 'check_in', 'check_out', 'guest_name']
        return all(field in data for field in required)

    def get_missing_reservation_fields(self, conversation_id):
        """Obtiene campos faltantes"""
        data = self.get_conversation_data(conversation_id)
        required = ['property_id', 'check_in', 'check_out', 'guest_name']
        return [field for field in required if field not in data]

    def _create_empty_conversation(self, conversation_id):
        """Crea estructura básica de conversación"""
        return {
            'id': conversation_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'state': 'new',
            'data': {},
            'messages': []
        }

    def _load_conversations(self):
        """Carga todas las conversaciones"""
        if self.conversations_file.exists():
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_conversations(self, conversations):
        """Guarda conversaciones"""
        try:
            # Limpiar conversaciones antiguas (>48h)
            self._cleanup_old_conversations(conversations)

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


conversation_tracker = ConversationTracker()