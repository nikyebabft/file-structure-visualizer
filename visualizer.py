import os
import sys
import threading
import queue
import time
from pathlib import Path
from typing import List, Optional, Dict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re

class TreeVisualizer:
    def __init__(self, show_hidden: bool = False, max_depth: Optional[int] = None, exclude_patterns: List[str] = None):
        self.show_hidden = show_hidden
        self.max_depth = max_depth
        self.exclude_patterns = exclude_patterns or ['__pycache__', '.git', '.DS_Store', '.pytest_cache', 'node_modules']
        
    def should_exclude(self, name: str) -> bool:
        if not self.show_hidden and name.startswith('.'):
            return True
        return any(pattern in name for pattern in self.exclude_patterns)
    
    def get_tree_lines(self, root_dir: Path, prefix: str = "", is_last: bool = True, depth: int = 0, progress_queue: Optional[queue.Queue] = None) -> List[str]:
        if self.max_depth is not None and depth > self.max_depth:
            return []
            
        try:
            items = list(root_dir.iterdir())
        except (PermissionError, OSError):
            return [f"{prefix}└── [Permission Denied]"]
        
        items = [item for item in items if not self.should_exclude(item.name)]
        
        if progress_queue:
            progress_queue.put(('progress', len(items)))
        
        dirs = sorted([item for item in items if item.is_dir()], key=lambda x: x.name.lower())
        files = sorted([item for item in items if item.is_file()], key=lambda x: x.name.lower())
        sorted_items = dirs + files
        
        lines = []
        
        for i, item in enumerate(sorted_items):
            is_last_item = (i == len(sorted_items) - 1)
            
            if is_last:
                connector = "└── " if is_last_item else "├── "
                next_prefix = prefix + "    "
            else:
                connector = "├── " if is_last_item else "├── "
                next_prefix = prefix + "│   "
            
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                child_lines = self.get_tree_lines(item, next_prefix, is_last_item, depth + 1, progress_queue)
                lines.extend(child_lines)
        
        return lines
    
    def visualize(self, root_path: Path, progress_queue: Optional[queue.Queue] = None) -> str:
        root_name = root_path.name if root_path.name else str(root_path)
        lines = [root_name + "/"]
        
        tree_lines = self.get_tree_lines(root_path, "", True, 0, progress_queue)
        lines.extend(tree_lines)
        
        return "\n".join(lines)
    
    def search_files(self, root_path: Path, search_pattern: str, progress_queue: Optional[queue.Queue] = None) -> List[Dict]:
        results = []
        search_lower = search_pattern.lower()
        
        if '*' in search_pattern or '?' in search_pattern:
            regex_pattern = search_lower.replace('.', '\\.')
            regex_pattern = regex_pattern.replace('*', '.*')
            regex_pattern = regex_pattern.replace('?', '.')
            regex_pattern = f"^{regex_pattern}$"
            pattern_re = re.compile(regex_pattern)
        else:
            pattern_re = None
        
        def search_recursive(current_path: Path, depth: int = 0):
            if self.max_depth is not None and depth > self.max_depth:
                return
                
            try:
                items = list(current_path.iterdir())
            except (PermissionError, OSError):
                return
            
            if progress_queue:
                progress_queue.put(('progress', len(items)))
            
            for item in items:
                if self.should_exclude(item.name):
                    continue
                    
                item_lower = item.name.lower()
                matches = False
                
                if pattern_re:
                    matches = pattern_re.search(item_lower) is not None
                else:
                    matches = search_lower in item_lower
                
                if matches:
                    rel_path = item.relative_to(root_path) if item != root_path else Path(item.name)
                    results.append({
                        'name': item.name,
                        'path': str(item),
                        'relative_path': str(rel_path),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': self._get_size(item) if item.is_file() else None,
                        'modified': self._get_modified_time(item)
                    })
                
                if item.is_dir():
                    search_recursive(item, depth + 1)
        
        search_recursive(root_path)
        return results
    
    def _get_size(self, file_path: Path) -> str:
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _get_modified_time(self, path: Path) -> str:
        try:
            mtime = path.stat().st_mtime
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        except:
            return "Unknown"

