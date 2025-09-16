#!/usr/bin/env python3
"""
ArchiveMaster: Interactive Multi-Archive Merger Toolkit
Combines multiple RAR, ZIP, and TAR archives into a single unified archive.
Supports GUI and CLI modes with progress tracking, validation, and compression control.
Coded By: Scav-engeR
"""
import os
import sys
import shutil
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import zipfile
import tarfile
import rarfile
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ArchiveInfo:
    path: Path
    type: str  # 'zip', 'rar', 'tar'
    size: int
    member_count: int
    files: List[str]

class ArchiveMerger:
    def __init__(self, output_path: Path, compression_level: int = 6):
        self.output_path = output_path
        self.compression_level = compression_level
        self.temp_dir = None
        self.extracted_files = []
        self.total_files = 0
        self.processed_files = 0
        self.lock = threading.Lock()
        
    def __enter__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="archivemaster_"))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def extract_rar(self, rar_path: Path) -> List[str]:
        """Extract all files from RAR archive to temp directory."""
        logger.info(f"Extracting RAR: {rar_path}")
        extracted = []
        try:
            with rarfile.RarFile(rar_path) as rf:
                for member in rf.namelist():
                    if not member.endswith('/'):  # Skip directories
                        extracted.append(member)
                        target_path = self.temp_dir / member
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with rf.open(member) as source, open(target_path, 'wb') as dest:
                            shutil.copyfileobj(source, dest)
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract RAR {rar_path}: {e}")
            raise
    
    def extract_zip(self, zip_path: Path) -> List[str]:
        """Extract all files from ZIP archive to temp directory."""
        logger.info(f"Extracting ZIP: {zip_path}")
        extracted = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    if not member.endswith('/'):
                        extracted.append(member)
                        target_path = self.temp_dir / member
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as source, open(target_path, 'wb') as dest:
                            shutil.copyfileobj(source, dest)
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract ZIP {zip_path}: {e}")
            raise
    
    def extract_tar(self, tar_path: Path) -> List[str]:
        """Extract all files from TAR archive to temp directory."""
        logger.info(f"Extracting TAR: {tar_path}")
        extracted = []
        try:
            with tarfile.open(tar_path, 'r') as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        extracted.append(member.name)
                        target_path = self.temp_dir / member.name
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        tf.extract(member, self.temp_dir)
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract TAR {tar_path}: {e}")
            raise
    
    def create_output_archive(self, archive_type: str, compression: str = 'deflate'):
        """Create final combined archive from extracted files."""
        logger.info(f"Creating {archive_type.upper()} output: {self.output_path}")
        
        if archive_type == 'zip':
            with zipfile.ZipFile(
                self.output_path, 
                'w', 
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=self.compression_level
            ) as zf:
                for file_path in sorted(self.extracted_files):
                    relative_path = file_path.relative_to(self.temp_dir)
                    zf.write(file_path, relative_path)
                    
        elif archive_type == 'tar':
            with tarfile.open(self.output_path, 'w:gz' if compression == 'gzip' else 'w') as tf:
                for file_path in sorted(self.extracted_files):
                    relative_path = file_path.relative_to(self.temp_dir)
                    tf.add(file_path, arcname=relative_path)
                    
        elif archive_type == 'tar.gz':
            with tarfile.open(self.output_path, 'w:gz') as tf:
                for file_path in sorted(self.extracted_files):
                    relative_path = file_path.relative_to(self.temp_dir)
                    tf.add(file_path, arcname=relative_path)
                    
        elif archive_type == 'tar.bz2':
            with tarfile.open(self.output_path, 'w:bz2') as tf:
                for file_path in sorted(self.extracted_files):
                    relative_path = file_path.relative_to(self.temp_dir)
                    tf.add(file_path, arcname=relative_path)

    def process_archives(self, archive_paths: List[Path], output_type: str = 'zip', compression: str = 'deflate') -> Dict:
        """Main method to combine multiple archives into one."""
        start_time = time.time()
        self.extracted_files = []
        
        # Determine total files across all archives
        total_files = 0
        for archive_path in archive_paths:
            if archive_path.suffix.lower() == '.rar':
                with rarfile.RarFile(archive_path) as rf:
                    total_files += len([m for m in rf.namelist() if not m.endswith('/')])
            elif archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    total_files += len([m for m in zf.namelist() if not m.endswith('/')])
            elif archive_path.suffix.lower() in ['.tar', '.tgz', '.tar.gz', '.tbz2', '.tar.bz2']:
                with tarfile.open(archive_path, 'r') as tf:
                    total_files += len([m for m in tf.getmembers() if m.isfile()])
        
        self.total_files = total_files
        self.processed_files = 0
        
        # Extract each archive
        for archive_path in archive_paths:
            ext = archive_path.suffix.lower()
            if ext == '.rar':
                extracted = self.extract_rar(archive_path)
            elif ext == '.zip':
                extracted = self.extract_zip(archive_path)
            elif ext in ['.tar', '.tgz', '.tar.gz', '.tbz2', '.tar.bz2']:
                extracted = self.extract_tar(archive_path)
            else:
                raise ValueError(f"Unsupported archive format: {ext}")
            
            # Add extracted file paths to our list
            for fname in extracted:
                full_path = self.temp_dir / fname
                if full_path.exists():
                    self.extracted_files.append(full_path)
            
            # Update progress
            with self.lock:
                self.processed_files += len(extracted)
        
        # Create final archive
        self.create_output_archive(output_type, compression)
        
        end_time = time.time()
        return {
            'success': True,
            'output_file': self.output_path,
            'total_input_files': len(archive_paths),
            'total_extracted_files': len(self.extracted_files),
            'elapsed_seconds': round(end_time - start_time, 2),
            'output_size_bytes': self.output_path.stat().st_size
        }

class ArchiveMasterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ArchiveMaster - Multi-Archive Merger")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Application state
        self.archive_files = []
        self.output_type = tk.StringVar(value="zip")
        self.compression = tk.StringVar(value="deflate")
        self.compression_level = tk.IntVar(value=6)
        self.is_processing = False
        self.merger = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="ArchiveMaster", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input Files Section
        input_frame = ttk.LabelFrame(main_frame, text="Input Archives", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)
        
        # File listbox with scrollbar
        listbox_frame = ttk.Frame(input_frame)
        listbox_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Buttons for file management
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Add Files", command=self.add_files).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Open Folder", command=self.open_folder).grid(row=0, column=3, padx=5)
        
        # Output Settings
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Output format
        ttk.Label(output_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        format_options = ['zip', 'tar', 'tar.gz', 'tar.bz2']
        ttk.OptionMenu(output_frame, self.output_type, self.output_type.get(), *format_options).grid(row=0, column=1, sticky=tk.W)
        
        # Compression level
        ttk.Label(output_frame, text="Compression Level (1-9):").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        compression_scale = ttk.Scale(output_frame, from_=1, to=9, variable=self.compression_level, orient=tk.HORIZONTAL, length=100)
        compression_scale.grid(row=0, column=3, sticky=tk.W, padx=(5, 10))
        self.level_label = ttk.Label(output_frame, text=f"{self.compression_level.get()}")
        self.level_label.grid(row=0, column=4, sticky=tk.W)
        
        compression_scale.bind("<B1-Motion>", lambda e: self.update_level_label())
        compression_scale.bind("<ButtonRelease-1>", lambda e: self.update_level_label())
        
        # Compression type
        ttk.Label(output_frame, text="Compression Type:").grid(row=0, column=5, sticky=tk.W, padx=(20, 10))
        comp_options = ['deflate', 'gzip', 'bzip2']
        ttk.OptionMenu(output_frame, self.compression, self.compression.get(), *comp_options).grid(row=0, column=6, sticky=tk.W)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_text = scrolledtext.ScrolledText(progress_frame, height=8, state='disabled')
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        self.start_button = ttk.Button(action_frame, text="Merge Archives", command=self.start_merge)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self.cancel_merge, state='disabled')
        self.cancel_button.grid(row=0, column=1, padx=5)
        
        self.save_button = ttk.Button(action_frame, text="Save Log", command=self.save_log)
        self.save_button.grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind events
        self.root.bind('<Control-o>', lambda e: self.add_files())
        self.root.bind('<Control-c>', lambda e: self.clear_all())
        self.root.bind('<Return>', lambda e: self.start_merge() if not self.is_processing else None)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def update_level_label(self):
        self.level_label.config(text=str(self.compression_level.get()))
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Archive Files",
            filetypes=[
                ("Archive Files", "*.zip *.rar *.tar *.tgz *.tar.gz *.tbz2 *.tar.bz2"),
                ("ZIP Files", "*.zip"),
                ("RAR Files", "*.rar"),
                ("TAR Files", "*.tar *.tgz *.tar.gz *.tbz2 *.tar.bz2"),
                ("All Files", "*.*")
            ]
        )
        
        for file_path in files:
            path = Path(file_path)
            if path.exists() and path.suffix.lower() in ['.zip', '.rar', '.tar', '.tgz', '.tar.gz', '.tbz2', '.tar.bz2']:
                if path not in self.archive_files:
                    self.archive_files.append(path)
                    self.file_listbox.insert(tk.END, path.name)
                    self.status_bar.config(text=f"Added {path.name}")
    
    def remove_selected(self):
        selected_indices = list(self.file_listbox.curselection())
        if not selected_indices:
            return
            
        for idx in reversed(selected_indices):
            self.file_listbox.delete(idx)
            self.archive_files.pop(idx)
        
        self.status_bar.config(text=f"Removed {len(selected_indices)} file(s)")
    
    def clear_all(self):
        self.file_listbox.delete(0, tk.END)
        self.archive_files.clear()
        self.status_bar.config(text="Cleared all files")
    
    def open_folder(self):
        if self.archive_files:
            folder = self.archive_files[0].parent
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
    
    def log_message(self, message: str):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
    
    def set_progress(self, value: float):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def start_merge(self):
        if not self.archive_files:
            messagebox.showwarning("No Files", "Please add at least one archive file.")
            return
            
        if self.is_processing:
            return
            
        self.is_processing = True
        self.start_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state='disabled')
        self.progress_var.set(0)
        
        # Run merge in background thread
        threading.Thread(target=self._merge_thread, daemon=True).start()
    
    def _merge_thread(self):
        try:
            output_ext = self.output_type.get()
            output_path = filedialog.asksaveasfilename(
                title="Save Combined Archive",
                defaultextension=f".{output_ext}",
                filetypes=[
                    ("ZIP Archive", "*.zip"),
                    ("TAR Archive", "*.tar"),
                    ("TAR.GZ Archive", "*.tar.gz"),
                    ("TAR.BZ2 Archive", "*.tar.bz2"),
                    ("All Files", "*.*")
                ],
                initialfile=f"combined_archive.{output_ext}"
            )
            
            if not output_path:
                self.log_message("Operation cancelled by user.")
                self.cleanup_after_operation()
                return
                
            output_path = Path(output_path)
            
            # Validate output path
            if output_path.exists():
                if not messagebox.askyesno("Overwrite?", f"{output_path} already exists. Overwrite?"):
                    self.log_message("Operation cancelled by user.")
                    self.cleanup_after_operation()
                    return
            
            # Create merger instance
            with ArchiveMerger(output_path, self.compression_level.get()) as merger:
                self.log_message(f"Starting merge of {len(self.archive_files)} archives...")
                self.log_message(f"Output format: {output_ext}, Compression: {self.compression.get()}, Level: {self.compression_level.get()}")
                
                result = merger.process_archives(
                    self.archive_files, 
                    output_type=output_ext, 
                    compression=self.compression.get()
                )
                
                if result['success']:
                    self.log_message(f"✓ Success! Created: {result['output_file']}")
                    self.log_message(f"  Total input archives: {result['total_input_files']}")
                    self.log_message(f"  Total files extracted: {result['total_extracted_files']}")
                    self.log_message(f"  Output size: {result['output_size_bytes']:,} bytes ({result['output_size_bytes']/1024/1024:.2f} MB)")
                    self.log_message(f"  Elapsed time: {result['elapsed_seconds']} seconds")
                    
                    # Show success dialog
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Combined archive created successfully!\n\n{result['output_file']}"))
                    
                else:
                    raise Exception("Merge failed")
                    
        except Exception as e:
            error_msg = f"✗ Error during merge: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{str(e)}"))
        
        finally:
            self.root.after(0, self.cleanup_after_operation)
    
    def cleanup_after_operation(self):
        self.is_processing = False
        self.start_button.config(state='normal')
        self.cancel_button.config(state='disabled')
        self.set_progress(100)
        self.status_bar.config(text="Operation completed")
    
    def cancel_merge(self):
        if self.is_processing:
            self.log_message("Cancelling operation...")
            self.is_processing = False
            self.cancel_button.config(state='disabled')
            # Note: Cannot truly interrupt the underlying process, but will stop further processing after current step
            self.status_bar.config(text="Cancelling...")
    
    def save_log(self):
        content = self.status_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("Empty Log", "No log content to save.")
            return
            
        save_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Saved", f"Log saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save log: {str(e)}")
    
    def on_closing(self):
        if self.is_processing:
            if messagebox.askokcancel("Quit", "Processing is in progress. Are you sure you want to quit?"):
                self.root.destroy()
        else:
            self.root.destroy()

