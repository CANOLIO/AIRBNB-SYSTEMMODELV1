# utils/logger.py
import logging
from datetime import datetime
from pathlib import Path


class MessageLogger:
    def __init__(self):
        # Crear directorio de logs
        log_dir = Path("data/logs")
        log_dir.mkdir(exist_ok=True)

        # Configurar logger
        self.logger = logging.getLogger('AirbnbManager')
        self.logger.setLevel(logging.INFO)

        # Evitar duplicados
        if not self.logger.handlers:
            # Handler para archivo
            file_handler = logging.FileHandler('data/logs/mensajes.log', encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            # Handler para consola
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def log_message_processed(self, mensaje_id, remitente, tipo, accion, detalles=""):
        """Registra mensaje procesado"""
        self.logger.info(f"MSG-{mensaje_id} | {remitente} | {tipo} | {accion} | {detalles}")

    def log_error(self, mensaje_id, error):
        """Registra error"""
        self.logger.error(f"MSG-{mensaje_id} | ERROR | {error}")

    def log_manual_review(self, mensaje_id, remitente, motivo):
        """Registra mensaje que requiere revisión manual"""
        self.logger.warning(f"MSG-{mensaje_id} | {remitente} | REVISIÓN MANUAL | {motivo}")