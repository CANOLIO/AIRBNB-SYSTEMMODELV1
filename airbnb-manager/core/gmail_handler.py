# core/gmail_handler.py
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from db.database import guardar_mensaje


class GmailHandler:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def listar_mensajes_sin_leer(self):
        """Lista mensajes sin leer pero NO los marca como leídos"""
        try:
            print(f"Conectando para listar mensajes sin leer...")
            servidor = imaplib.IMAP4_SSL(self.imap_server)
            servidor.login(self.email, self.password)
            servidor.select("inbox")

            # Buscar mensajes no leídos
            status, mensajes = servidor.search(None, 'UNSEEN')

            if status != 'OK':
                servidor.close()
                servidor.logout()
                return []

            ids = mensajes[0].split()
            mensajes_encontrados = []

            # Solo leer encabezados, no marcar como leídos
            for id in ids[:10]:  # Limitar a 10 mensajes para no sobrecargar
                try:
                    # Usar PEEK para no marcar como leído
                    status, datos = servidor.fetch(id, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')

                    if status == 'OK':
                        mensaje_header = datos[0][1].decode('utf-8')

                        # Parsear encabezados manualmente
                        remitente = self.extraer_campo(mensaje_header, 'From')
                        asunto = self.extraer_campo(mensaje_header, 'Subject')
                        fecha = self.extraer_campo(mensaje_header, 'Date')

                        mensajes_encontrados.append({
                            "id_gmail": id.decode() if isinstance(id, bytes) else id,
                            "remitente": remitente,
                            "asunto": asunto,
                            "fecha": fecha
                        })
                except Exception as e:
                    print(f"Error procesando mensaje {id}: {e}")
                    continue

            servidor.close()
            servidor.logout()
            print(f"Encontrados {len(mensajes_encontrados)} mensajes sin leer")
            return mensajes_encontrados

        except Exception as e:
            print(f"Error listando mensajes: {e}")
            return []

    def extraer_campo(self, header_text, campo):
        """Extrae un campo específico de los headers"""
        import re
        pattern = rf'{campo}:\s*(.+?)(?:\r?\n[^\s]|\r?\n$|$)'
        match = re.search(pattern, header_text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ''

    def leer_mensajes_para_procesar(self):
        """Lee mensajes nuevos PARA PROCESAR y RESPONDER (estos sí se marcan como leídos)"""
        try:
            print(f"Conectando para procesar mensajes...")
            servidor = imaplib.IMAP4_SSL(self.imap_server)
            servidor.login(self.email, self.password)
            servidor.select("inbox")

            # Buscar mensajes no leídos
            status, mensajes = servidor.search(None, 'UNSEEN')

            if status != 'OK':
                servidor.close()
                servidor.logout()
                return []

            ids = mensajes[0].split()
            mensajes_nuevos = []

            for id in ids[:10]:  # Limitar a 10 mensajes
                try:
                    print(f"Procesando mensaje ID: {id}")
                    status, datos = servidor.fetch(id, '(RFC822)')

                    if status != 'OK':
                        continue

                    mensaje_raw = datos[0][1]
                    mensaje_email = email.message_from_bytes(mensaje_raw)

                    remitente = mensaje_email.get('From', 'Desconocido')
                    asunto = mensaje_email.get('Subject', 'Sin asunto')

                    # Extraer cuerpo del mensaje
                    cuerpo = self.extraer_cuerpo_mensaje(mensaje_email)

                    # Guardar en base de datos
                    mensaje_id = guardar_mensaje(remitente, asunto, cuerpo)

                    mensajes_nuevos.append({
                        "id": mensaje_id,
                        "id_gmail": id.decode() if isinstance(id, bytes) else id,
                        "remitente": remitente,
                        "asunto": asunto,
                        "cuerpo": cuerpo
                    })

                except Exception as e:
                    print(f"Error procesando mensaje {id}: {e}")
                    continue

            servidor.close()
            servidor.logout()
            print(f"Procesados {len(mensajes_nuevos)} mensajes para respuesta automática")
            return mensajes_nuevos

        except Exception as e:
            print(f"Error procesando mensajes: {e}")
            return []

    def extraer_cuerpo_mensaje(self, mensaje_email):
        """Extrae el cuerpo del mensaje"""
        try:
            if mensaje_email.is_multipart():
                cuerpo = ''
                for parte in mensaje_email.walk():
                    if parte.get_content_type() == "text/plain":
                        payload = parte.get_payload(decode=True)
                        if payload:
                            cuerpo = payload.decode('utf-8', errors='ignore')
                            break
                return cuerpo
            else:
                payload = mensaje_email.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')
                return ''
        except Exception as e:
            print(f"Error extrayendo cuerpo: {e}")
            return ''

    def enviar_respuesta(self, destinatario, asunto, cuerpo):
        """Envía respuesta automática por Gmail"""
        try:
            print(f"Enviando respuesta a: {destinatario}")

            mensaje = MIMEMultipart()
            mensaje['From'] = self.email
            mensaje['To'] = destinatario
            mensaje['Subject'] = f"Re: {asunto}"

            mensaje.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

            servidor = smtplib.SMTP(self.smtp_server, self.smtp_port)
            servidor.starttls()
            servidor.login(self.email, self.password)
            texto = mensaje.as_string()
            servidor.sendmail(self.email, destinatario, texto)
            servidor.quit()

            print("Respuesta enviada exitosamente")
            return True
        except Exception as e:
            print(f"Error enviando respuesta: {e}")
            return False