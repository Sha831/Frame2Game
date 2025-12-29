
from ultralytics import YOLO
from pathlib import Path
import torch
import gc



class YoloDetector():
    def __init__(self,yolo_path,gpu_id=None):
        self.path = yolo_path
        self.gpu_id = gpu_id if gpu_id is not None else 0
        self.device = None
        self.model = None
        self.set_device()
        self._load_device()
        

    def set_device(self):
        #added try block to fallback to cpu if any error detecting gpu
        try:
            if torch.cuda.is_available() and torch.cuda.device_count()>0:
                    if self.gpu_id < torch.cuda.device_count():
                        self.device = torch.device(f"cuda:{self.gpu_id}")
                    else:
                        print(f"GPU {self.gpu_id} not found, falling back to CPU")
                        self.device = torch.device("cpu")
            else:
                self.device = torch.device("cpu")
                
        except Exception as e:
            print(f"Gpu detection failed, moving model to Cpu: {e}")
            self.device = torch.device("cpu")

        print(f"Using device: {self.device}")


    def _load_device(self):
        try:
            print("🎬 Loading models for video extraction...")
            self.model = YOLO(self.path).to(self.device)
            print(f" Models loaded on {self.device}")
        except Exception as e:
            print(f" Error loading models: {e}")
            raise


    def _del_device(self):
        if self.model is not None:
            del self.model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


    def close(self):
        self._del_device()


    def object_detection(self, image_paths):  # FIX: parameter name
        self.model.fuse()
        All_boxes = {}
        
        # FIX: Add debug print
        print(f" Processing {len(image_paths)} images with YOLO...")
        
        results = self.model(image_paths, iou=0.6, conf = 0.6 )  # FIX: Use correct parameter name

        for i, result in enumerate(results):
            boxes = []

            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())

                    detection = {
                        'image_index': i,
                        'box': (x1, y1, x2, y2),
                        'confidence': round(float(box.conf.item()), 3),
                        'class_id': int(box.cls.item()),
                        'class_name': self.model.names[int(box.cls.item())]
                    }
                    
                    boxes.append(detection)
                    

            All_boxes[f'{Path(result.path).stem}']=boxes
        
        print(f" Returning: {All_boxes}")
        return All_boxes

