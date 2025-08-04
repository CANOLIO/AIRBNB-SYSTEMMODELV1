# gui/app_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import webbrowser
import pyperclip
from pathlib import Path

# Importaciones locales
from utils.config_manager import ConfigManager


class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Airbnb - Valdivia")
        self.root.geometry("1200x800")

        from db.database import init_db
        init_db()
        self.config_manager = ConfigManager()

        # Variables para mensajes seleccionados
        self.mensaje_seleccionado = None

        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Crear pestañas
        self.tab_propiedades = ttk.Frame(self.notebook)
        self.tab_reservas = ttk.Frame(self.notebook)
        self.tab_calendario = ttk.Frame(self.notebook)
        self.tab_mensajes = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)
        self.tab_logs = ttk.Frame(self.notebook)

        # Agregar pestañas al notebook
        self.notebook.add(self.tab_propiedades, text="Propiedades")
        self.notebook.add(self.tab_reservas, text="Reservas")
        self.notebook.add(self.tab_calendario, text="Calendario")
        self.notebook.add(self.tab_mensajes, text="Mensajes")
        self.notebook.add(self.tab_config, text="Configuración")
        self.notebook.add(self.tab_logs, text="Logs")

        self.crear_tab_propiedades()
        self.crear_tab_reservas()
        self.crear_tab_calendario()
        self.crear_tab_mensajes()
        self.crear_tab_config()
        self.crear_tab_logs()

        # Cargar datos iniciales
        self.cargar_propiedades()
        self.cargar_reservas()
        self.cargar_calendario()
        self.cargar_mensajes_procesados()
        self.cargar_mensajes_atencion_humana()
        self.cargar_logs()

    def crear_tab_propiedades(self):
        # Formulario para agregar propiedad
        frame_form = ttk.LabelFrame(self.tab_propiedades, text="Agregar Nueva Propiedad")
        frame_form.pack(fill='x', padx=10, pady=10)

        # Primera fila
        ttk.Label(frame_form, text="Nombre:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.nombre_entry = ttk.Entry(frame_form, width=25)
        self.nombre_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Dirección:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.direccion_entry = ttk.Entry(frame_form, width=25)
        self.direccion_entry.grid(row=0, column=3, padx=5, pady=5)

        # Segunda fila
        ttk.Label(frame_form, text="Capacidad:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.capacidad_entry = ttk.Entry(frame_form, width=10)
        self.capacidad_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(frame_form, text="Precio/noche:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.precio_entry = ttk.Entry(frame_form, width=10)
        self.precio_entry.grid(row=1, column=3, sticky='w', padx=5, pady=5)

        # Tercera fila
        ttk.Label(frame_form, text="Sector:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.sector_entry = ttk.Entry(frame_form, width=20)
        self.sector_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Ciudad:").grid(row=2, column=2, sticky='w', padx=5, pady=5)
        self.ciudad_entry = ttk.Entry(frame_form, width=20)
        self.ciudad_entry.insert(0, "Valdivia")  # Valor por defecto
        self.ciudad_entry.grid(row=2, column=3, padx=5, pady=5)

        ttk.Button(frame_form, text="Agregar Propiedad", command=self.agregar_propiedad).grid(row=3, column=0,
                                                                                              columnspan=4, pady=10)

        # Lista de propiedades
        frame_lista = ttk.LabelFrame(self.tab_propiedades, text="Propiedades Registradas")
        frame_lista.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_propiedades = ttk.Treeview(frame_lista,
                                             columns=('ID', 'Nombre', 'Dirección', 'Capacidad', 'Precio', 'Sector',
                                                      'Ciudad'), show='headings')
        self.tree_propiedades.heading('ID', text='ID')
        self.tree_propiedades.heading('Nombre', text='Nombre')
        self.tree_propiedades.heading('Dirección', text='Dirección')
        self.tree_propiedades.heading('Capacidad', text='Capacidad')
        self.tree_propiedades.heading('Precio', text='Precio/noche')
        self.tree_propiedades.heading('Sector', text='Sector')
        self.tree_propiedades.heading('Ciudad', text='Ciudad')

        self.tree_propiedades.column('ID', width=40)
        self.tree_propiedades.column('Nombre', width=120)
        self.tree_propiedades.column('Dirección', width=150)
        self.tree_propiedades.column('Capacidad', width=80)
        self.tree_propiedades.column('Precio', width=90)
        self.tree_propiedades.column('Sector', width=100)
        self.tree_propiedades.column('Ciudad', width=80)

        scrollbar = ttk.Scrollbar(frame_lista, orient='vertical', command=self.tree_propiedades.yview)
        self.tree_propiedades.configure(yscrollcommand=scrollbar.set)

        self.tree_propiedades.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def crear_tab_reservas(self):
        frame_lista = ttk.LabelFrame(self.tab_reservas, text="Reservas")
        frame_lista.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_reservas = ttk.Treeview(frame_lista,
                                          columns=('ID', 'Propiedad', 'Inicio', 'Fin', 'Huésped', 'Estado', 'Total'),
                                          show='headings')
        self.tree_reservas.heading('ID', text='ID')
        self.tree_reservas.heading('Propiedad', text='Propiedad')
        self.tree_reservas.heading('Inicio', text='Fecha Inicio')
        self.tree_reservas.heading('Fin', text='Fecha Fin')
        self.tree_reservas.heading('Huésped', text='Huésped')
        self.tree_reservas.heading('Estado', text='Estado')
        self.tree_reservas.heading('Total', text='Total')

        for col in ['ID', 'Inicio', 'Fin', 'Estado']:
            self.tree_reservas.column(col, width=80)
        self.tree_reservas.column('Propiedad', width=150)
        self.tree_reservas.column('Huésped', width=120)
        self.tree_reservas.column('Total', width=100)

        scrollbar = ttk.Scrollbar(frame_lista, orient='vertical', command=self.tree_reservas.yview)
        self.tree_reservas.configure(yscrollcommand=scrollbar.set)

        self.tree_reservas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def crear_tab_calendario(self):
        frame_lista = ttk.LabelFrame(self.tab_calendario, text="Calendario de Ocupación")
        frame_lista.pack(fill='both', expand=True, padx=10, pady=10)

        self.tree_calendario = ttk.Treeview(frame_lista, columns=('Propiedad', 'Inicio', 'Fin', 'Huésped', 'Estado'),
                                            show='headings')
        self.tree_calendario.heading('Propiedad', text='Propiedad')
        self.tree_calendario.heading('Inicio', text='Fecha Inicio')
        self.tree_calendario.heading('Fin', text='Fecha Fin')
        self.tree_calendario.heading('Huésped', text='Huésped')
        self.tree_calendario.heading('Estado', text='Estado')

        for col in ['Inicio', 'Fin', 'Estado']:
            self.tree_calendario.column(col, width=100)
        self.tree_calendario.column('Propiedad', width=150)
        self.tree_calendario.column('Huésped', width=120)

        scrollbar = ttk.Scrollbar(frame_lista, orient='vertical', command=self.tree_calendario.yview)
        self.tree_calendario.configure(yscrollcommand=scrollbar.set)

        self.tree_calendario.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def crear_tab_mensajes(self):
        # Frame superior - botones
        frame_top = ttk.Frame(self.tab_mensajes)
        frame_top.pack(fill='x', padx=10, pady=5)

        ttk.Button(frame_top, text="Buscar Nuevos Mensajes", command=self.buscar_mensajes).pack(side='left', padx=5)
        ttk.Button(frame_top, text="Procesar Mensajes Automáticamente",
                   command=self.procesar_mensajes_automaticamente).pack(side='left', padx=5)
        ttk.Button(frame_top, text="Actualizar Todos", command=self.actualizar_todas_las_listas).pack(side='left',
                                                                                                      padx=5)

        # Notebook para separar diferentes tipos de mensajes
        mensajes_notebook = ttk.Notebook(self.tab_mensajes)
        mensajes_notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Pestaña 1: Mensajes sin leer
        self.tab_mensajes_sin_leer = ttk.Frame(mensajes_notebook)
        mensajes_notebook.add(self.tab_mensajes_sin_leer, text="Mensajes Sin Leer")

        # Pestaña 2: Mensajes procesados
        self.tab_mensajes_procesados = ttk.Frame(mensajes_notebook)
        mensajes_notebook.add(self.tab_mensajes_procesados, text="Mensajes Procesados")

        # Pestaña 3: Mensajes que requieren atención humana
        self.tab_mensajes_atencion = ttk.Frame(mensajes_notebook)
        mensajes_notebook.add(self.tab_mensajes_atencion, text="Requieren Atención Humana")

        # === MENSajes SIN LEER ===
        frame_sin_leer = ttk.LabelFrame(self.tab_mensajes_sin_leer, text="Mensajes Pendientes de Procesar")
        frame_sin_leer.pack(fill='both', expand=True, padx=5, pady=5)

        self.tree_mensajes_sin_leer = ttk.Treeview(frame_sin_leer, columns=('ID', 'Remitente', 'Asunto', 'Fecha'),
                                                   show='headings')
        self.tree_mensajes_sin_leer.heading('ID', text='ID Gmail')
        self.tree_mensajes_sin_leer.heading('Remitente', text='Remitente')
        self.tree_mensajes_sin_leer.heading('Asunto', text='Asunto')
        self.tree_mensajes_sin_leer.heading('Fecha', text='Fecha')

        self.tree_mensajes_sin_leer.column('ID', width=80)
        self.tree_mensajes_sin_leer.column('Remitente', width=200)
        self.tree_mensajes_sin_leer.column('Asunto', width=250)
        self.tree_mensajes_sin_leer.column('Fecha', width=150)

        # Tags para colores
        self.tree_mensajes_sin_leer.tag_configure('nuevo', background='#FFE4B5')  # Amarillo claro

        scrollbar_sin_leer_y = ttk.Scrollbar(frame_sin_leer, orient='vertical',
                                             command=self.tree_mensajes_sin_leer.yview)
        scrollbar_sin_leer_x = ttk.Scrollbar(frame_sin_leer, orient='horizontal',
                                             command=self.tree_mensajes_sin_leer.xview)
        self.tree_mensajes_sin_leer.configure(yscrollcommand=scrollbar_sin_leer_y.set,
                                              xscrollcommand=scrollbar_sin_leer_x.set)

        self.tree_mensajes_sin_leer.pack(side='left', fill='both', expand=True)
        scrollbar_sin_leer_y.pack(side='right', fill='y')
        scrollbar_sin_leer_x.pack(side='bottom', fill='x')

        # === MENSajes PROCESADOS ===
        frame_procesados = ttk.LabelFrame(self.tab_mensajes_procesados, text="Mensajes Procesados")
        frame_procesados.pack(fill='both', expand=True, padx=5, pady=5)

        self.tree_mensajes_procesados = ttk.Treeview(frame_procesados,
                                                     columns=('ID', 'Remitente', 'Asunto', 'Fecha', 'Respondido'),
                                                     show='headings')
        self.tree_mensajes_procesados.heading('ID', text='ID')
        self.tree_mensajes_procesados.heading('Remitente', text='Remitente')
        self.tree_mensajes_procesados.heading('Asunto', text='Asunto')
        self.tree_mensajes_procesados.heading('Fecha', text='Fecha')
        self.tree_mensajes_procesados.heading('Respondido', text='Respondido')

        self.tree_mensajes_procesados.column('ID', width=50)
        self.tree_mensajes_procesados.column('Remitente', width=200)
        self.tree_mensajes_procesados.column('Asunto', width=200)
        self.tree_mensajes_procesados.column('Fecha', width=120)
        self.tree_mensajes_procesados.column('Respondido', width=80)

        # Tags para colores
        self.tree_mensajes_procesados.tag_configure('manual_review', background='#FFE4B5')  # Amarillo claro
        self.tree_mensajes_procesados.tag_configure('respondido', background='#90EE90')  # Verde claro

        scrollbar_procesados_y = ttk.Scrollbar(frame_procesados, orient='vertical',
                                               command=self.tree_mensajes_procesados.yview)
        scrollbar_procesados_x = ttk.Scrollbar(frame_procesados, orient='horizontal',
                                               command=self.tree_mensajes_procesados.xview)
        self.tree_mensajes_procesados.configure(yscrollcommand=scrollbar_procesados_y.set,
                                                xscrollcommand=scrollbar_procesados_x.set)

        self.tree_mensajes_procesados.pack(side='left', fill='both', expand=True)
        scrollbar_procesados_y.pack(side='right', fill='y')
        scrollbar_procesados_x.pack(side='bottom', fill='x')

        # === MENSajes QUE REQUIEREN ATENCIÓN HUMANA ===
        frame_atencion = ttk.LabelFrame(self.tab_mensajes_atencion, text="Mensajes que Requieren Atención Humana")
        frame_atencion.pack(fill='both', expand=True, padx=5, pady=5)

        # Frame superior para botones de atención
        frame_atencion_botones = ttk.Frame(frame_atencion)
        frame_atencion_botones.pack(fill='x', padx=5, pady=5)

        ttk.Button(frame_atencion_botones, text="Abrir en Gmail", command=self.abrir_mensaje_gmail).pack(side='left',
                                                                                                         padx=5)
        ttk.Button(frame_atencion_botones, text="Copiar Contenido", command=self.copiar_contenido_mensaje).pack(
            side='left', padx=5)
        ttk.Button(frame_atencion_botones, text="Marcar como Revisado", command=self.marcar_como_revisado).pack(
            side='left', padx=5)

        self.tree_mensajes_atencion = ttk.Treeview(frame_atencion,
                                                   columns=('ID', 'Remitente', 'Asunto', 'Fecha', 'Motivo'),
                                                   show='headings')
        self.tree_mensajes_atencion.heading('ID', text='ID')
        self.tree_mensajes_atencion.heading('Remitente', text='Remitente')
        self.tree_mensajes_atencion.heading('Asunto', text='Asunto')
        self.tree_mensajes_atencion.heading('Fecha', text='Fecha')
        self.tree_mensajes_atencion.heading('Motivo', text='Motivo')

        self.tree_mensajes_atencion.column('ID', width=50)
        self.tree_mensajes_atencion.column('Remitente', width=180)
        self.tree_mensajes_atencion.column('Asunto', width=200)
        self.tree_mensajes_atencion.column('Fecha', width=120)
        self.tree_mensajes_atencion.column('Motivo', width=200)

        # Tags para colores
        self.tree_mensajes_atencion.tag_configure('atencion', background='#FFB6C1')  # Rosa claro

        scrollbar_atencion_y = ttk.Scrollbar(frame_atencion, orient='vertical',
                                             command=self.tree_mensajes_atencion.yview)
        scrollbar_atencion_x = ttk.Scrollbar(frame_atencion, orient='horizontal',
                                             command=self.tree_mensajes_atencion.xview)
        self.tree_mensajes_atencion.configure(yscrollcommand=scrollbar_atencion_y.set,
                                              xscrollcommand=scrollbar_atencion_x.set)

        self.tree_mensajes_atencion.pack(side='left', fill='both', expand=True)
        scrollbar_atencion_y.pack(side='right', fill='y')
        scrollbar_atencion_x.pack(side='bottom', fill='x')

        # Bind para selección de mensajes
        self.tree_mensajes_atencion.bind('<<TreeviewSelect>>', self.seleccionar_mensaje_atencion)

        # Frame detalle mensaje
        frame_detalle = ttk.LabelFrame(self.tab_mensajes, text="Detalle del Mensaje")
        frame_detalle.pack(fill='both', expand=True, padx=10, pady=5)

        self.text_mensaje = tk.Text(frame_detalle, height=8)
        self.text_mensaje.pack(fill='both', expand=True, padx=5, pady=5)

        # Frame respuesta
        frame_respuesta = ttk.LabelFrame(self.tab_mensajes, text="Respuesta Generada")
        frame_respuesta.pack(fill='x', padx=10, pady=5)

        self.text_respuesta = tk.Text(frame_respuesta, height=4)
        self.text_respuesta.pack(fill='both', expand=True, padx=5, pady=5)

    def crear_tab_config(self):
        frame_config = ttk.LabelFrame(self.tab_config, text="Configuración de Cuenta Gmail")
        frame_config.pack(fill='both', expand=True, padx=10, pady=10)

        # Cargar credenciales guardadas
        saved_email = self.config_manager.load_email()

        ttk.Label(frame_config, text="Email:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.email_entry = ttk.Entry(frame_config, width=30)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        if saved_email:
            self.email_entry.insert(0, saved_email)

        ttk.Label(frame_config, text="Contraseña/App Password:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.password_entry = ttk.Entry(frame_config, width=30, show='*')
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # Botón para mostrar/ocultar contraseña
        self.show_password_var = tk.BooleanVar()
        show_btn = ttk.Checkbutton(frame_config, text="Mostrar contraseña", variable=self.show_password_var,
                                   command=self.toggle_password_visibility)
        show_btn.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        frame_botones = ttk.Frame(frame_config)
        frame_botones.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(frame_botones, text="Guardar Configuración", command=self.guardar_config).pack(side='left', padx=5)
        ttk.Button(frame_botones, text="Probar Conexión Gmail", command=self.probar_conexion).pack(side='left', padx=5)
        ttk.Button(frame_botones, text="Limpiar Credenciales", command=self.limpiar_credenciales).pack(side='left',
                                                                                                       padx=5)
        ttk.Button(frame_botones, text="Procesamiento Automático", command=self.configurar_auto_procesamiento).pack(
            side='left', padx=5)

        # Estado de conexión
        self.connection_status = ttk.Label(frame_config, text="Estado: No configurado")
        self.connection_status.grid(row=4, column=0, columnspan=2, pady=5)

        # Mostrar información de carga inicial
        if saved_email:
            self.connection_status.config(text=f"Estado: Credenciales cargadas para {saved_email}")

    def crear_tab_logs(self):
        frame_logs = ttk.LabelFrame(self.tab_logs, text="Registro de Actividad")
        frame_logs.pack(fill='both', expand=True, padx=10, pady=10)

        # Botones
        frame_botones = ttk.Frame(frame_logs)
        frame_botones.pack(fill='x', padx=5, pady=5)

        ttk.Button(frame_botones, text="Actualizar Logs", command=self.cargar_logs).pack(side='left', padx=5)
        ttk.Button(frame_botones, text="Limpiar Logs", command=self.limpiar_logs).pack(side='left', padx=5)

        # Área de texto para logs
        self.text_logs = tk.Text(frame_logs, height=20)
        self.text_logs.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar_logs = ttk.Scrollbar(frame_logs, orient='vertical', command=self.text_logs.yview)
        self.text_logs.configure(yscrollcommand=scrollbar_logs.set)
        scrollbar_logs.pack(side='right', fill='y')

    def toggle_password_visibility(self):
        """Muestra u oculta la contraseña"""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='*')

    def guardar_config(self):
        """Guarda las credenciales de forma segura"""
        try:
            email = self.email_entry.get().strip()
            password = self.password_entry.get()

            if not email:
                messagebox.showerror("Error", "Ingrese el email")
                return

            # Guardar email en archivo
            if self.config_manager.save_email(email):
                # Guardar contraseña de forma segura (solo si se proporcionó)
                if password:
                    if self.config_manager.save_password(email, password):
                        messagebox.showinfo("Éxito", "Credenciales guardadas correctamente")
                        self.connection_status.config(text=f"Estado: Credenciales guardadas para {email}")
                    else:
                        messagebox.showwarning("Advertencia", "Email guardado, pero error al guardar contraseña")
                else:
                    messagebox.showinfo("Éxito", "Email guardado. Ingrese contraseña para guardarla también.")
                    self.connection_status.config(text=f"Estado: Email guardado para {email}")
            else:
                messagebox.showerror("Error", "Error al guardar el email")

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {str(e)}")

    def probar_conexion(self):
        def tarea_conexion():
            try:
                # Obtener credenciales de los campos o cargar guardadas
                email = self.email_entry.get().strip()
                password = self.password_entry.get()

                # Si no hay credenciales en campos, cargar guardadas
                if not email:
                    email = self.config_manager.load_email()
                if not password:
                    password = self.config_manager.load_password(email)

                if not email or not password:
                    self.root.after(0, lambda: messagebox.showerror("Error",
                                                                    "Configure las credenciales de Gmail primero"))
                    self.root.after(0, lambda: self.connection_status.config(
                        text="Estado: Error - Credenciales faltantes"))
                    return

                import imaplib

                # Intentar conectar
                servidor = imaplib.IMAP4_SSL("imap.gmail.com")
                servidor.login(email, password)
                servidor.select("inbox")

                # Contar mensajes no leídos
                status, mensajes = servidor.search(None, 'UNSEEN')
                unread_count = len(mensajes[0].split()) if mensajes[0] else 0

                servidor.close()
                servidor.logout()

                # Actualizar estado en UI principal
                self.root.after(0, lambda: self.connection_status.config(
                    text=f"Estado: Conectado ✓ ({unread_count} mensajes sin leer)"
                ))

                self.root.after(0, lambda: messagebox.showinfo("Éxito",
                                                               f"Conexión exitosa a Gmail\nMensajes sin leer: {unread_count}"))

            except imaplib.IMAP4.error as e:
                self.root.after(0, lambda: self.connection_status.config(text="Estado: Error de autenticación"))
                self.root.after(0, lambda: messagebox.showerror("Error de Autenticación",
                                                                f"Credenciales incorrectas: {str(e)}"))
            except Exception as e:
                self.root.after(0, lambda: self.connection_status.config(text="Estado: Error de conexión"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error de conexión: {str(e)}"))

        self.connection_status.config(text="Estado: Conectando...")
        threading.Thread(target=tarea_conexion, daemon=True).start()

    def limpiar_credenciales(self):
        """Limpia las credenciales guardadas"""
        if messagebox.askyesno("Confirmar", "¿Está seguro de limpiar las credenciales guardadas?"):
            try:
                if self.config_manager.clear_credentials():
                    self.email_entry.delete(0, tk.END)
                    self.password_entry.delete(0, tk.END)
                    self.connection_status.config(text="Estado: Credenciales eliminadas")
                    messagebox.showinfo("Éxito", "Credenciales eliminadas correctamente")
                else:
                    messagebox.showerror("Error", "Error al eliminar credenciales")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")

    def configurar_auto_procesamiento(self):
        """Configura procesamiento automático periódico"""
        messagebox.showinfo("Información", "Funcionalidad de procesamiento automático programado en desarrollo")

    # Métodos de funcionalidad
    def agregar_propiedad(self):
        nombre = self.nombre_entry.get()
        direccion = self.direccion_entry.get()
        capacidad = self.capacidad_entry.get()
        precio = self.precio_entry.get() or "0"
        sector = self.sector_entry.get()
        ciudad = self.ciudad_entry.get() or "Valdivia"

        if not all([nombre, direccion, capacidad]):
            messagebox.showerror("Error", "Nombre, dirección y capacidad son obligatorios")
            return

        try:
            capacidad = int(capacidad)
            precio = float(precio) if precio else 0
            from db.database import agregar_propiedad
            agregar_propiedad(nombre, direccion, capacidad, precio, sector, ciudad)
            self.cargar_propiedades()
            messagebox.showinfo("Éxito", "Propiedad agregada correctamente")

            # Limpiar campos
            self.nombre_entry.delete(0, tk.END)
            self.direccion_entry.delete(0, tk.END)
            self.capacidad_entry.delete(0, tk.END)
            self.precio_entry.delete(0, tk.END)
            self.sector_entry.delete(0, tk.END)
            self.ciudad_entry.delete(0, tk.END)
            self.ciudad_entry.insert(0, "Valdivia")

        except ValueError:
            messagebox.showerror("Error", "Capacidad y precio deben ser números válidos")

    def cargar_propiedades(self):
        for item in self.tree_propiedades.get_children():
            self.tree_propiedades.delete(item)

        from db.database import obtener_propiedades
        propiedades = obtener_propiedades()
        for prop in propiedades:
            # Asegurar que tenemos suficientes columnas
            if len(prop) >= 7:
                valores = (
                    prop[0],  # ID
                    prop[1],  # Nombre
                    prop[2],  # Dirección
                    prop[3],  # Capacidad
                    f"${prop[4]:,.0f}" if prop[4] else "$0",  # Precio
                    prop[5] if prop[5] else "",  # Sector
                    prop[6] if len(prop) > 6 else "Valdivia"  # Ciudad
                )
                self.tree_propiedades.insert('', 'end', values=valores)

    # Agrega este método a la clase AppGUI en gui/app_gui.py

    def cargar_reservas(self):
        """Carga reservas confirmadas en la tabla"""
        for item in self.tree_reservas.get_children():
            self.tree_reservas.delete(item)

        try:
            from db.database import obtener_reservas
            reservas = obtener_reservas()

            # Filtrar solo reservas confirmadas
            reservas_confirmadas = [r for r in reservas if len(r) > 9 and r[7] == 'confirmada']

            for reserva in reservas_confirmadas:
                # Formatear precio
                precio_formateado = f"${reserva[8]:,.0f}" if len(reserva) > 8 and reserva[8] else "N/A"

                # Asegurar que tenemos suficientes columnas
                if len(reserva) >= 9:
                    valores = (
                        reserva[0] if reserva[0] else "",  # ID
                        reserva[9] if len(reserva) > 9 else "N/A",  # Nombre propiedad
                        reserva[2] if len(reserva) > 2 else "",  # Fecha inicio
                        reserva[3] if len(reserva) > 3 else "",  # Fecha fin
                        reserva[4] if len(reserva) > 4 else "N/A",  # Huésped
                        reserva[7] if len(reserva) > 7 else "N/A",  # Estado
                        precio_formateado  # Precio total
                    )
                    self.tree_reservas.insert('', 'end', values=valores)

        except Exception as e:
            print(f"Error cargando reservas: {e}")

    def cargar_calendario(self):
        for item in self.tree_calendario.get_children():
            self.tree_calendario.delete(item)

        from db.database import obtener_calendario_ocupacion
        ocupaciones = obtener_calendario_ocupacion()
        for ocupacion in ocupaciones:
            self.tree_calendario.insert('', 'end', values=ocupacion)

    def cargar_mensajes_sin_leer(self, mensajes):
        """Carga mensajes sin leer en la GUI"""
        # Limpiar árbol existente
        for item in self.tree_mensajes_sin_leer.get_children():
            self.tree_mensajes_sin_leer.delete(item)

        for mensaje in mensajes:
            valores = (
                mensaje.get('id_gmail', 'N/A')[:15],
                mensaje.get('remitente', 'Desconocido')[:35],
                mensaje.get('asunto', 'Sin asunto')[:40],
                mensaje.get('fecha', '')[:20]
            )
            self.tree_mensajes_sin_leer.insert('', 'end', values=valores, tags=('nuevo',))

    def cargar_mensajes_procesados(self):
        """Carga mensajes procesados desde la base de datos"""
        # Limpiar árbol existente
        for item in self.tree_mensajes_procesados.get_children():
            self.tree_mensajes_procesados.delete(item)

        try:
            from db.database import obtener_mensajes_no_respondidos
            mensajes = obtener_mensajes_no_respondidos()

            for mensaje in mensajes:
                # Asegurar que tenemos suficientes columnas
                if len(mensaje) >= 7:
                    respondido = "Sí" if mensaje[6] else "No"
                    valores = (
                        mensaje[0] if mensaje[0] else "",
                        mensaje[1][:35] if mensaje[1] else "Desconocido",
                        mensaje[2][:35] if mensaje[2] else "Sin asunto",
                        mensaje[4][:20] if len(mensaje) > 4 else "",
                        respondido
                    )

                    # Aplicar tags según estado
                    tags = []
                    if not mensaje[6]:  # No respondido
                        tags.append('manual_review')
                    else:
                        tags.append('respondido')

                    self.tree_mensajes_procesados.insert('', 'end', values=valores, tags=tags)

        except Exception as e:
            print(f"Error cargando mensajes procesados: {e}")

    def cargar_mensajes_atencion_humana(self):
        """Carga mensajes que requieren atención humana"""
        # Limpiar árbol existente
        for item in self.tree_mensajes_atencion.get_children():
            self.tree_mensajes_atencion.delete(item)

        try:
            from db.database import obtener_mensajes_que_requieren_atencion
            mensajes = obtener_mensajes_que_requieren_atencion()

            for mensaje in mensajes:
                # Asegurar que tenemos suficientes columnas
                if len(mensaje) >= 8:
                    motivo = mensaje[7] if mensaje[7] else "No especificado"
                    valores = (
                        mensaje[0] if mensaje[0] else "",
                        mensaje[1][:30] if mensaje[1] else "Desconocido",
                        mensaje[2][:30] if mensaje[2] else "Sin asunto",
                        mensaje[4][:15] if len(mensaje) > 4 else "",
                        motivo[:35]
                    )

                    self.tree_mensajes_atencion.insert('', 'end', values=valores, tags=('atencion',))

        except Exception as e:
            print(f"Error cargando mensajes de atención: {e}")

    def seleccionar_mensaje_atencion(self, event):
        """Maneja la selección de un mensaje que requiere atención"""
        seleccion = self.tree_mensajes_atencion.selection()
        if seleccion:
            item = self.tree_mensajes_atencion.item(seleccion[0])
            self.mensaje_seleccionado = item['values'][0]  # ID del mensaje

    def abrir_mensaje_gmail(self):
        """Abre el mensaje seleccionado en Gmail (simulado)"""
        if self.mensaje_seleccionado:
            # En una implementación real, aquí se abriría el mensaje en Gmail
            messagebox.showinfo("Información", f"Funcionalidad para abrir mensaje {self.mensaje_seleccionado} en Gmail")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un mensaje primero")

    def copiar_contenido_mensaje(self):
        """Copia el contenido del mensaje seleccionado al portapapeles"""
        if self.mensaje_seleccionado:
            try:
                # Aquí se copiaría el contenido real del mensaje
                pyperclip.copy(f"Contenido del mensaje ID: {self.mensaje_seleccionado}")
                messagebox.showinfo("Éxito", "Contenido copiado al portapapeles")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar: {e}")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un mensaje primero")

    def marcar_como_revisado(self):
        """Marca el mensaje seleccionado como revisado"""
        if self.mensaje_seleccionado:
            if messagebox.askyesno("Confirmar", "¿Marcar este mensaje como revisado?"):
                try:
                    from db.database import marcar_mensaje_respondido
                    # Marcar como respondido con respuesta vacía
                    marcar_mensaje_respondido(self.mensaje_seleccionado, "Revisado manualmente", "Revisado por usuario")
                    self.cargar_mensajes_atencion_humana()
                    self.mensaje_seleccionado = None
                    messagebox.showinfo("Éxito", "Mensaje marcado como revisado")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al marcar como revisado: {e}")
        else:
            messagebox.showwarning("Advertencia", "Seleccione un mensaje primero")

    def cargar_logs(self):
        """Carga los logs en la interfaz"""
        try:
            log_file = "data/logs/mensajes.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    self.text_logs.delete(1.0, tk.END)
                    self.text_logs.insert(1.0, contenido)
                    self.text_logs.see(tk.END)  # Ir al final
            else:
                self.text_logs.delete(1.0, tk.END)
                self.text_logs.insert(1.0, "No hay registros disponibles.")
        except Exception as e:
            self.text_logs.delete(1.0, tk.END)
            self.text_logs.insert(1.0, f"Error cargando logs: {e}")

    def limpiar_logs(self):
        """Limpia el archivo de logs"""
        try:
            log_file = "data/logs/mensajes.log"
            if os.path.exists(log_file):
                open(log_file, 'w').close()  # Vaciar archivo
                self.cargar_logs()
                messagebox.showinfo("Éxito", "Logs limpiados correctamente")
            else:
                messagebox.showinfo("Información", "No hay logs para limpiar")
        except Exception as e:
            messagebox.showerror("Error", f"Error limpiando logs: {e}")

    def buscar_mensajes(self):
        def tarea_busqueda():
            try:
                # Obtener credenciales de los campos o cargar guardadas
                email = self.email_entry.get().strip()
                password = self.password_entry.get()

                # Si no hay credenciales en campos, cargar guardadas
                if not email:
                    email = self.config_manager.load_email()
                if not password:
                    password = self.config_manager.load_password(email)

                if not email or not password:
                    self.root.after(0, lambda: messagebox.showerror("Error",
                                                                    "Configure las credenciales de Gmail primero"))
                    return

                from core.gmail_handler import GmailHandler
                gmail_handler = GmailHandler(email, password)
                mensajes_encontrados = gmail_handler.listar_mensajes_sin_leer()

                if mensajes_encontrados:
                    # Mostrar en GUI
                    self.root.after(0, lambda: self.cargar_mensajes_sin_leer(mensajes_encontrados))
                    # También actualizar otras listas
                    self.root.after(0, self.cargar_mensajes_procesados)
                    self.root.after(0, self.cargar_mensajes_atencion_humana)
                    self.root.after(0, lambda: messagebox.showinfo("Éxito",
                                                                   f"Se encontraron {len(mensajes_encontrados)} mensajes sin leer"))
                else:
                    self.root.after(0, lambda: self.cargar_mensajes_sin_leer([]))
                    # Actualizar otras listas
                    self.root.after(0, self.cargar_mensajes_procesados)
                    self.root.after(0, self.cargar_mensajes_atencion_humana)
                    self.root.after(0, lambda: messagebox.showinfo("Información", "No hay mensajes sin leer"))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error al buscar mensajes: {str(e)}"))

        threading.Thread(target=tarea_busqueda, daemon=True).start()

    # En gui/app_gui.py, busca la función procesar_mensajes_automaticamente y reemplázala:

    def procesar_mensajes_automaticamente(self):
        """Procesa mensajes automáticamente con respuestas inteligentes"""

        def tarea_procesamiento():
            try:
                # Obtener credenciales
                email = self.email_entry.get().strip()
                password = self.password_entry.get()

                if not email:
                    email = self.config_manager.load_email()
                if not password:
                    password = self.config_manager.load_password(email)

                if not email or not password:
                    self.root.after(0, lambda: messagebox.showerror("Error",
                                                                    "Configure las credenciales de Gmail primero"))
                    return

                # Procesar mensajes (estos sí se marcan como leídos)
                from core.message_processor import MessageProcessor
                processor = MessageProcessor(email, password)
                resultados = processor.procesar_mensajes_nuevos()

                if resultados:
                    mensaje_resultado = f"""Procesamiento completado:
    - Mensajes respondidos automáticamente: {resultados['respondidos_auto']}
    - Mensajes que requieren revisión: {resultados['requieren_revision']}
    - Errores: {resultados['errores']}"""

                    # Refrescar todas las listas
                    self.root.after(0, self.actualizar_todas_las_listas_despues_de_procesar)
                    self.root.after(0, self.cargar_logs)
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", mensaje_resultado))
                else:
                    self.root.after(0, self.actualizar_todas_las_listas_despues_de_procesar)
                    self.root.after(0,
                                    lambda: messagebox.showinfo("Información", "No hay nuevos mensajes para procesar"))

            except Exception as e:
                import traceback
                error_msg = f"Error procesando mensajes: {str(e)}"
                print(error_msg)
                traceback.print_exc()
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))

        if messagebox.askyesno("Confirmar",
                               "¿Desea procesar automáticamente los mensajes nuevos?\n(Se marcarán como leídos y se responderán)"):
            threading.Thread(target=tarea_procesamiento, daemon=True).start()

    def actualizar_todas_las_listas_despues_de_procesar(self):
        """Actualiza todas las listas después de procesar mensajes"""
        try:
            # Limpiar lista de mensajes sin leer
            self.cargar_mensajes_sin_leer([])

            # Actualizar mensajes procesados
            self.cargar_mensajes_procesados()

            # Actualizar mensajes que requieren atención
            self.cargar_mensajes_atencion_humana()

            print("Todas las listas actualizadas después de procesamiento")

        except Exception as e:
            print(f"Error actualizando listas después de procesamiento: {e}")

    def actualizar_todas_las_listas(self):
        """Actualiza todas las listas de mensajes"""
        try:
            # Buscar mensajes sin leer nuevamente
            self.buscar_mensajes_para_actualizar()

            # Actualizar mensajes procesados
            self.cargar_mensajes_procesados()

            # Actualizar mensajes que requieren atención
            self.cargar_mensajes_atencion_humana()

            print("Todas las listas actualizadas")

        except Exception as e:
            print(f"Error actualizando listas: {e}")

    def buscar_mensajes_para_actualizar(self):
        """Busca mensajes sin leer para actualizar la lista"""
        try:
            # Obtener credenciales
            email = self.email_entry.get().strip()
            if not email:
                email = self.config_manager.load_email()

            password = self.password_entry.get()
            if not password:
                password = self.config_manager.load_password(email)

            if email and password:
                from core.gmail_handler import GmailHandler
                gmail_handler = GmailHandler(email, password)
                mensajes_encontrados = gmail_handler.listar_mensajes_sin_leer()
                self.cargar_mensajes_sin_leer(mensajes_encontrados)
            else:
                self.cargar_mensajes_sin_leer([])

        except Exception as e:
            print(f"Error buscando mensajes para actualización: {e}")
            self.cargar_mensajes_sin_leer([])

    def enviar_respuesta_manual(self):
        """Envía respuesta manual (pendiente de implementación completa)"""
        messagebox.showinfo("Información", "Funcionalidad de envío manual en desarrollo")


# Punto de entrada
if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()