import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import json
import pathlib
import random
import math
import numpy as np

def create_circle_mask(size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    return mask

def create_rectangular_mask(size):
    mask = Image.new('L', (size, size), 255)
    return mask

def create_hexagon_mask(size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    width = size
    height = size

    radius = width / 2
    center_x = width / 2
    center_y = height / 2
    hexagon_points = [
        (center_x + radius * math.cos(math.radians(30 + 60 * i)),
         center_y + radius * math.sin(math.radians(30 + 60 * i)))
        for i in range(6)
    ]

    draw.polygon(hexagon_points, fill=255)
    return mask

def average_color(image):
    np_image = np.array(image.convert('RGB'))
    avg_color = np_image.mean(axis=(0, 1)).astype(int)
    return tuple(avg_color)

def apply_mask(image, mask):
    np_image = np.array(image.resize(mask.size).convert('RGBA'))
    np_mask = np.array(mask) / 255.0
    np_image[:, :, 3] = (np_image[:, :, 3] * np_mask).astype(np.uint8)
    return Image.fromarray(np_image)

def load_color_image_dict(dict_path):
    with open(dict_path, 'r') as f:
        return {tuple(map(int, k.strip('()').split(','))): v for k, v in json.load(f).items()}

def create_color_image_dict(folder_path, dict_path):
    imgs_dir = pathlib.Path(folder_path)
    images = list(imgs_dir.glob("*.jpg"))
    data = {}
    for img_path in images:
        img = Image.open(img_path)
        avg_color = average_color(img)
        avg_color = tuple(int(x) for x in avg_color)
        if str(avg_color) in data:
            data[str(avg_color)].append(str(img_path))
        else:
            data[str(avg_color)] = [str(img_path)]
    with open(dict_path, "w") as file:
        json.dump(data, file, indent=2, sort_keys=True)

def find_closest_color(target_color, color_dict):
    closest_color = min(color_dict.keys(), key=lambda c: np.linalg.norm(np.array(c) - np.array(target_color)))
    return closest_color

def create_mosaic(target_image_path, color_dict, output_path, tile_size=100, mask_func=create_circle_mask, progress_callback=None):
    target_image = Image.open(target_image_path).convert('RGB')
    target_image = target_image.resize((1000, 1000))
    pattern_mask = mask_func(tile_size)
    mosaic = Image.new('RGBA', target_image.size)
    num_cols = int(mosaic.width / tile_size) + 1
    num_rows = int(mosaic.height / tile_size) + 1
    pattern_requires_offset = mask_func in [create_circle_mask, create_hexagon_mask]

    total_tiles = num_cols * num_rows
    current_tile = 0

    for row in range(num_rows):
        for col in range(num_cols):
            x_offset = col * tile_size
            y_offset = row * tile_size
            if pattern_requires_offset and row % 2 == 1:
                x_offset += tile_size // 2

            if x_offset < mosaic.width and y_offset < mosaic.height:
                region = target_image.crop((x_offset, y_offset, x_offset + tile_size, y_offset + tile_size))
                avg_color = average_color(region)
                closest_color = find_closest_color(avg_color, color_dict)
                selected_image_path = random.choice(color_dict[closest_color])
                selected_image = Image.open(selected_image_path)
                masked_image = apply_mask(selected_image, pattern_mask)
                mosaic.paste(masked_image, (int(x_offset), int(y_offset)), mask=masked_image)

            current_tile += 1
            if progress_callback:
                progress_callback(current_tile / total_tiles * 100)

    mosaic.save(output_path)

class MosaicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mosaic Generator")
        self.geometry("600x400")
        self.resizable(False, False)

        self.dataset_folder = None
        self.target_image_path = None
        self.tile_size = tk.IntVar(value=20)
        self.pattern = tk.StringVar(value="Circular")
        self.output_path = 'mosaic_output.png'

        self.dataset_folder_label = tk.Label(self, text="Dataset Folder: Not selected")
        self.dataset_folder_label.pack(side=tk.TOP, pady=5)

        self.target_image_label = tk.Label(self, text="Target Image: Not selected")
        self.target_image_label.pack(side=tk.TOP, pady=5)

        self.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate', length=600)
        self.progress.pack(side=tk.TOP, pady=5)

        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        tk.Button(self.controls_frame, text="Select Dataset Folder", command=self.select_dataset_folder).pack(
            side=tk.TOP, pady=5)
        tk.Button(self.controls_frame, text="Select Target Image", command=self.select_target_image).pack(side=tk.TOP,
                                                                                                          pady=5)

        tile_size_frame = tk.Frame(self.controls_frame)
        tile_size_frame.pack(side=tk.TOP, pady=5)
        tk.Label(tile_size_frame, text="Tile Size:").pack(side=tk.LEFT, padx=5)
        tk.Entry(tile_size_frame, textvariable=self.tile_size, width=5).pack(side=tk.LEFT, padx=5)

        pattern_frame = tk.Frame(self.controls_frame)
        pattern_frame.pack(side=tk.TOP, pady=5)
        tk.Label(pattern_frame, text="Pattern:").pack(side=tk.LEFT, padx=5)
        tk.OptionMenu(pattern_frame, self.pattern, "Circular", "Rectangular", "Hexagonal").pack(side=tk.LEFT, padx=5)

        tk.Button(self.controls_frame, text="Generate Mosaic", command=self.generate_mosaic).pack(side=tk.TOP, pady=10)

    def select_dataset_folder(self):
        self.dataset_folder = filedialog.askdirectory()
        if self.dataset_folder:
            self.dataset_folder_label.config(text=f"Dataset Folder: {self.dataset_folder}")
        else:
            messagebox.showerror("Error", "No dataset folder selected.")

    def select_target_image(self):
        self.target_image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png")])
        if self.target_image_path:
            self.target_image_label.config(text=f"Target Image: {self.target_image_path}")
        else:
            messagebox.showerror("Error", "No target image selected.")

    def update_progress(self, value):
        self.progress['value'] = value
        self.update_idletasks()

    def generate_mosaic(self):
        if not self.dataset_folder or not self.target_image_path:
            messagebox.showerror("Error", "Please select both dataset folder and target image.")
            return

        dict_path = 'cache.json'

        if not os.path.exists(dict_path):
            create_color_image_dict(self.dataset_folder, dict_path)

        color_dict = load_color_image_dict(dict_path)

        mask_func = {
            "Circular": create_circle_mask,
            "Rectangular": create_rectangular_mask,
            "Hexagonal": create_hexagon_mask
        }.get(self.pattern.get(), create_circle_mask)

        self.progress['value'] = 0
        create_mosaic(self.target_image_path, color_dict, self.output_path, tile_size=self.tile_size.get(),
                      mask_func=mask_func, progress_callback=self.update_progress)
        self.show_result_image()

    def show_result_image(self):
        result_window = tk.Toplevel(self)
        result_window.title("Mosaic Result")
        result_image = Image.open(self.output_path)
        result_image_tk = ImageTk.PhotoImage(result_image)

        result_image_label = tk.Label(result_window, image=result_image_tk)
        result_image_label.image = result_image_tk
        result_image_label.pack()

if __name__ == "__main__":
    app = MosaicApp()
    app.mainloop()
