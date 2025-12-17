import cv2
import numpy as np
from typing import Union


from src.backend.style_options import AssertStyles
from src.backend.enhancement_options import EnhanceImage

class EditOptions():
    def __init__(self):
        self.add_style = AssertStyles()
        self.enhance_image = EnhanceImage()

    def get_points(self, image: np.ndarray, input_data: tuple[tuple[int,int], str]):
        result = image.copy()
        
        point = input_data[0]
        if input_data[1] == 'Object':
            color = (0,255,0)  
        elif input_data[1] == 'Background':
            color = (0,0,255)

        cv2.circle(result, point, 3, color, -1)  

        return result
    
    

    @staticmethod
    def fill_or_erase_point(image: np.ndarray, input_data: tuple[list[tuple[int,int]],int,str]):
        points, diameter, edit = input_data
        img = image.copy()

        for point in points:
            cx ,cy = point

            r = diameter // 2

            h, w = img.shape[:2]

            # Create a coordinate grid
            Y, X = np.ogrid[:h, :w]

            # Mask for circle
            dist_sq = (X - cx)**2 + (Y - cy)**2
            mask = dist_sq <= r*r

            if edit == 'Fill':
                alpha_value = 255
            else:
                alpha_value = 0

            # Apply alpha change
            img[mask, 3] = alpha_value


        return img
        
  
######################################################################################
#ADD IMAGE ENHANCEMENTS
######################################################################################
    def add_full_image_edits(self,image: np.ndarray, input_data:dict):

        edited_image = image.copy()

        if input_data.get('Denoising'):
            edited_image = self.enhance_image.apply_denoising(edited_image,input_data['Denoising'])

        if input_data.get('Sharpen/Darken Edges'):
            edited_image = self.enhance_image.enhance_edges_unified(edited_image,input_data['Sharpen/Darken Edges'])

        if input_data.get('White Balance'):
            edited_image = self.enhance_image.white_balance(edited_image,input_data['White Balance'])

        if input_data.get('Color Balance'):
            edited_image = self.enhance_image.color_balance_vibrance_fixed(edited_image,input_data['Color Balance'])

        if input_data.get('Saturation'):
            edited_image = self.enhance_image.adjust_saturation(edited_image,input_data['Saturation'])

        if input_data.get('Refine Edges'):
            edited_image = self.enhance_image.refine_edges(edited_image,input_data['Refine Edges'])


        return edited_image
        

######################################################################################
#ADD STYLES
######################################################################################
    def add_image_styles(self,image: np.ndarray, input_data:dict):

        edited_image = image.copy()

        if input_data.get('Pixel Art'):
            print(input_data['Pixel Art'])
            edited_image = self.add_style.apply_pixel_art(edited_image,input_data['Pixel Art'])

        if input_data.get('Cel Shading'):
            print('Cel Shading')
            edited_image = self.add_style.apply_cel_shaded_art(edited_image,input_data['Cel Shading'])

        if input_data.get('Anime'):
            print(input_data['Anime'])
            edited_image = self.add_style.apply_anime_art(edited_image,input_data['Anime'])

        if input_data.get('Dithered Art'):
            print(input_data['Dithered Art'])
            edited_image = self.add_style.apply_dithering_art(edited_image,input_data['Dithered Art'])

        if input_data.get('Game Boy'):
            print('Game Boy')
            edited_image = self.add_style.apply_gameboy_art(edited_image,input_data['Game Boy'])
        
        if input_data.get('Simple Animation'):
            print('Simple Animation')
            edited_image = self.add_style.apply_simple_animation_art(edited_image,input_data['Simple Animation'])

        return edited_image
    


######################################################################################
#RESIZE IMAGE
######################################################################################
    @staticmethod
    def resize_game_asset(bgra_image, target_size):
        #MVP: Game assets only → Scale to fit, anchor top-left .NO padding, NO centering, NO empty collision space
        h, w = bgra_image.shape[:2]
        target_w, target_h = target_size
        
        # Calculate scale to fit within target
        scale = min(target_w / w, target_h / h)
        
        # New dimensions (fit inside target)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(bgra_image, (new_w, new_h), cv2.INTER_LANCZOS4)
        
        return resized
    

    def scale_from_center_slider(self,bgra_image, slider_value):
        #slider_value: -100 to +100
        # -100 = 25% of original (scale down)
        # 0 = 100% (no change)
        # +100 = 400% of original (scale up)

        if slider_value == 0:
            return bgra_image
        
        h, w = bgra_image.shape[:2]
        
        # Convert slider to scale factor
        if slider_value < 0:
            # Negative: Scale down (0.25x to 1.0x)
            scale = 1.0 + (slider_value / 100.0) * 0.75  # 0.25 to 1.0
        else:
            # Positive: Scale up (1.0x to 4.0x)
            scale = 1.0 + (slider_value / 100.0) * 3.0   # 1.0 to 4.0
        
        # Calculate new size
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(bgra_image, (new_w, new_h), cv2.INTER_LANCZOS4)

        return resized


    def should_apply_auto_size(self,current_size, target_size, threshold=0.15):

        curr_w, curr_h = current_size
        target_w, target_h = target_size

        if curr_w == target_w and curr_h == target_h:
            return False
        
        # Calculate size ratio difference
        width_ratio = abs(curr_w - target_w) / target_w
        height_ratio = abs(curr_h - target_h) / target_h
        
        # Only resize if significantly different (>15%)
        return width_ratio > threshold or height_ratio > threshold


    def apply_auto_size_if_needed(self,bgra_image, preset_name):
        #Smart auto-size: Only resize if not already close to target

        STANDARD_SIZES = {
            'Tiny': (32, 32),
            'Small': (64, 64),
            'Medium': (128, 128),
            'Large': (256, 256),
            'Huge': (512, 512)
        }
        
        if preset_name == 'Original':
            return bgra_image

        current_size = (bgra_image.shape[1], bgra_image.shape[0])
        target_size = STANDARD_SIZES[preset_name]
        
        if self.should_apply_auto_size(current_size, target_size):
            return self.resize_game_asset(bgra_image, target_size)
        else:
            print(f"Already near {preset_name} size, skipping resize")
            return bgra_image
        

    def apply_auto_or_manual_resize(self,bgra_image:np.ndarray,value:Union[int,str]):

        image = bgra_image.copy()

        if isinstance(value,int):
            return self.scale_from_center_slider(image,value)

        elif isinstance(value,str):
            return self.apply_auto_size_if_needed(image,value)

        else:
            raise ValueError(f"Invalid resize value type: {type(value)}")