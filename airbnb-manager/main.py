# main.py
import os
import tkinter as tk
from tkinter import messagebox
from gui.app_gui import AppGUI


def main():
    # Crear directorios necesarios
    directories = ['data', 'data/logs']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Verificar dependencias
    try:
        import imaplib
        import keyring
    except ImportError as e:
        print(f"Error: Dependencia faltante. Instala con: pip install imaplib2 keyring")
        return

    # Iniciar aplicación
    try:
        root = tk.Tk()
        app = AppGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error iniciando la aplicación: {e}")


if __name__ == "__main__":
    main()