def cli_mode():
    """Command-line interface mode for ArchiveMaster"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ArchiveMaster - Combine multiple archive files")
    parser.add_argument('inputs', nargs='+', help='Input archive files (.zip, .rar, .tar, etc.)')
    parser.add_argument('-o', '--output', required=True, help='Output archive file path')
    parser.add_argument('-f', '--format', choices=['zip', 'tar', 'tar.gz', 'tar.bz2'], default='zip',
                       help='Output format (default: zip)')
    parser.add_argument('-c', '--compression', choices=['deflate', 'gzip', 'bzip2'], default='deflate',
                       help='Compression type (default: deflate)')
    parser.add_argument('-l', '--level', type=int, default=6, choices=range(1, 10),
                       help='Compression level (1-9, default: 6)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Validate inputs
    for f in args.inputs:
        if not Path(f).exists():
            print(f"Error: Input file does not exist: {f}")
            sys.exit(1)
    
    # Check output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge archives
    try:
        with ArchiveMerger(output_path, args.level) as merger:
            result = merger.process_archives(
                [Path(f) for f in args.inputs],
                output_type=args.format,
                compression=args.compression
            )
            
            print(f"\n✅ Success!")
            print(f"   Output: {result['output_file']}")
            print(f"   Files: {result['total_extracted_files']}")
            print(f"   Size: {result['output_size_bytes']:,} bytes ({result['output_size_bytes']/1024/1024:.2f} MB)")
            print(f"   Time: {result['elapsed_seconds']} seconds")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if running with command line arguments
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        cli_mode()
    else:
        # Start GUI
        root = tk.Tk()
        # Apply theme for better appearance
        try:
            style = ttk.Style()
            style.theme_use('clam')  # Modern theme
        except:
            pass
        app = ArchiveMasterGUI(root)
        root.mainloop()
