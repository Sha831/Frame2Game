
import cv2
from pathlib import Path

from src.backend.yolo_detector import YoloDetector
from src.backend.file_manager import FileManager


class ImageProcess():
    def __init__(self):
        model_path , model_config_path = FileManager().get_model_path('detector')
        self.yolo = YoloDetector(yolo_path=model_path)
        self.yolo_result = None
        self.images_with_boundingbox = None
        self.no_of_boundingbox = None

    def object_detection(self,image_path):
        self.yolo_result = self.yolo.object_detection(image_path)
        return self.update_img_with_yolo_boundingbox(image_path)


    def update_img_with_yolo_boundingbox(self, image_paths):
        img_with_boundingbox = {}
        for img_path in image_paths:
            img_boxes = []
            image_name = Path(img_path).stem
            
            # Check if this image has detections in yolo_result
            if image_name in self.yolo_result:
                # Directly get boxes from the detection list
                detections = self.yolo_result[image_name]
                img_boxes = [detection['box'] for detection in detections]
            
            # Load image and draw boxes
            image = cv2.imread(img_path)
            for (x1, y1, x2, y2) in img_boxes:
                h, w = image.shape[:2]
                avg_dim = (w + h) / 2
                thickness = max(1, int(avg_dim / 500))

                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), thickness)
            
            img_with_boundingbox[f'{image_name}']=(image,len(img_boxes),img_boxes)
        
        return img_with_boundingbox
        

    def update_img_with_manual_boundigbox(self,image,box_coordinates):
        for (x1, y1, x2, y2) in box_coordinates:
                h, w = image.shape[:2]
                avg_dim = (w + h) / 2
                thickness = max(1, int(avg_dim / 500))
                cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), thickness)

        return image
            

    def close(self):
        self._del_device()

    def _del_device(self):
        #Clean up when ImageProcess is destroyed
        if hasattr(self, 'yolo'):
            self.yolo.close()


