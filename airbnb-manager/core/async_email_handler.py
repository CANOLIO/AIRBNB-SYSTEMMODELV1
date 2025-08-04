# core/async_email_handler.py
"""
Asynchronous email handler for improved performance and non-blocking operations
"""
import asyncio
import concurrent.futures
import threading
from typing import List, Dict, Optional, Callable, Any
from functools import wraps
from core.lazy_loader import LazyImporter

# Lazy imports for email handling
imaplib = LazyImporter('imaplib')
email = LazyImporter('email')
smtplib = LazyImporter('smtplib')


class AsyncEmailHandler:
    """Asynchronous email handler with connection pooling and batch processing"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        self._pending_operations = []
        
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    async def connect_imap_async(self, server: str, port: int, username: str, password: str) -> bool:
        """Async IMAP connection"""
        loop = asyncio.get_event_loop()
        
        def _connect():
            try:
                mail = imaplib.IMAP4_SSL(server, port)
                mail.login(username, password)
                
                # Store connection in pool
                with self._pool_lock:
                    connection_key = f"{username}@{server}"
                    self._connection_pool[connection_key] = {
                        'imap': mail,
                        'last_used': asyncio.get_event_loop().time()
                    }
                
                return True
            except Exception as e:
                print(f"Error connecting to IMAP: {e}")
                return False
        
        return await loop.run_in_executor(self.executor, _connect)
    
    async def fetch_emails_async(self, username: str, server: str, limit: int = 50) -> List[Dict]:
        """Fetch emails asynchronously"""
        loop = asyncio.get_event_loop()
        
        def _fetch():
            connection_key = f"{username}@{server}"
            
            with self._pool_lock:
                if connection_key not in self._connection_pool:
                    return []
                
                mail = self._connection_pool[connection_key]['imap']
            
            try:
                mail.select('inbox')
                
                # Search for unseen emails
                result, messages = mail.search(None, 'UNSEEN')
                if result != 'OK':
                    return []
                
                message_ids = messages[0].split()
                emails = []
                
                # Limit the number of emails to process
                for msg_id in message_ids[-limit:]:
                    result, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if result == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract email data
                        email_data = {
                            'id': msg_id.decode(),
                            'subject': email_message['Subject'] or '',
                            'sender': email_message['From'] or '',
                            'date': email_message['Date'] or '',
                            'body': self._extract_body(email_message)
                        }
                        emails.append(email_data)
                
                return emails
                
            except Exception as e:
                print(f"Error fetching emails: {e}")
                return []
        
        return await loop.run_in_executor(self.executor, _fetch)
    
    async def send_email_async(self, smtp_server: str, smtp_port: int, username: str, 
                              password: str, to_email: str, subject: str, body: str) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        
        def _send():
            try:
                msg = email.mime.multipart.MIMEMultipart()
                msg['From'] = username
                msg['To'] = to_email
                msg['Subject'] = subject
                
                msg.attach(email.mime.text.MIMEText(body, 'plain', 'utf-8'))
                
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
                server.quit()
                
                return True
                
            except Exception as e:
                print(f"Error sending email: {e}")
                return False
        
        return await loop.run_in_executor(self.executor, _send)
    
    async def batch_process_emails(self, emails: List[Dict], 
                                 processor_func: Callable[[Dict], Any]) -> List[Any]:
        """Process multiple emails in parallel"""
        loop = asyncio.get_event_loop()
        
        # Create tasks for parallel processing
        tasks = []
        for email_data in emails:
            task = loop.run_in_executor(self.executor, processor_func, email_data)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = [result for result in results if not isinstance(result, Exception)]
        return successful_results
    
    def _extract_body(self, email_message) -> str:
        """Extract body from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if (content_type == "text/plain" and 
                    "attachment" not in content_disposition):
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8')
            except:
                body = str(email_message.get_payload())
        
        return body
    
    async def cleanup_connections(self):
        """Clean up old connections"""
        current_time = asyncio.get_event_loop().time()
        
        with self._pool_lock:
            expired_connections = []
            
            for key, connection_data in self._connection_pool.items():
                # Close connections older than 30 minutes
                if current_time - connection_data['last_used'] > 1800:
                    expired_connections.append(key)
            
            for key in expired_connections:
                try:
                    self._connection_pool[key]['imap'].close()
                    self._connection_pool[key]['imap'].logout()
                except:
                    pass
                del self._connection_pool[key]


class AsyncTaskQueue:
    """Asynchronous task queue for managing email operations"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.queue = asyncio.Queue()
        self.active_tasks = set()
        self.results = {}
        
    async def add_task(self, task_id: str, coro) -> str:
        """Add a task to the queue"""
        await self.queue.put((task_id, coro))
        return task_id
    
    async def worker(self):
        """Worker coroutine to process tasks"""
        while True:
            try:
                task_id, coro = await self.queue.get()
                
                # Wait if we have too many active tasks
                while len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.1)
                
                # Execute task
                task = asyncio.create_task(coro)
                self.active_tasks.add(task)
                
                # Handle task completion
                task.add_done_callback(lambda t: self.active_tasks.discard(t))
                
                try:
                    result = await task
                    self.results[task_id] = {'success': True, 'result': result}
                except Exception as e:
                    self.results[task_id] = {'success': False, 'error': str(e)}
                
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker error: {e}")
    
    async def start_workers(self, num_workers: int = 3):
        """Start worker coroutines"""
        workers = [asyncio.create_task(self.worker()) for _ in range(num_workers)]
        return workers
    
    def get_result(self, task_id: str) -> Optional[Dict]:
        """Get task result"""
        return self.results.get(task_id)


# Global async email handler instance
async_email_handler = AsyncEmailHandler()
async_task_queue = AsyncTaskQueue()


def async_email_operation(func):
    """Decorator to make email operations asynchronous"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            return asyncio.create_task(func(*args, **kwargs))
        else:
            # If no loop is running, run until complete
            return loop.run_until_complete(func(*args, **kwargs))
    return wrapper


# Example usage functions
@async_email_operation
async def fetch_and_process_emails_async(server_config: Dict, processor_func: Callable) -> List[Any]:
    """Fetch and process emails asynchronously"""
    # Connect to email server
    connected = await async_email_handler.connect_imap_async(
        server_config['server'],
        server_config['port'], 
        server_config['username'],
        server_config['password']
    )
    
    if not connected:
        return []
    
    # Fetch emails
    emails = await async_email_handler.fetch_emails_async(
        server_config['username'],
        server_config['server'],
        limit=server_config.get('limit', 50)
    )
    
    # Process emails in parallel
    results = await async_email_handler.batch_process_emails(emails, processor_func)
    
    return results


@async_email_operation
async def send_response_emails_async(email_configs: List[Dict]) -> List[bool]:
    """Send multiple response emails asynchronously"""
    tasks = []
    
    for config in email_configs:
        task = async_email_handler.send_email_async(
            config['smtp_server'],
            config['smtp_port'],
            config['username'],
            config['password'],
            config['to_email'],
            config['subject'],
            config['body']
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [result for result in results if not isinstance(result, Exception)]