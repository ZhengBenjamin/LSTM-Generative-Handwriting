import os 
import csv
import tkinter as tk
import pandas as pd
import numpy as np

from DataProcessing import DataProcessing
from PIL import Image, ImageDraw
from tkinter import ttk

class MakeVectors():
  
  def __init__(self, num_vectors, num_intermediates):
    self.num_intermediates = num_intermediates 
    self.output_folder = "training"
    self.output_file = "training/vectors.csv"
    
    os.makedirs(self.output_folder, exist_ok=True)

    self.data_vectors = []
    
    for i in range(num_vectors):  
      self.make_vector(i)
    
    self.save_vectors() 
      
  def make_vector(self, i):
    window = tk.Tk()
    window.title("Make Vector")
    vectors = []
    
    canvas = tk.Canvas(window, width=256, height=256, bg="white") 
    canvas.pack()
    
    image = Image.new("1", (256, 256), 1)
    draw = ImageDraw.Draw(image)
    
    self.last_x, self.last_y = None, None
    stroke_vector = []

    def on_hold(event):
      # Paint
      x1, y1 = (event.x - 1), (event.y - 1)
      x2, y2 = (event.x + 1), (event.y + 1)
      canvas.create_oval(x1, y1, x2, y2, fill="black", width=7)
      draw.line([x1, y1, x2, y2], fill="black", width=10)
      
      curr_x = int(event.x / 4) # Divide by 4 for 64x64 image
      curr_y = int(event.y / 4)
      
      # Save vector details 
      if self.last_x == None:
        self.last_x = curr_x
        self.last_y = curr_y
      else:
        
        if self.last_x != curr_x and self.last_y != curr_y:
          stroke_vector.append([self.last_x, self.last_y, curr_x, curr_y])
          self.last_x = curr_x
          self.last_y = curr_y
      
    def on_release(event):
      stroke_vector.append([self.last_x, self.last_y, int(event.x / 4), int(event.y / 4)])
      self.last_x, self.last_y = None, None
      vectors.append(stroke_vector.copy())
      stroke_vector.clear()
      
    canvas.bind("<B1-Motion>", on_hold)
    canvas.bind("<ButtonRelease-1>", on_release)
    
    def compress_stroke_vector(vector, num_intermediates):
      # Flatten the stroke into a list of points
      points = []
      for segment in vector:
        points.append((segment[0], segment[1]))
        points.append((segment[2], segment[3]))

      # Remove duplicates and maintain order
      points = list(dict.fromkeys(points))

      # Compute total path length
      distances = [np.linalg.norm(np.subtract(points[i + 1], points[i])) for i in range(len(points) - 1)]
      total_length = sum(distances)

      # Determine evenly spaced distances
      if total_length == 0 or len(points) < 2:
        return [[0, 0] for _ in range(num_intermediates)]  # Handle edge cases
      segment_lengths = np.cumsum([0] + distances)
      target_distances = np.linspace(0, total_length, num_intermediates)

      # Interpolate points along the path
      compressed = []
      current_index = 0
      for target_distance in target_distances:
        while current_index < len(segment_lengths) - 1 and segment_lengths[current_index + 1] < target_distance:
          current_index += 1
        t = (target_distance - segment_lengths[current_index]) / (segment_lengths[current_index + 1] - segment_lengths[current_index])
        interpolated_x = int((1 - t) * points[current_index][0] + t * points[current_index + 1][0])
        interpolated_y = int((1 - t) * points[current_index][1] + t * points[current_index + 1][1])
        compressed.append([interpolated_x, interpolated_y])
      return compressed
    
    def save_image():
      window.destroy()
      
      compressed_vectors = [] 
      for stroke_vector in vectors:
        compressed_stroke_vector = compress_stroke_vector(stroke_vector, self.num_intermediates)
        
        while len(compressed_stroke_vector) < self.num_intermediates: # Approprate length for training
          compressed_stroke_vector.append([0, 0])
          
        compressed_vectors += compressed_stroke_vector
        
      while len(compressed_vectors) < 4 * self.num_intermediates: # 4 strokes per vector 
        compressed_vectors.append([0, 0])
      
      self.data_vectors.append(compressed_vectors)
      
      DataProcessing.draw_vector(compressed_vectors, f"{self.output_folder}/vector_{i}.png")

    save_button = ttk.Button(window, text="Save", command=save_image)
    save_button.pack()
    
    window.mainloop()
    
  def save_vectors(self):
    
    print(len(self.data_vectors))
    with open(self.output_file, "w") as file:
      writer = csv.writer(file)
      
      for character in self.data_vectors:
        row = []
        for coordinate in character:
          row += coordinate
        writer.writerow(row)

if __name__ == "__main__":
  MakeVectors(10, 80)
    
    