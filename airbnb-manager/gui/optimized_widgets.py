# gui/optimized_widgets.py
"""
Optimized GUI widgets with virtual scrolling and performance improvements
"""
from core.lazy_loader import LazyImporter
from typing import List, Dict, Any, Optional, Callable
import threading
import time

# Lazy imports for GUI components
tk = LazyImporter('tkinter')
ttk = LazyImporter('tkinter.ttk')


class VirtualListbox:
    """Virtual listbox widget that only renders visible items for better performance"""
    
    def __init__(self, parent, height: int = 10, data_provider: Optional[Callable] = None):
        self.parent = parent
        self.height = height
        self.data_provider = data_provider or (lambda: [])
        
        # Create frame and widgets
        self.frame = ttk.Frame(parent)
        self.setup_widgets()
        
        # Virtual scrolling state
        self.total_items = 0
        self.visible_start = 0
        self.visible_end = 0
        self.item_height = 20  # Estimated item height in pixels
        self.cache = {}
        self.cache_size = 200
        
        # Performance tracking
        self.last_update = 0
        self.update_throttle = 0.1  # Minimum time between updates
        
    def setup_widgets(self):
        """Setup the virtual listbox widgets"""
        # Create listbox and scrollbar
        self.listbox = tk.Listbox(self.frame, height=self.height)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.on_scroll)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack widgets
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.listbox.bind("<MouseWheel>", self.on_mousewheel)
        self.listbox.bind("<KeyPress>", self.on_keypress)
        
    def set_data_provider(self, provider: Callable):
        """Set the data provider function"""
        self.data_provider = provider
        self.cache.clear()
        self.refresh()
    
    def refresh(self):
        """Refresh the listbox content"""
        current_time = time.time()
        if current_time - self.last_update < self.update_throttle:
            return
        
        self.last_update = current_time
        
        # Get total number of items
        try:
            data = self.data_provider()
            self.total_items = len(data) if hasattr(data, '__len__') else 0
        except Exception as e:
            print(f"Error getting data: {e}")
            self.total_items = 0
            return
        
        # Update visible range
        self.update_visible_range()
        
        # Update listbox content
        self.update_listbox_content()
    
    def update_visible_range(self):
        """Calculate which items should be visible"""
        # Calculate visible range based on scroll position
        first_visible = max(0, int(self.scrollbar.get()[0] * self.total_items))
        last_visible = min(self.total_items, first_visible + self.height + 1)
        
        self.visible_start = first_visible
        self.visible_end = last_visible
    
    def update_listbox_content(self):
        """Update the actual listbox content with visible items"""
        self.listbox.delete(0, tk.END)
        
        if self.total_items == 0:
            return
        
        # Get visible items from cache or data provider
        visible_items = self.get_visible_items()
        
        # Add items to listbox
        for item in visible_items:
            display_text = str(item) if not isinstance(item, dict) else item.get('display', str(item))
            self.listbox.insert(tk.END, display_text)
    
    def get_visible_items(self) -> List[Any]:
        """Get visible items, using cache when possible"""
        items = []
        
        for i in range(self.visible_start, self.visible_end):
            # Check cache first
            if i in self.cache:
                items.append(self.cache[i])
            else:
                # Get item from data provider
                try:
                    data = self.data_provider()
                    if i < len(data):
                        item = data[i]
                        
                        # Cache the item
                        if len(self.cache) < self.cache_size:
                            self.cache[i] = item
                        
                        items.append(item)
                except Exception as e:
                    print(f"Error getting item {i}: {e}")
                    continue
        
        return items
    
    def on_scroll(self, *args):
        """Handle scrollbar events"""
        # Update scrollbar
        self.scrollbar.set(*args)
        
        # Update visible content
        self.refresh()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.refresh()
    
    def on_keypress(self, event):
        """Handle keyboard navigation"""
        if event.keysym in ['Up', 'Down', 'Page_Up', 'Page_Down', 'Home', 'End']:
            self.parent.after_idle(self.refresh)
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs)


