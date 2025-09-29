import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
from PIL import Image
import os
from pathlib import Path
import threading


class VideoPosterGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Poster Generator")
        self.root.geometry("800x600")
        
        # Video queue
        self.video_queue = []
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Video Poster Generator", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Frame position setting (as percentage)
        ttk.Label(settings_frame, text="Frame Position (%):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.position_var = tk.DoubleVar(value=25.0)
        position_frame = ttk.Frame(settings_frame)
        position_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        position_scale = ttk.Scale(position_frame, from_=0, to=100, 
                                   variable=self.position_var, orient=tk.HORIZONTAL,
                                   command=self.round_position)
        position_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        position_frame.columnconfigure(0, weight=1)
        
        # Clickable entry for manual input
        position_entry = ttk.Entry(position_frame, textvariable=self.position_var, width=6)
        position_entry.grid(row=0, column=1, padx=(5, 0))
        position_entry.bind('<Return>', lambda e: self.validate_position())
        position_entry.bind('<FocusOut>', lambda e: self.validate_position())
        
        ttk.Label(settings_frame, text="(25% = 0.25s into 1s video, 2s into 8s video)").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # JPEG Quality setting
        ttk.Label(settings_frame, text="JPEG Quality:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        # Quality presets with radio buttons
        self.quality_var = tk.IntVar(value=85)
        self.quality_preset_var = tk.StringVar(value="custom")
        
        quality_main_frame = ttk.Frame(settings_frame)
        quality_main_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Radio buttons for presets
        presets_frame = ttk.Frame(quality_main_frame)
        presets_frame.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Radiobutton(presets_frame, text="Low (60)", variable=self.quality_preset_var, 
                       value="low", command=lambda: self.set_quality_preset(60)).grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="Medium (75)", variable=self.quality_preset_var, 
                       value="medium", command=lambda: self.set_quality_preset(75)).grid(row=0, column=1, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="High (85)", variable=self.quality_preset_var, 
                       value="high", command=lambda: self.set_quality_preset(85)).grid(row=0, column=2, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="Maximum (95)", variable=self.quality_preset_var, 
                       value="maximum", command=lambda: self.set_quality_preset(95)).grid(row=0, column=3, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="Custom", variable=self.quality_preset_var, 
                       value="custom", command=self.enable_quality_slider).grid(row=0, column=4)
        
        # Slider for custom quality
        quality_slider_frame = ttk.Frame(quality_main_frame)
        quality_slider_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        quality_slider_frame.columnconfigure(0, weight=1)
        
        self.quality_scale = ttk.Scale(quality_slider_frame, from_=1, to=100, 
                                      variable=self.quality_var, orient=tk.HORIZONTAL,
                                      command=self.round_quality)
        self.quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Clickable entry for manual input
        self.quality_entry = ttk.Entry(quality_slider_frame, textvariable=self.quality_var, width=6)
        self.quality_entry.grid(row=0, column=1, padx=(5, 0))
        self.quality_entry.bind('<Return>', lambda e: self.validate_quality())
        self.quality_entry.bind('<FocusOut>', lambda e: self.validate_quality())
        self.quality_entry.bind('<KeyPress>', lambda e: self.on_quality_manual_edit())
        
        # Output size override
        ttk.Label(settings_frame, text="Output Size (optional):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        size_frame = ttk.Frame(settings_frame)
        size_frame.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0)
        ttk.Entry(size_frame, textvariable=self.width_var, width=8).grid(row=0, column=1, padx=(5, 10))
        ttk.Label(size_frame, text="Height:").grid(row=0, column=2)
        ttk.Entry(size_frame, textvariable=self.height_var, width=8).grid(row=0, column=3, padx=(5, 0))
        ttk.Label(size_frame, text="(leave blank for original size)").grid(row=0, column=4, padx=(10, 0))
        
        # Drop Zone Frame
        drop_frame = ttk.LabelFrame(main_frame, text="Drop Video Files Here or Click to Browse", padding="10")
        drop_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        drop_frame.columnconfigure(0, weight=1)
        drop_frame.rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(drop_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.video_listbox = tk.Listbox(list_frame, height=10)
        self.video_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.video_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.video_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Enable drag and drop
        self.video_listbox.drop_target_register(DND_FILES)
        self.video_listbox.dnd_bind('<<Drop>>', self.drop_files)
        
        # Click to browse
        self.video_listbox.bind('<Double-Button-1>', lambda e: self.browse_files())
        
        # Button frame
        button_frame = ttk.Frame(drop_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="Browse Files", command=self.browse_files).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Clear Queue", command=self.clear_queue).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=2, padx=5)
        
        # Progress Frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Process Button
        self.process_button = ttk.Button(main_frame, text="Generate Posters", 
                                        command=self.process_videos, style='Accent.TButton')
        self.process_button.grid(row=4, column=0)
        
    def round_position(self, value):
        """Round position slider to nearest whole number"""
        rounded = round(float(value))
        self.position_var.set(rounded)
        
    def validate_position(self):
        """Validate and constrain position input"""
        try:
            value = float(self.position_var.get())
            value = max(0, min(100, value))  # Constrain to 0-100
            self.position_var.set(round(value))
        except (ValueError, tk.TclError):
            self.position_var.set(25)  # Reset to default
            
    def round_quality(self, value):
        """Round quality slider to nearest whole number"""
        rounded = round(float(value))
        self.quality_var.set(rounded)
        self.quality_preset_var.set("custom")  # Switch to custom when slider moved
        
    def validate_quality(self):
        """Validate and constrain quality input"""
        try:
            value = int(self.quality_var.get())
            value = max(1, min(100, value))  # Constrain to 1-100
            self.quality_var.set(value)
            self.quality_preset_var.set("custom")
        except (ValueError, tk.TclError):
            self.quality_var.set(85)  # Reset to default
            
    def set_quality_preset(self, quality_value):
        """Set quality to preset value"""
        self.quality_var.set(quality_value)
        
    def enable_quality_slider(self):
        """Enable custom quality slider when custom is selected"""
        # This allows the slider to be used when custom is selected
        pass
        
    def on_quality_manual_edit(self):
        """Switch to custom mode when quality is manually edited"""
        self.quality_preset_var.set("custom")
        
    def drop_files(self, event):
        """Handle dropped files"""
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)
        
    def browse_files(self):
        """Browse for video files"""
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if files:
            self.add_files(files)
            
    def add_files(self, files):
        """Add files to the queue"""
        for file in files:
            file = file.strip('{}')  # Remove curly braces from drag-drop
            if file.lower().endswith('.mp4') and file not in self.video_queue:
                self.video_queue.append(file)
                self.video_listbox.insert(tk.END, os.path.basename(file))
                
    def clear_queue(self):
        """Clear all videos from queue"""
        self.video_queue.clear()
        self.video_listbox.delete(0, tk.END)
        
    def remove_selected(self):
        """Remove selected items from queue"""
        selected = self.video_listbox.curselection()
        for index in reversed(selected):
            self.video_queue.pop(index)
            self.video_listbox.delete(index)
            
    def is_split_screen(self, width, height):
        """Detect if video is split-screen format (width ≈ 2x height)"""
        ratio = width / height if height > 0 else 0
        return ratio >= 1.8  # Auto-detect split screen
        
    def extract_poster(self, video_path, position_percent, quality, output_size=None):
        """Extract poster frame from video"""
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return False, "Could not open video file"
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0 or fps <= 0:
                cap.release()
                return False, "Invalid video properties"
            
            # Calculate frame number based on percentage
            frame_number = int((position_percent / 100.0) * total_frames)
            # Ensure frame number is within bounds
            frame_number = max(0, min(frame_number, total_frames - 1))
                
            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Could not read frame at specified position"
                
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = frame.shape[:2]
            
            # Check for split-screen and crop if needed
            if self.is_split_screen(width, height):
                frame = frame[:, :width//2]  # Take left 50%
                
            # Convert to PIL Image
            img = Image.fromarray(frame)
            
            # Resize if output size specified
            if output_size:
                img = img.resize(output_size, Image.LANCZOS)
                
            # Generate output filename
            path = Path(video_path)
            output_path = path.parent / f"{path.stem}-poster.jpg"
            
            # Save as JPEG with specified quality
            img.save(output_path, 'JPEG', quality=quality)
            
            return True, str(output_path)
            
        except Exception as e:
            return False, str(e)
            
    def process_videos(self):
        """Process all videos in queue"""
        if not self.video_queue:
            messagebox.showwarning("No Videos", "Please add video files to the queue.")
            return
            
        # Disable process button during processing
        self.process_button.config(state='disabled')
        
        # Run processing in separate thread
        thread = threading.Thread(target=self.process_thread)
        thread.daemon = True
        thread.start()
        
    def process_thread(self):
        """Thread for processing videos"""
        total = len(self.video_queue)
        success_count = 0
        errors = []
        
        # Get settings
        position_percent = self.position_var.get()
        quality = self.quality_var.get()
        
        # Get output size if specified
        output_size = None
        try:
            width = self.width_var.get().strip()
            height = self.height_var.get().strip()
            if width and height:
                output_size = (int(width), int(height))
        except (ValueError, AttributeError):
            pass
            
        for i, video_path in enumerate(self.video_queue):
            # Update status
            self.status_label.config(text=f"Processing: {os.path.basename(video_path)}")
            
            # Process video
            success, result = self.extract_poster(video_path, position_percent, quality, output_size)
            
            if success:
                success_count += 1
            else:
                errors.append(f"{os.path.basename(video_path)}: {result}")
                
            # Update progress
            progress = ((i + 1) / total) * 100
            self.progress_var.set(progress)
            
        # Processing complete
        self.status_label.config(text=f"Complete: {success_count}/{total} successful")
        self.process_button.config(state='normal')
        
        # Show results
        if errors:
            error_msg = "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"
            messagebox.showwarning("Processing Complete with Errors", 
                                 f"Successfully processed {success_count}/{total} videos.\n\nErrors:\n{error_msg}")
        else:
            messagebox.showinfo("Success", f"Successfully generated {success_count} poster images!")


def main():
    root = TkinterDnD.Tk()
    app = VideoPosterGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()