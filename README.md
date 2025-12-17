# Frame2Game (F2G)

Frame2Game (F2G) is a lightweight tool — currently in active development — that converts any image or gameplay frame into clean, usable **2D game assets**.  
It was built specifically to help **solo developers** and **indie game creators** rapidly prototype games without needing a full art pipeline or dedicated artists.

F2G makes it easy to extract characters, objects, backgrounds, and styled sprites directly from images — fast, offline, and simple to use.

Frame2Game currently supports NVIDIA GPUs only, using CUDA acceleration.

Supported NVIDIA GPUs include:
RTX series (RTX 20xx, 30xx, 40xx)
GTX series with CUDA support (GTX 10xx and newer)
NVIDIA GPUs with CUDA Compute Capability ≥ 6.1

Your GPU must support CUDA and have a compatible NVIDIA driver installed.

---

## Main Features

### **1. Image Segmentation**
- Extract characters, objects, enemies, props, or backgrounds  
- Automatic masking using modern AI models  
- Clean edges and transparent backgrounds for game-ready sprites  

### **2. Image Filters**
- Cleanup filters  
- Edge smoothing / sharpening  
- Color correction and noise reduction  
- Ideal for preparing assets before importing into a game engine  

### **3. Asset Styling**
- Transform assets into different art styles  
- Pixel-art effects, toon shading, outline filters, and more  
- Helps turn real screenshots into consistent game-ready aesthetics  

---

### Demo Previews

### Character Segmentation

<div style="display: flex; gap: 16px; align-items: center;">
  <img src="asserts\images\scene_22.webp" width="400"/>
  <img src="asserts\extracted_asserts\scene_22_object_0.png"/>
</div>

<div style="display: flex; gap: 16px; align-items: center;">
  <img src="asserts/images/scene_8.jpg" width="400"/>
  <img src="asserts/extracted_asserts/scene_8_object_0.png" width="200"/>
</div>

---

## Core Tech Stack

F2G uses a combination of modern AI + CV tools:

- **YOLO (Ultralytics)** – object detection  
  - Includes YOLOv8 and newer families such as **YOLOv9/YOLOv10/YOLOv11/YOLOv12 (e.g., yolo12x.pt)**  
- **SAM 2 (Segment Anything Model 2)** – segmentation and mask extraction  
- **OpenCV** – image processing  
- **PyQt6** – graphical user interface  
- **NumPy** – numerical operations  
- **Rembg / custom segmentation filters**  
- **SAM2-Build / CUDA / PyTorch / ONNX** – model backend acceleration  

All processing is done **fully offline** using your system's CPU or GPU.

---

## Downloads (For Users)

Executables and model files will be available soon.

- **Download EXE:**  
  https://github.com/Sha831/Frame2Game/releases/download/Exe-Frame2Game_v1.0.0/Frame2Game.7z

- **Download Models:**  
  https://github.com/Sha831/Frame2Game/releases/download/Models-Frame2Game_v1.0.0/models.zip

Once available, users simply:

1. Download the EXE  
2. Run F2G — it will auto-download required models if not present (one-time setup)  
3. Start extracting and styling game assets  

---

## For Developers

If you want to run F2G from source or contribute to development:

- **Repository (Source Code):**  
  https://github.com/Sha831/Frame2Game

- **Model Files:**  
  https://github.com/Sha831/Frame2Game/releases/download/Models-Frame2Game_v1.0.0/models.zip

### Run Locally
```bash
git clone @repo-link
cd Frame2Game
pip install -r requirements.txt
### GPU support (recommended)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

python main.py

---





