import cv2
import numpy as np
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import torch
import gc




class SamExtractor():
    def __init__(self,sam_path,sam_model_config,gpu_id=None):
        self.path = sam_path
        self.gpu_id = gpu_id if gpu_id is not None else 0
        self.model_type = sam_model_config
        self.device = None
        self.model = None
        self.set_device()
        

    def set_device(self):
        #added try block to fallback to cpu if any error detecting gpu
        try:
            if torch.cuda.is_available():
                if self.gpu_id > 0:
                    self.device = f'cuda:{self.gpu_id}'
                else:
                    self.device = 'cuda:0'  # Fallback to GPU 0
            else:
                self.device = 'cpu'
                
        except Exception as e:
            print(f"Gpu detection failed, moving model to Cpu: {e}")
            self.device = 'cpu'

        print(f"Using device: {self.device}")
        

    def load_device(self):
        try:
            print("🎬 Loading models for object extraction...")
            self.model = build_sam2(config_file=self.model_type,ckpt_path=self.path).to('cuda:0')
            self.predictor = SAM2ImagePredictor(self.model)
            print(f" Models loaded on {self.device}")
        except Exception as e:
            print(f" Error loading models: {e}")
            raise

    def close(self):
        self._del_device()

    def _del_device(self):
        del self.model
        gc.collect()
        torch.cuda.empty_cache()

    
    def segmented_objects(self,image_path, bbox: dict,**kwargs):

        if image_path is not None:
            image = cv2.imread(image_path)
            if image is None:
                raise FileNotFoundError(f"Could not read image at path: {image_path}")
        else:
            raise ValueError("image_path cannot be None")     

        # Convert image BGR → BGRA
        bgra_org = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

        pc = kwargs.get("point_coords")
        point_coords = None if not pc else np.array(pc, dtype=np.float32)

        pl = kwargs.get("point_labels")
        point_labels = [] if not pc else np.array(pl, dtype=np.float32)

        all_objects = {}

        for objects,bounding_box in bbox.items():
            x1,y1,x2,y2 = bounding_box
            box = np.array( bounding_box, dtype=np.float32)

            #filter points based off bounding box
            if point_coords is not None and len(point_coords) > 0:
                mask_points = (point_coords[:, 0] >= x1) & (point_coords[:, 0] <= x2) & \
                            (point_coords[:, 1] >= y1) & (point_coords[:, 1] <= y2)

                #Filtered
                filtered_points = point_coords[mask_points]
                filtered_labels = point_labels[mask_points]

                # If no points inside this box → set None
                if filtered_points.shape[0] == 0:
                    filtered_points = None
                    filtered_labels = []

            else:
                filtered_points = None
                filtered_labels = []


            mask = self.segmentation_mask(image,bounding_box=box,point_coords=filtered_points,point_labels=filtered_labels)
            refined_mask = self.mask_refining_usingCV2(mask)

            # Ensure mask is valid alpha
            alpha = refined_mask.astype(np.uint8)
            if alpha.max() <= 1:
                alpha = alpha * 255

            # Put refined mask into alpha channel
            bgra = bgra_org.copy()
            bgra[:, :, 3] = alpha

            # Crop result
            object_rgba = bgra[y1:y2, x1:x2]

            all_objects[objects] = object_rgba

        return all_objects



    def segmentation_mask(self,image,bounding_box,point_coords,point_labels,
                          multimask_output=True,
                          mask_input=None,
                          return_logits=False):


        self.predictor.set_image(image)

        mask, score, logits = self.predictor.predict(
        box=bounding_box,
        point_coords=point_coords,
        point_labels=point_labels,
        mask_input=mask_input,
        multimask_output=multimask_output,
        return_logits=return_logits)


        best_mask = (None 
                if mask is None or mask.size == 0 
                else mask[score.argmax()] 
                if multimask_output 
                else mask[0] 
                if mask.ndim == 3 
                else mask)
        
        if best_mask is None:
            segmented_mask = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            return segmented_mask
        
        segmented_mask_uint8 = (best_mask*255).astype(np.uint8)

        return segmented_mask_uint8


    def mask_refining_usingCV2(self,mask,
                                ksize=(7,7),sigmaX=0,sigmaY=0,
                                kernel_shape=cv2.MORPH_ELLIPSE,kernel_size = (5,5)):

        mask_float = mask.astype(np.float32) / 255
        mask_gauss_blur = cv2.GaussianBlur(mask_float, ksize, sigmaX, sigmaY)
        mask_gauss_blur_uint8 = np.round(mask_gauss_blur*255).astype(np.uint8)

        kernel = cv2.getStructuringElement(kernel_shape,kernel_size)
        mask_morph = cv2.morphologyEx(mask_gauss_blur_uint8, cv2.MORPH_CLOSE, kernel)
        mask_morph = cv2.morphologyEx(mask_morph,cv2.MORPH_CLOSE,kernel)

        return mask_morph


