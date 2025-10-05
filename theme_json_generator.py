import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
from PIL import Image
import os
import json
import re
from pathlib import Path
import threading
import xml.etree.ElementTree as ET


class ThemeJSONGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Theme JSON Generator")
        self.root.geometry("900x700")
        
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
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Theme JSON Generator", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Base URL Path
        ttk.Label(settings_frame, text="Base URL Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.base_url_var = tk.StringVar(value="./assets/media/")
        url_entry = ttk.Entry(settings_frame, textvariable=self.base_url_var)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Label(settings_frame, text="(e.g., ./assets/media/theme-name/)").grid(row=0, column=2, sticky=tk.W)
        
        # Frame position setting
        ttk.Label(settings_frame, text="Poster Frame Position (%):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.position_var = tk.IntVar(value=25)
        position_frame = ttk.Frame(settings_frame)
        position_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        position_scale = ttk.Scale(position_frame, from_=0, to=100, 
                                   variable=self.position_var, orient=tk.HORIZONTAL,
                                   command=lambda v: self.position_var.set(round(float(v))))
        position_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        position_frame.columnconfigure(0, weight=1)
        position_entry = ttk.Entry(position_frame, textvariable=self.position_var, width=6)
        position_entry.grid(row=0, column=1, padx=(5, 0))
        
        # JPEG Quality presets
        ttk.Label(settings_frame, text="JPEG Quality:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.quality_var = tk.IntVar(value=85)
        self.quality_preset_var = tk.StringVar(value="high")
        
        quality_main_frame = ttk.Frame(settings_frame)
        quality_main_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Radio buttons
        presets_frame = ttk.Frame(quality_main_frame)
        presets_frame.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Radiobutton(presets_frame, text="Low (60)", variable=self.quality_preset_var,
                       value="low", command=lambda: self.set_quality_preset(60)).grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="Medium (75)", variable=self.quality_preset_var,
                       value="medium", command=lambda: self.set_quality_preset(75)).grid(row=0, column=1, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="High (85)", variable=self.quality_preset_var,
                       value="high", command=lambda: self.set_quality_preset(85)).grid(row=0, column=2, padx=(0, 10))
        ttk.Radiobutton(presets_frame, text="Max (95)", variable=self.quality_preset_var,
                       value="max", command=lambda: self.set_quality_preset(95)).grid(row=0, column=3)
        
        # Slider
        quality_slider_frame = ttk.Frame(quality_main_frame)
        quality_slider_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        quality_slider_frame.columnconfigure(0, weight=1)
        
        self.quality_scale = ttk.Scale(quality_slider_frame, from_=1, to=100,
                                      variable=self.quality_var, orient=tk.HORIZONTAL,
                                      command=lambda v: self.on_quality_slider_change(v))
        self.quality_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.quality_entry = ttk.Entry(quality_slider_frame, textvariable=self.quality_var, width=6)
        self.quality_entry.grid(row=0, column=1, padx=(5, 0))
        
        # Output size override
        ttk.Label(settings_frame, text="Poster Size:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        size_frame = ttk.Frame(settings_frame)
        size_frame.grid(row=3, column=1, sticky=tk.W, pady=(10, 0))
        
        self.width_var = tk.StringVar(value="640")
        self.height_var = tk.StringVar(value="360")
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0)
        ttk.Entry(size_frame, textvariable=self.width_var, width=8).grid(row=0, column=1, padx=(5, 10))
        ttk.Label(size_frame, text="Height:").grid(row=0, column=2)
        ttk.Entry(size_frame, textvariable=self.height_var, width=8).grid(row=0, column=3, padx=(5, 0))
        ttk.Label(size_frame, text="(default 640x360)").grid(row=0, column=4, padx=(10, 0))
        
        # Append mode checkbox
        self.append_mode_var = tk.BooleanVar(value=False)
        append_check = ttk.Checkbutton(settings_frame, text="Append to existing theme JSON (auto-detects in folder)",
                                      variable=self.append_mode_var)
        append_check.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        # Drop Zone Frame
        drop_frame = ttk.LabelFrame(main_frame, text="Drop Video Files Here or Click to Browse", padding="10")
        drop_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
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
        self.video_listbox.bind('<Double-Button-1>', lambda e: self.browse_files())
        
        # Button frame
        button_frame = ttk.Frame(drop_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(button_frame, text="Browse Files", command=self.browse_files).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Clear Queue", command=self.clear_queue).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).grid(row=0, column=2, padx=5)
        
        # Progress Frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Process Button
        button_row = ttk.Frame(main_frame)
        button_row.grid(row=5, column=0)
        
        self.process_button = ttk.Button(button_row, text="Generate Theme JSON & Posters", 
                                        command=self.process_videos)
        self.process_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_row, text="Help / Documentation", 
                  command=self.show_help).grid(row=0, column=1, padx=5)
        
    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)
        
    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if files:
            self.add_files(files)
            
    def add_files(self, files):
        for file in files:
            file = file.strip('{}')
            if file.lower().endswith('.mp4') and file not in self.video_queue:
                self.video_queue.append(file)
                self.video_listbox.insert(tk.END, os.path.basename(file))
                
    def clear_queue(self):
        self.video_queue.clear()
        self.video_listbox.delete(0, tk.END)
        
    def remove_selected(self):
        selected = self.video_listbox.curselection()
        for index in reversed(selected):
            self.video_queue.pop(index)
            self.video_listbox.delete(index)
    
    def set_quality_preset(self, quality_value):
        """Set quality to preset value"""
        self.quality_var.set(quality_value)
    
    def on_quality_slider_change(self, value):
        """Handle quality slider change"""
        rounded = round(float(value))
        self.quality_var.set(rounded)
        self.quality_preset_var.set("custom")
    
    def parse_comp_name(self, filename):
        """Parse composition name from filename"""
        name = Path(filename).stem
        parts = name.split('-')
        
        if len(parts) < 3:
            return None
        
        # Find the first part that's a valid number (the order)
        order_index = None
        order_num = None
        
        for i, part in enumerate(parts):
            try:
                order_num = int(part)
                order_index = i
                break
            except ValueError:
                continue
        
        if order_index is None or order_index == 0:
            return None
        
        # Everything before the number is the category
        category = '-'.join(parts[:order_index])
        # Everything after the number is the title
        title = '-'.join(parts[order_index + 1:])
        
        if not title:
            return None
        
        return {
            'category': category,
            'categoryOrder': order_num,
            'title': title.replace('-', ' ').title()
        }
    
    def parse_xmp_metadata(self, xmp_path, look_for_theme=False):
        """Extract marker data from XMP file
        
        Args:
            xmp_path: Path to XMP file
            look_for_theme: If True, only look at frame 0 markers. If False, look at frame 1+ markers.
        """
        try:
            tree = ET.parse(xmp_path)
            root = tree.getroot()
            
            # Namespaces
            namespaces = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'xmpDM': 'http://ns.adobe.com/xmp/1.0/DynamicMedia/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # Extract composition title
            comp_title = None
            for title_elem in root.findall('.//dc:title/rdf:Alt/rdf:li', namespaces):
                comp_title = title_elem.text
                break
            
            # Extract marker comment based on frame position
            marker_comment = None
            for marker in root.findall('.//xmpDM:markers/rdf:Seq/rdf:li', namespaces):
                start_time_elem = marker.find('xmpDM:startTime', namespaces)
                comment_elem = marker.find('xmpDM:comment', namespaces)
                
                if start_time_elem is not None and comment_elem is not None:
                    start_time = int(start_time_elem.text)
                    
                    # Frame 0 for theme, Frame 1+ for clips
                    if look_for_theme and start_time == 0:
                        marker_comment = comment_elem.text
                        break
                    elif not look_for_theme and start_time > 0:
                        marker_comment = comment_elem.text
                        break
            
            return comp_title, marker_comment
            
        except Exception as e:
            print(f"Error parsing XMP: {e}")
            return None, None
    
    def parse_simplified_marker(self, marker_text):
        """Parse simplified marker syntax into JSON structure"""
        if not marker_text:
            return None
            
        config = {
            'customInputs': []
        }
        
        # Split on both \n and \r to handle different line endings
        lines = re.split(r'[\r\n]+', marker_text.strip())
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('DESCRIPTION:'):
                config['popupMessage'] = line[12:].strip()
                
            elif line.startswith('THEME-NAME:'):
                config['themeName'] = line[11:].strip()
                
            elif line.startswith('THEME-DESCRIPTION:'):
                config['themeDescription'] = line[18:].strip()
                
            elif line.startswith('TEXT:'):
                parts = [p.strip() for p in line[5:].split('|')]
                if len(parts) >= 3:
                    input_def = {
                        'inputType': 'text',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'maxLength': int(parts[2])
                    }
                    if len(parts) > 3 and parts[3]:
                        input_def['placeholder'] = parts[3]
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('TEXTAREA:'):
                parts = [p.strip() for p in line[9:].split('|')]
                if len(parts) >= 3:
                    input_def = {
                        'inputType': 'textarea',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'maxLength': int(parts[2])
                    }
                    if len(parts) > 3 and parts[3]:
                        input_def['placeholder'] = parts[3]
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('URL:'):
                parts = [p.strip() for p in line[4:].split('|')]
                if len(parts) >= 2:
                    input_def = {
                        'inputType': 'url',
                        'label': parts[0],
                        'fieldId': parts[1]
                    }
                    if len(parts) > 2 and parts[2]:
                        input_def['placeholder'] = parts[2]
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('TEXTLIST-FIXED:'):
                parts = [p.strip() for p in line[15:].split('|')]
                if len(parts) >= 4:
                    input_def = {
                        'inputType': 'textList',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'count': int(parts[2]),
                        'itemMaxLength': int(parts[3])
                    }
                    if len(parts) > 4 and parts[4]:
                        input_def['placeholder'] = parts[4]
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('TEXTLIST-FLEX:'):
                parts = [p.strip() for p in line[14:].split('|')]
                if len(parts) >= 4:
                    min_max = parts[2].split('-')
                    input_def = {
                        'inputType': 'textList',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'minItems': int(min_max[0]),
                        'maxItems': int(min_max[1]),
                        'itemMaxLength': int(parts[3])
                    }
                    if len(parts) > 4 and parts[4]:
                        input_def['placeholder'] = parts[4]
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('MEDIA-FIXED:'):
                parts = [p.strip() for p in line[12:].split('|')]
                if len(parts) >= 5:
                    input_def = {
                        'inputType': 'mediaRequestList',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'mediaType': parts[2],
                        'count': int(parts[3]),
                        'description': parts[4]
                    }
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('MEDIA-FLEX:'):
                parts = [p.strip() for p in line[11:].split('|')]
                if len(parts) >= 5:
                    min_max = parts[3].split('-')
                    input_def = {
                        'inputType': 'mediaRequestList',
                        'label': parts[0],
                        'fieldId': parts[1],
                        'mediaType': parts[2],
                        'minItems': int(min_max[0]),
                        'maxItems': int(min_max[1]),
                        'description': parts[4]
                    }
                    config['customInputs'].append(input_def)
                    
            elif line.startswith('NO-INPUT:'):
                config['requiresInput'] = False
                
            elif line.startswith('OVERLAY:'):
                config['isOverlay'] = True
                
            elif line.startswith('TIER:'):
                config['tierRequirement'] = line[5:].strip()
        
        return config
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            
            if fps > 0:
                duration = frame_count / fps
                return round(duration, 2)
            return 3
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 3
    
    def is_split_screen(self, width, height):
        """Detect if video is split-screen format"""
        ratio = width / height if height > 0 else 0
        return ratio >= 1.8
        
    def extract_poster(self, video_path, position_percent, quality, output_size=None):
        """Extract poster frame from video"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return False, "Could not open video file"
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0 or fps <= 0:
                cap.release()
                return False, "Invalid video properties"
            
            frame_number = int((position_percent / 100.0) * total_frames)
            frame_number = max(0, min(frame_number, total_frames - 1))
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Could not read frame"
                
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = frame.shape[:2]
            
            # Check if this is an overlay file or split-screen
            filename = Path(video_path).stem
            if filename.startswith('overlay') or self.is_split_screen(width, height):
                frame = frame[:, :width//2]
                
            img = Image.fromarray(frame)
            
            # Resize if output size specified
            if output_size:
                img = img.resize(output_size, Image.LANCZOS)
            
            path = Path(video_path)
            output_path = path.parent / f"{path.stem}-poster.jpg"
            
            img.save(output_path, 'JPEG', quality=quality)
            
            return True, str(output_path)
            
        except Exception as e:
            return False, str(e)
    
    def generate_theme_id(self, theme_name):
        """Generate theme ID from theme name"""
        theme_id = theme_name.lower()
        theme_id = re.sub(r'[^a-z0-9\s-]', '', theme_id)
        theme_id = re.sub(r'\s+', '-', theme_id)
        theme_id = re.sub(r'-+', '-', theme_id)
        return theme_id.strip('-')
    
    def find_existing_json(self, folder_path):
        """Find existing theme JSON file in folder"""
        folder = Path(folder_path)
        json_files = list(folder.glob('*.json'))
        
        if len(json_files) == 1:
            return json_files[0]
        elif len(json_files) > 1:
            # Multiple JSONs - look for one that matches theme structure
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'theme' in data and 'clips' in data:
                            return json_file
                except:
                    continue
        return None
    
    def load_existing_theme_data(self, json_path):
        """Load existing theme JSON"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('theme'), data.get('clips', [])
        except Exception as e:
            print(f"Error loading existing JSON: {e}")
            return None, []
    
    def move_xmp_to_trash(self, video_paths):
        """Move XMP files to xmp_trash folder"""
        if not video_paths:
            return
        
        try:
            # Create xmp_trash folder in same directory as videos
            folder = Path(video_paths[0]).parent
            trash_folder = folder / 'xmp_trash'
            trash_folder.mkdir(exist_ok=True)
            
            moved_count = 0
            for video_path in video_paths:
                xmp_path = Path(video_path).with_suffix('.xmp')
                if xmp_path.exists():
                    trash_path = trash_folder / xmp_path.name
                    # If file already exists in trash, add number
                    counter = 1
                    while trash_path.exists():
                        trash_path = trash_folder / f"{xmp_path.stem}_{counter}.xmp"
                        counter += 1
                    xmp_path.rename(trash_path)
                    moved_count += 1
            
            print(f"Moved {moved_count} XMP files to xmp_trash/")
        except Exception as e:
            print(f"Error moving XMP files: {e}")
    
    def show_help(self):
        """Show help documentation window"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help & Documentation")
        help_window.geometry("800x600")
        
        # Create scrolled text widget
        text_frame = ttk.Frame(help_window, padding="10")
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        help_window.columnconfigure(0, weight=1)
        help_window.rowconfigure(0, weight=1)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, padx=10, pady=10)
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Help content
        help_text = """THEME JSON GENERATOR - QUICK START GUIDE

═══════════════════════════════════════════════════════════════════

1. NAMING YOUR AFTER EFFECTS COMPOSITIONS

Format: category-order-Title

CATEGORIES:
• hook - Opening/attention grabbers
• solution-intro - Introduce the solution
• features-benefits - Product features and benefits
• product-showcase - Product demonstrations
• proof-trust - Testimonials, stats, client logos
• cta - Calls to action
• overlay - Logo, captions, overlays
• clean - Clean plates/renders/backgrounds

EXAMPLES:
hook-001-IntroSlide
solution-intro-002-ValueProp
features-benefits-003-ThreeFeatures
proof-trust-005-ClientLogos
cta-006-VisitBooth
clean-002-ProductSpin

═══════════════════════════════════════════════════════════════════

2. ADDING MARKERS IN AFTER EFFECTS

A. For THEME PREVIEW (theme-demo comp):
   • Place marker at FRAME 0
   • Add this in Comment field:

THEME-NAME: Your Theme Name Here
THEME-DESCRIPTION: Brief description of theme style and use case

B. For ALL CLIPS:
   • Place marker at FRAME 1 (not frame 0!)
   • Add simplified metadata in Comment field

═══════════════════════════════════════════════════════════════════

3. SIMPLIFIED MARKER SYNTAX

For clips with NO user input needed:
DESCRIPTION: Animated background loop - no customization needed.
NO-INPUT: true

For clips needing single text input:
DESCRIPTION: Enter your company tagline.
TEXT: Tagline | tagline | 60 | e.g., Innovation Starts Here

For clips with multiple inputs:
DESCRIPTION: Add headline and supporting text.
TEXT: Headline | headline | 60 | e.g., Welcome
TEXT: Subheadline | subheadline | 80 | e.g., Discover the Future

FIXED lists (exact number required):
TEXTLIST-FIXED: Feature Titles | featureTitles | 3 | 40 | e.g., Feature name

FLEXIBLE lists (user chooses quantity):
TEXTLIST-FLEX: Benefits | benefits | 2-8 | 60 | Enter a benefit

FIXED media (exact number):
MEDIA-FIXED: Feature Icons | featureIcons | image | 3 | 3 icons for features

FLEXIBLE media (variable quantity):
MEDIA-FLEX: Client Logos | clientLogos | logo | 3-20 | Client logos (PNG)

═══════════════════════════════════════════════════════════════════

4. EXPORTING FROM MEDIA ENCODER

1. Add compositions to render queue
2. Choose H.265 (HEVC) preset
3. Click output filename to open settings
4. Go to Metadata tab:
   ✓ Check "Export XMP metadata to sidecar file"
   ✓ Check "Include composition markers"
5. Render

This creates TWO files per clip:
• your-clip-name.mp4 (video)
• your-clip-name.xmp (metadata)

═══════════════════════════════════════════════════════════════════

5. USING THIS TOOL

CREATING NEW THEME:
1. Enter Base URL Path (e.g., ./assets/media/my-theme/)
2. Drag all MP4 files (including theme-demo.mp4)
3. Leave "Append" checkbox UNCHECKED
4. Click "Generate Theme JSON & Posters"

ADDING CLIPS TO EXISTING THEME:
1. Drag only NEW clip MP4 files (no theme-demo needed)
2. CHECK "Append to existing theme JSON" checkbox
3. Click "Generate Theme JSON & Posters"
4. Tool finds existing JSON and adds new clips

═══════════════════════════════════════════════════════════════════

6. WHAT THE TOOL DOES

✓ Reads XMP metadata from sidecar files
✓ Parses simplified marker syntax
✓ Extracts video duration automatically
✓ Generates poster JPEGs (640x360 by default)
✓ Builds complete theme JSON
✓ Saves everything to same folder
✓ Moves XMP files to xmp_trash/ folder
✓ In append mode: merges new clips with existing

═══════════════════════════════════════════════════════════════════

7. TIPS & TROUBLESHOOTING

✓ Theme marker must be at FRAME 0
✓ Clip markers must be at FRAME 1+
✓ Keep both MP4 and XMP files together
✓ Use descriptive fieldIds (camelCase, no spaces)
✓ XMP files moved to xmp_trash/ - can delete when done
✓ Test marker syntax at jsonlint.com if issues

FIELD NAMING:
Good: headline, featureTitles, clientLogos
Bad: text1, feature titles, feature-titles

═══════════════════════════════════════════════════════════════════

For full documentation, see:
• Technical Documentation (complete specs)
• Animator's Guide (quick reference)
"""
        
        text_widget.insert('1.0', help_text)
        text_widget.configure(state='disabled')  # Make read-only
        
        # Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).grid(row=1, column=0, pady=10)
    
    def process_videos(self):
        if not self.video_queue:
            messagebox.showwarning("No Videos", "Please add video files to the queue.")
            return
            
        self.process_button.config(state='disabled')
        thread = threading.Thread(target=self.process_thread)
        thread.daemon = True
        thread.start()
        
    def process_thread(self):
        total = len(self.video_queue)
        position_percent = self.position_var.get()
        quality = self.quality_var.get()
        base_url = self.base_url_var.get().rstrip('/') + '/'
        append_mode = self.append_mode_var.get()
        
        # Get output size if specified
        output_size = None
        try:
            width = self.width_var.get().strip()
            height = self.height_var.get().strip()
            if width and height:
                output_size = (int(width), int(height))
        except (ValueError, AttributeError):
            pass
        
        # Check for existing JSON if in append mode
        existing_theme = None
        existing_clips = []
        existing_json_path = None
        
        if append_mode and self.video_queue:
            folder = Path(self.video_queue[0]).parent
            existing_json_path = self.find_existing_json(folder)
            
            if existing_json_path:
                existing_theme, existing_clips = self.load_existing_theme_data(existing_json_path)
                if existing_theme:
                    self.status_label.config(text=f"Appending to: {existing_json_path.name}")
                else:
                    self.status_label.config(text="Existing JSON found but invalid format")
                    append_mode = False
            else:
                self.status_label.config(text="No existing JSON found - creating new theme")
                append_mode = False
        
        theme_data = existing_theme
        clips = list(existing_clips) if existing_clips else []
        errors = []
        new_clips_count = 0
        
        for i, video_path in enumerate(self.video_queue):
            self.status_label.config(text=f"Processing: {os.path.basename(video_path)}")
            
            try:
                # Get XMP path
                xmp_path = Path(video_path).with_suffix('.xmp')
                
                if not xmp_path.exists():
                    errors.append(f"{os.path.basename(video_path)}: No XMP file found")
                    continue
                
                # Check if this might be theme-demo by filename
                is_theme_file = 'theme' in Path(video_path).stem.lower()
                
                # Parse XMP - look at frame 0 if theme file, frame 1+ otherwise
                comp_title, marker_text = self.parse_xmp_metadata(xmp_path, look_for_theme=is_theme_file)
                
                if not marker_text:
                    errors.append(f"{os.path.basename(video_path)}: No marker data found")
                    continue
                
                # Parse marker
                config = self.parse_simplified_marker(marker_text)
                
                if not config:
                    errors.append(f"{os.path.basename(video_path)}: Could not parse marker")
                    continue
                
                # Check if this is theme preview
                if 'themeName' in config:
                    if append_mode and existing_theme:
                        # Skip theme processing in append mode
                        self.status_label.config(text=f"Skipping theme video (using existing theme data)")
                        continue
                    
                    theme_name = config['themeName']
                    theme_id = self.generate_theme_id(theme_name)
                    
                    # Generate poster for theme preview
                    success, poster_path = self.extract_poster(video_path, position_percent, quality, output_size)
                    
                    theme_data = {
                        'id': theme_id,
                        'name': theme_name,
                        'description': config.get('themeDescription', ''),
                        'previewUrl': base_url + os.path.basename(video_path),
                        'posterUrl': base_url + os.path.basename(poster_path) if success else ''
                    }
                else:
                    # This is a clip
                    parsed_name = self.parse_comp_name(video_path)
                    
                    if not parsed_name:
                        errors.append(f"{os.path.basename(video_path)}: Invalid filename format")
                        continue
                    
                    # Check if clip already exists (by id)
                    clip_id = Path(video_path).stem
                    if any(c['id'] == clip_id for c in clips):
                        self.status_label.config(text=f"Skipping {clip_id} (already exists)")
                        continue
                    
                    # Generate poster
                    success, poster_path = self.extract_poster(video_path, position_percent, quality, output_size)
                    
                    if not success:
                        errors.append(f"{os.path.basename(video_path)}: {poster_path}")
                        continue
                    
                    # Get duration
                    duration = self.get_video_duration(video_path)
                    
                    # Get theme ID (from existing or new theme data)
                    theme_id = theme_data['id'] if theme_data else 'any'
                    
                    # Build clip object
                    clip = {
                        'id': clip_id,
                        'title': parsed_name['title'],
                        'category': parsed_name['category'],
                        'categoryOrder': parsed_name['categoryOrder'],
                        'previewUrl': base_url + os.path.basename(video_path),
                        'posterUrl': base_url + os.path.basename(poster_path),
                        'themeId': theme_id,
                        'defaultDuration': duration,
                        'isOverlay': config.get('isOverlay', False),
                        'tierRequirement': config.get('tierRequirement', 'Essential'),
                        'triggersTierUpgrade': False,
                        'requiresInput': config.get('requiresInput', len(config['customInputs']) > 0),
                        'popupMessage': config.get('popupMessage', ''),
                        'customInputs': config['customInputs']
                    }
                    
                    clips.append(clip)
                    new_clips_count += 1
                
            except Exception as e:
                errors.append(f"{os.path.basename(video_path)}: {str(e)}")
            
            progress = ((i + 1) / total) * 100
            self.progress_var.set(progress)
        
        # Build final JSON
        if theme_data and clips:
            # Update clip themeIds if needed
            theme_id = theme_data['id']
            for clip in clips:
                if clip['themeId'] == 'any':
                    clip['themeId'] = theme_id
            
            final_json = {
                'theme': theme_data,
                'clips': clips
            }
            
            # Save JSON (overwrite existing if in append mode)
            output_dir = Path(self.video_queue[0]).parent
            
            if append_mode and existing_json_path:
                json_path = existing_json_path
                status_msg = f"Updated: Added {new_clips_count} new clips (total: {len(clips)})"
            else:
                json_path = output_dir / f"{theme_id}.json"
                status_msg = f"Complete: Generated {len(clips)} clips + theme JSON"
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
            
            # Move XMP files to trash folder
            self.move_xmp_to_trash(self.video_queue)
            
            self.status_label.config(text=status_msg)
            
            if errors:
                error_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... and {len(errors) - 5} more errors"
                messagebox.showwarning("Processing Complete with Errors", 
                                     f"{status_msg}\n\nXMP files moved to xmp_trash/\n\nErrors:\n{error_msg}")
                
            else:
                messagebox.showinfo("Success", 
                                  f"{status_msg}\n\nXMP files moved to xmp_trash/\n\nSaved to: {json_path.name}")
                
        else:
            if not theme_data:
                messagebox.showerror("Error", "No theme data found. Make sure theme exists or add theme preview video with THEME-NAME marker.")
            elif not clips:
                messagebox.showerror("Error", "No valid clips processed.")
        
        self.process_button.config(state='normal')


def main():
    root = TkinterDnD.Tk()
    app = ThemeJSONGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()