class FileStructureCreator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Structure Creator - .nikye.")
        self.root.geometry("1200x800")
        
        self.current_path = None
        self.visualizer = TreeVisualizer()
        self.progress_queue = queue.Queue()
        self.is_processing = False
        
        self.setup_gui()
        
    def setup_gui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_panel = ttk.Frame(main_container, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_panel, text="Folder Operations", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        ttk.Button(left_panel, text="📁 Select Folder", command=self.select_folder, width=25).pack(pady=5)
        
        self.path_label = ttk.Label(left_panel, text="No folder selected", wraplength=280, relief=tk.SUNKEN, padding=5)
        self.path_label.pack(pady=5, fill=tk.X)
        
        options_frame = ttk.LabelFrame(left_panel, text="Options", padding=10)
        options_frame.pack(pady=10, fill=tk.X)
        
        self.show_hidden_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Show hidden files", variable=self.show_hidden_var).pack(anchor=tk.W)
        
        ttk.Label(options_frame, text="Max depth:").pack(anchor=tk.W, pady=(5,0))
        self.depth_var = tk.StringVar(value="Unlimited")
        ttk.Combobox(options_frame, textvariable=self.depth_var, values=["Unlimited", "1", "2", "3", "4", "5", "10"], width=15, state="readonly").pack(anchor=tk.W, pady=2)
        
        ttk.Label(options_frame, text="Exclude patterns:").pack(anchor=tk.W, pady=(5,0))
        self.exclude_var = tk.StringVar(value=".git, __pycache__, node_modules")
        ttk.Entry(options_frame, textvariable=self.exclude_var, width=25).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        ttk.Label(left_panel, text="File Search", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Search pattern:").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=25).pack(fill=tk.X, pady=2)
        
        ttk.Button(search_frame, text="🔍 Search Files", command=self.search_files, width=25).pack(pady=5)
        
        self.search_info = ttk.Label(left_panel, text="", wraplength=280)
        self.search_info.pack(pady=5)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        ttk.Label(left_panel, text="Save Options", font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        ttk.Button(left_panel, text="💾 Save Structure As...", command=self.save_structure, width=25).pack(pady=5)
        
        self.save_status = ttk.Label(left_panel, text="", wraplength=280)
        self.save_status.pack(pady=5)
        
        credits = ttk.Label(left_panel, text="Created by .nikye. on Discord", font=('Arial', 8), foreground='gray')
        credits.pack(side=tk.BOTTOM, pady=10)
        
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        tree_tab = ttk.Frame(self.notebook)
        self.notebook.add(tree_tab, text="Tree View")
        
        tree_frame = ttk.Frame(tree_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree_text = scrolledtext.ScrolledText(tree_frame, wrap=tk.NONE, font=('Consolas', 10))
        self.tree_text.pack(fill=tk.BOTH, expand=True)
        
        search_tab = ttk.Frame(self.notebook)
        self.notebook.add(search_tab, text="Search Results")
        
        search_frame = ttk.Frame(search_tab)
        search_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('name', 'type', 'size', 'modified', 'relative_path')
        self.results_tree = ttk.Treeview(search_frame, columns=columns, show='headings')
        
        self.results_tree.heading('name', text='File Name')
        self.results_tree.heading('type', text='Type')
        self.results_tree.heading('size', text='Size')
        self.results_tree.heading('modified', text='Modified')
        self.results_tree.heading('relative_path', text='Relative Path')
        
        self.results_tree.column('name', width=200)
        self.results_tree.column('type', width=80)
        self.results_tree.column('size', width=80)
        self.results_tree.column('modified', width=120)
        self.results_tree.column('relative_path', width=300)
        
        scrollbar = ttk.Scrollbar(search_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree.bind('<Double-1>', self.open_result_location)
        
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.progress_label = ttk.Label(status_frame, text="")
        self.progress_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder to Visualize", initialdir=self.current_path or os.path.expanduser("~"))
        if folder_path:
            self.current_path = Path(folder_path)
            self.path_label.config(text=str(self.current_path))
            self.generate_tree()
    
    def generate_tree(self):
        if not self.current_path or self.is_processing:
            return
            
        self.is_processing = True
        self.status_label.config(text="Generating tree...")
        self.progress_bar.start()
        self.tree_text.delete(1.0, tk.END)
        self.tree_text.insert(tk.END, "Generating tree structure...\n")
        
        depth_str = self.depth_var.get()
        max_depth = None if depth_str == "Unlimited" else int(depth_str)
        
        exclude_patterns = [p.strip() for p in self.exclude_var.get().split(',') if p.strip()]
        
        self.visualizer = TreeVisualizer(
            show_hidden=self.show_hidden_var.get(),
            max_depth=max_depth,
            exclude_patterns=exclude_patterns
        )
        
        thread = threading.Thread(target=self._generate_tree_thread)
        thread.daemon = True
        thread.start()
        
        self.root.after(100, self._monitor_progress)
    
    def _generate_tree_thread(self):
        try:
            tree = self.visualizer.visualize(self.current_path, self.progress_queue)
            self.progress_queue.put(('done', tree))
        except Exception as e:
            self.progress_queue.put(('error', str(e)))
    
    def _monitor_progress(self):
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == 'progress':
                    pass
                elif msg_type == 'done':
                    self._update_tree_display(data)
                    break
                elif msg_type == 'error':
                    self._show_error(data)
                    break
                    
        except queue.Empty:
            if self.is_processing:
                self.root.after(100, self._monitor_progress)
    
    def _update_tree_display(self, tree_text):
        self.tree_text.delete(1.0, tk.END)
        self.tree_text.insert(tk.END, tree_text)
        
        self.tree_text.tag_configure('directory', foreground='blue')
        self.tree_text.tag_configure('python', foreground='green')
        self.tree_text.tag_configure('javascript', foreground='orange')
        self.tree_text.tag_configure('html', foreground='red')
        self.tree_text.tag_configure('css', foreground='purple')
        self.tree_text.tag_configure('markdown', foreground='darkblue')
        self.tree_text.tag_configure('config', foreground='brown')
        
        content = self.tree_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if '/' in line and line.strip().endswith('/'):
                start_idx = f"{i}.0"
                end_idx = f"{i}.end"
                self.tree_text.tag_add('directory', start_idx, end_idx)
            elif any(ext in line.lower() for ext in ['.py', '.pyw']):
                self.tree_text.tag_add('python', f"{i}.0", f"{i}.end")
            elif any(ext in line.lower() for ext in ['.js', '.jsx', '.ts', '.tsx']):
                self.tree_text.tag_add('javascript', f"{i}.0", f"{i}.end")
            elif any(ext in line.lower() for ext in ['.html', '.htm']):
                self.tree_text.tag_add('html', f"{i}.0", f"{i}.end")
            elif '.css' in line.lower():
                self.tree_text.tag_add('css', f"{i}.0", f"{i}.end")
            elif any(ext in line.lower() for ext in ['.md', '.markdown']):
                self.tree_text.tag_add('markdown', f"{i}.0", f"{i}.end")
            elif any(ext in line.lower() for ext in ['.json', '.yaml', '.yml', '.toml', '.ini']):
                self.tree_text.tag_add('config', f"{i}.0", f"{i}.end")
        
        self.status_label.config(text="Tree generated successfully")
        self.progress_bar.stop()
        self.is_processing = False
        self.progress_label.config(text="")
        
        self.notebook.select(0)
    
    def search_files(self):
        if not self.current_path:
            messagebox.showwarning("No Folder", "Please select a folder first.")
            return
            
        search_pattern = self.search_var.get().strip()
        if not search_pattern:
            messagebox.showwarning("No Pattern", "Please enter a search pattern.")
            return
            
        self.is_processing = True
        self.status_label.config(text=f"Searching for '{search_pattern}'...")
        self.progress_bar.start()
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        depth_str = self.depth_var.get()
        max_depth = None if depth_str == "Unlimited" else int(depth_str)
        
        self.visualizer.max_depth = max_depth
        
        thread = threading.Thread(target=self._search_files_thread, args=(search_pattern,))
        thread.daemon = True
        thread.start()
        
        self.root.after(100, self._monitor_search_progress)
    
    def _search_files_thread(self, search_pattern):
        try:
            results = self.visualizer.search_files(self.current_path, search_pattern, self.progress_queue)
            self.progress_queue.put(('search_done', results))
        except Exception as e:
            self.progress_queue.put(('error', str(e)))
    
    def _monitor_search_progress(self):
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == 'progress':
                    pass
                elif msg_type == 'search_done':
                    self._update_search_results(data)
                    break
                elif msg_type == 'error':
                    self._show_error(data)
                    break
                    
        except queue.Empty:
            if self.is_processing:
                self.root.after(100, self._monitor_search_progress)
    
    def _update_search_results(self, results):
        self.status_label.config(text=f"Found {len(results)} results")
        self.progress_bar.stop()
        self.is_processing = False
        
        self.search_info.config(text=f"Found {len(results)} matches\nPattern: {self.search_var.get()}\nFolder: {self.current_path.name}")
        
        for result in results:
            self.results_tree.insert('', tk.END, values=(
                result['name'],
                result['type'],
                result['size'] or '',
                result['modified'],
                result['relative_path']
            ))
        
        self.notebook.select(1)
    
    def open_result_location(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return
            
        item = self.results_tree.item(selection[0])
        values = item['values']
        if values:
            file_path = values[4]
            full_path = self.current_path / file_path
            
            try:
                if sys.platform == 'win32':
                    os.startfile(full_path.parent)
                elif sys.platform == 'darwin':
                    os.system(f'open "{full_path.parent}"')
                else:
                    os.system(f'xdg-open "{full_path.parent}"')
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open location: {e}")
    
    def save_structure(self):
        if not self.current_path:
            messagebox.showwarning("No Tree", "Please generate a tree first.")
            return
        
        default_name = f"{self.current_path.name}_structure.txt"
        file_path = filedialog.asksaveasfilename(
            title="Save Tree Structure",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path):
        self.status_label.config(text="Saving to file...")
        self.progress_bar.start()
        
        def save_thread():
            try:
                tree_text = self.tree_text.get(1.0, tk.END)
                
                metadata = f"""# File Structure Creator - Created by .nikye. on Discord
# GitHub: https://github.com/nikyebabft
# 
# File Structure: {self.current_path}
# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Options: {'Show hidden' if self.visualizer.show_hidden else 'Hide hidden'}, Max depth: {self.visualizer.max_depth or 'Unlimited'}

"""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(metadata + tree_text)
                
                self.progress_queue.put(('save_done', file_path))
            except Exception as e:
                self.progress_queue.put(('error', str(e)))
        
        thread = threading.Thread(target=save_thread)
        thread.daemon = True
        thread.start()
        
        self.root.after(100, self._monitor_save_progress)
    
    def _monitor_save_progress(self):
        try:
            msg_type, data = self.progress_queue.get_nowait()
            
            if msg_type == 'save_done':
                self.status_label.config(text="File saved successfully")
                self.progress_bar.stop()
                self.save_status.config(text=f"Saved to:\n{data}")
                messagebox.showinfo("Success", f"Structure saved to:\n{data}")
            elif msg_type == 'error':
                self._show_error(data)
                
        except queue.Empty:
            self.root.after(100, self._monitor_save_progress)
    
    def _show_error(self, error_msg):
        self.status_label.config(text="Error occurred")
        self.progress_bar.stop()
        self.is_processing = False
        messagebox.showerror("Error", str(error_msg))
    
    def run(self):
        self.root.mainloop()

def main():
    app = FileStructureCreator()
    app.run()

if __name__ == "__main__":
    main()
