# utils/config_manager.py
import keyring
import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.config_dir = Path("data")
        self.config_file = self.config_dir / "app_config.json"
        self.app_name = "AirbnbManager_Valdivia"

        # Crear directorio si no existe
        self.config_dir.mkdir(exist_ok=True)

    def save_email(self, email):
        """Guarda el email en archivo de configuración"""
        try:
            config = self._load_config_file()
            config['email'] = email

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"Email guardado: {email}")
            return True
        except Exception as e:
            print(f"Error guardando email: {e}")
            return False

    def load_email(self):
        """Carga el email guardado"""
        try:
            config = self._load_config_file()
            email = config.get('email', '')
            print(f"Email cargado: {email}")
            return email
        except Exception as e:
            print(f"Error cargando email: {e}")
            return ''

    def save_password(self, email, password):
        """Guarda la contraseña de forma segura usando keyring"""
        try:
            if password:  # Solo guardar si hay contraseña
                keyring.set_password(self.app_name, email, password)
                print("Contraseña guardada en keyring")
                return True
            return False
        except Exception as e:
            print(f"Error guardando contraseña en keyring: {e}")
            return False

    def load_password(self, email):
        """Carga la contraseña guardada"""
        try:
            if not email:
                return ''
            password = keyring.get_password(self.app_name, email)
            print(f"Contraseña cargada desde keyring: {'Sí' if password else 'No'}")
            return password or ''
        except Exception as e:
            print(f"Error cargando contraseña desde keyring: {e}")
            return ''

    def _load_config_file(self):
        """Carga configuración desde archivo"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        return json.loads(content)
                    else:
                        return {}
            except json.JSONDecodeError:
                print("Archivo de configuración corrupto, creando nuevo")
                return {}
            except Exception as e:
                print(f"Error leyendo config file: {e}")
                return {}
        return {}

    def clear_credentials(self):
        """Limpia las credenciales guardadas"""
        try:
            config = self._load_config_file()
            email = config.get('email', '')

            if email:
                try:
                    keyring.delete_password(self.app_name, email)
                    print("Contraseña eliminada de keyring")
                except:
                    print("No se encontró contraseña para eliminar")

            # Limpiar archivo de configuración
            if self.config_file.exists():
                self.config_file.unlink()
                print("Archivo de configuración eliminado")

            return True
        except Exception as e:
            print(f"Error limpiando credenciales: {e}")
            return False

    def test_config(self):
        """Método de prueba para verificar funcionamiento"""
        print("=== TEST CONFIG MANAGER ===")
        print(f"Config file path: {self.config_file}")
        print(f"Config file exists: {self.config_file.exists()}")
        print(f"Current config: {self._load_config_file()}")