class OptimizedTreeview:
    """Optimized treeview with lazy loading and performance improvements"""
    
    def __init__(self, parent, columns: List[str], data_provider: Optional[Callable] = None):
        self.parent = parent
        self.columns = columns
        self.data_provider = data_provider or (lambda: [])
        
        # Create treeview
        self.tree = ttk.Treeview(parent, columns=columns, show='tree headings')
        self.setup_treeview()
        
        # Performance state
        self.loaded_ranges = set()
        self.item_cache = {}
        self.batch_size = 50
        self.loading = False
        
    def setup_treeview(self):
        """Setup treeview columns and scrollbars"""
        # Configure columns
        for col in self.columns:
            self.tree.heading(col, text=col.replace('_', ' ').title())
            self.tree.column(col, width=100)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.parent, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack widgets
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Bind scroll events
        self.tree.bind('<Configure>', self.on_tree_configure)
    
    def load_data_batch(self, start_index: int, end_index: int):
        """Load a batch of data asynchronously"""
        if self.loading:
            return
        
        self.loading = True
        
        def load_batch():
            try:
                data = self.data_provider()
                
                # Load items in the specified range
                for i in range(start_index, min(end_index, len(data))):
                    if i not in self.item_cache:
                        item_data = data[i]
                        
                        # Insert item into treeview
                        values = [str(item_data.get(col, '')) for col in self.columns]
                        item_id = self.tree.insert('', 'end', values=values)
                        
                        # Cache the item
                        self.item_cache[i] = {
                            'data': item_data,
                            'item_id': item_id
                        }
                
                # Mark range as loaded
                self.loaded_ranges.add((start_index, end_index))
                
            except Exception as e:
                print(f"Error loading batch {start_index}-{end_index}: {e}")
            finally:
                self.loading = False
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=load_batch)
        thread.daemon = True
        thread.start()
    
    def on_tree_configure(self, event):
        """Handle treeview configuration changes"""
        # Determine visible range and load data if needed
        visible_items = self.tree.get_children()
        
        if visible_items:
            # Check if we need to load more data
            try:
                data_length = len(self.data_provider())
                loaded_count = len(self.item_cache)
                
                if loaded_count < data_length and loaded_count < len(visible_items) + self.batch_size:
                    self.load_data_batch(loaded_count, loaded_count + self.batch_size)
            except:
                pass
    
    def refresh(self):
        """Refresh the treeview content"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear cache
        self.item_cache.clear()
        self.loaded_ranges.clear()
        
        # Load initial batch
        self.load_data_batch(0, self.batch_size)
    
    def filter_data(self, filter_func: Callable[[Dict], bool]):
        """Filter treeview data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            data = self.data_provider()
            filtered_data = [item for item in data if filter_func(item)]
            
            # Load filtered data
            for i, item_data in enumerate(filtered_data):
                values = [str(item_data.get(col, '')) for col in self.columns]
                self.tree.insert('', 'end', values=values)
                
        except Exception as e:
            print(f"Error filtering data: {e}")


class ProgressiveLoader:
    """Progressive loader for heavy operations with visual feedback"""
    
    def __init__(self, parent):
        self.parent = parent
        self.progress_window = None
        self.progress_bar = None
        self.status_label = None
        self.cancel_flag = threading.Event()
        
    def show_progress(self, title: str = "Loading..."):
        """Show progress dialog"""
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title(title)
        self.progress_window.geometry("300x120")
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        # Center the window
        self.progress_window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Create widgets
        self.status_label = ttk.Label(self.progress_window, text="Initializing...")
        self.status_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_window, 
            mode='determinate',
            length=250
        )
        self.progress_bar.pack(pady=10)
        
        # Cancel button
        cancel_button = ttk.Button(
            self.progress_window,
            text="Cancel",
            command=self.cancel_operation
        )
        cancel_button.pack(pady=5)
        
        # Prevent closing
        self.progress_window.protocol("WM_DELETE_WINDOW", self.cancel_operation)
    
    def update_progress(self, value: int, status: str = ""):
        """Update progress bar and status"""
        if self.progress_bar:
            self.progress_bar['value'] = value
        
        if self.status_label and status:
            self.status_label.config(text=status)
        
        if self.progress_window:
            self.progress_window.update()
    
    def cancel_operation(self):
        """Cancel the current operation"""
        self.cancel_flag.set()
        self.hide_progress()
    
    def hide_progress(self):
        """Hide progress dialog"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
            self.progress_bar = None
            self.status_label = None
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self.cancel_flag.is_set()
    
    def reset(self):
        """Reset the loader for reuse"""
        self.cancel_flag.clear()


class CachedFrame:
    """Frame with cached rendering for complex content"""
    
    def __init__(self, parent, cache_timeout: int = 300):
        self.parent = parent
        self.cache_timeout = cache_timeout
        self.frame = ttk.Frame(parent)
        
        # Cache state
        self.content_cache = {}
        self.last_render = {}
        self.pending_updates = set()
        
    def render_content(self, content_id: str, render_func: Callable, *args, **kwargs):
        """Render content with caching"""
        current_time = time.time()
        
        # Check if content is cached and still valid
        if (content_id in self.content_cache and 
            content_id in self.last_render and
            current_time - self.last_render[content_id] < self.cache_timeout):
            
            # Use cached content
            cached_widgets = self.content_cache[content_id]
            for widget in cached_widgets:
                if widget.winfo_exists():
                    widget.pack_forget()
                    widget.pack()
            return
        
        # Render new content
        try:
            # Clear previous content for this ID
            if content_id in self.content_cache:
                for widget in self.content_cache[content_id]:
                    if widget.winfo_exists():
                        widget.destroy()
            
            # Render new widgets
            new_widgets = render_func(self.frame, *args, **kwargs)
            
            # Cache the widgets
            self.content_cache[content_id] = new_widgets if isinstance(new_widgets, list) else [new_widgets]
            self.last_render[content_id] = current_time
            
        except Exception as e:
            print(f"Error rendering content {content_id}: {e}")
    
    def invalidate_cache(self, content_id: Optional[str] = None):
        """Invalidate cache for specific content or all content"""
        if content_id:
            if content_id in self.content_cache:
                del self.content_cache[content_id]
            if content_id in self.last_render:
                del self.last_render[content_id]
        else:
            self.content_cache.clear()
            self.last_render.clear()
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame"""
        self.frame.grid(**kwargs)