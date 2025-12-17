import cv2
import numpy as np


class EnhanceImage:
    def __init__(self):
        pass

######################################################################################
#DENOISING ALPHA
######################################################################################
    def apply_denoising(self, image: np.ndarray, slider_value: int):
        # Apply alpha channel denoising
        if slider_value > 0:
            alpha_kernel = self.slider_to_alpha_params(slider_value, image.shape[:2])
            if alpha_kernel > 1:
                alpha = image[:, :, 3]
                denoised_alpha = cv2.medianBlur(alpha, alpha_kernel)
                image[:, :, 3] = denoised_alpha
        
        #RGB denioising
        rgb_slider = slider_value // 2  #RGB denoising at half strength
        if rgb_slider > 25:  # Only if significant
            rgb_params = self.slider_to_rgb_params(slider_value)
            rgb = image[:, :, :3]
            denoised_rgb = cv2.bilateralFilter(
                rgb, 
                d=rgb_params['d'],
                sigmaColor=rgb_params['sigmaColor'],
                sigmaSpace=rgb_params['sigmaSpace']
            )
            image[:, :, :3] = denoised_rgb
        
        return image
    

    def slider_to_alpha_params(self,slider_value, image_size):
        h, w = image_size
        
        #limit based on image size
        max_kernel = min(h, w) // 10  # Max 10% of smallest dimension
        max_kernel = max(max_kernel, 31)  #But at least 31
        
        if slider_value == 0:
            return 1
        else:
            # Map 1-100 to 3-max_kernel
            kernel = 3 + int((slider_value / 100.0) * (max_kernel - 3))
            return kernel if kernel % 2 == 1 else kernel + 1  # Ensure odd
        

    def slider_to_rgb_params(self,slider_value):
        # sigmaColor and sigmaSpace range: 0 to 50
        sigma = int((slider_value / 100.0) * 50)
        
        # d (kernel size) based on strength
        if slider_value == 0:
            d = 1  # No filtering
        elif slider_value <= 50:
            d = 5  # Light
        else:
            d = 7  # Medium to Strong
        
        return {
            'd': d,
            'sigmaColor': sigma,
            'sigmaSpace': sigma
        }
    
######################################################################################
#EDGE ENHANCEMENT
######################################################################################
    def slider_to_edge_params(self,slider_value:int):

        external_thickness = int((slider_value / 100.0) * 4)  #0-4 pixels
        internal_thickness = external_thickness//2

        if slider_value <= 50:
            #0-50: More sharpening
            sharpen = 0.7 + (slider_value / 50.0) * 0.3  #0.7 to 1.0
            darken = (slider_value / 50.0) * 0.3  #0 to 0.3
        else:
            #51-100: More darkening
            sharpen = 1.0 - ((slider_value - 50) / 50.0) * 0.7  #1.0 to 0.3
            darken = 0.3 + ((slider_value - 50) / 50.0) * 0.7  #0.3 to 1.0
        
        return {'external_thickness':external_thickness,'internal_thickness':internal_thickness,'sharpen': sharpen, 'darken': darken}


    def enhance_edges_unified(self, bgra_image:np.ndarray, slider_value:int):
        #Calculate parameters from slider
        slider_params = self.slider_to_edge_params(slider_value)
        
        # Skip if no effect
        if slider_value == 0:
            return bgra_image
        

        # 3. Create edge zone masks
        edge_zones = self.create_edge_zones(bgra_image, slider_params['external_thickness'])
        
        # 4. Apply effects
        result = self.apply_edge_effects(
            bgra_image, 
            edge_zones, 
            darken_strength=slider_params['darken'],
            sharpen_strength=slider_params['sharpen']
        )
        
        return result
    

    def create_edge_zones(self,bgra_image,external_width):

        alpha = bgra_image[:, :, 3]
        bgr = bgra_image[:, :, :3]

        _, binary = cv2.threshold(alpha, 128, 255, cv2.THRESH_BINARY)
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 0)
        external_zone = (dist_transform <= external_width) & (dist_transform > 0)

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3,3), 0)
        # Low thresholds to catch subtle curves
        edges = cv2.Canny(gray, threshold1=40, threshold2=100)
        #Keep edges only inside object
        internal_zone = (edges > 0) & (alpha > 128)

        return {
            'external': external_zone.astype(np.uint8),
            'internal': internal_zone.astype(np.uint8)
        }
    

    def apply_edge_effects(self, bgra_image, edge_zones, darken_strength, sharpen_strength):

        bgr = bgra_image[:, :, :3]

        if darken_strength > 0:
            external_mask = edge_zones['external']

            external_min_factor = 0.15  
            external_factor = 1.0 - darken_strength * (1.0 - external_min_factor)#min 15% of original brightness retained always

            bgr[external_mask == 1] = (
                bgr[external_mask == 1] * external_factor
            ).astype(np.uint8)

        
            internal_mask = edge_zones['internal']

            internal_min_factor = 0.7  # never too dark
            internal_factor = 1.0 - darken_strength * (1.0 - internal_min_factor)#min 70% of original brightness retained always

            bgr[internal_mask == 1] = (
                bgr[internal_mask == 1] * internal_factor
            ).astype(np.uint8)

    
        if sharpen_strength > 0:
            blurred = cv2.GaussianBlur(bgr, (0, 0), 1.0)
            sharpened = cv2.addWeighted(
                bgr, 1.0 + sharpen_strength,
                blurred, -sharpen_strength,
                0
            )

            internal_mask = edge_zones['internal']
            bgr[internal_mask == 1] = sharpened[internal_mask == 1]

        bgra_image[:, :, :3] = bgr

        return bgra_image

######################################################################################
#WHITE BALANCE
######################################################################################
    def white_balance(self,bgra_image:np.ndarray, slider_value:int, gentleness=0.3):

        #slightly change the white/mood of image max 30% of original
        if slider_value == 0:
            return bgra_image
        

        bgr = bgra_image[:, :, :3].astype(np.float32)
        
        strength = slider_value / 100.0
        
        avg_color = np.mean(bgr, axis=(0,1))
        
        # Target: neutral gray
        target_gray = np.mean(avg_color)
        
        # Standard correction factors
        correction = target_gray / avg_color
        
        #adjustment (30% of full correction)
        gentle_correction = 1.0 + (correction - 1.0) * gentleness
        
        # Apply user strength
        final_correction = 1.0 + (gentle_correction - 1.0) * strength
        
        # Apply correction
        corrected = bgr * final_correction
        
        # Update image
        result = bgra_image.copy()
        result[:, :, :3] = np.clip(corrected, 0, 255).astype(np.uint8)
        
        return result
    
######################################################################################
#COLOR BALANCE
######################################################################################
    def color_balance_vibrance_fixed(self, bgra_image:np.ndarray, slider_value:int):
        #vibrance using HSV with alpha preservation
        
        if slider_value == 0:
            return bgra_image
        
        # Store alpha channel
        alpha_channel = bgra_image[:, :, 3].copy()
        
        # Extract BGR
        bgr = bgra_image[:, :, :3]
        
        # Convert to HSV
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        
        # Convert to float for calculations
        hsv_float = hsv.astype(np.float32)
        saturation = hsv_float[:, :, 1]  # Saturation channel
        
        # Calculate boost: 0-100 → 1.0-2.5
        base_boost = 1.0 + (slider_value / 100.0) * 1.5  # 1.0 to 2.5
        
        # Normalize saturation (0-1)
        sat_norm = saturation / 255.0
        
        # sat=0 → boost=base_boost, sat=1 → boost=1.0
        boost_map = 1.0 + (base_boost - 1.0) * (1.0 - sat_norm)
        
        # Apply boost
        hsv_float[:, :, 1] = saturation * boost_map
        
        # Clip saturation to valid range
        hsv_float[:, :, 1] = np.clip(hsv_float[:, :, 1], 0, 255)
        
        # Convert back
        hsv_uint8 = hsv_float.astype(np.uint8)
        boosted_bgr = cv2.cvtColor(hsv_uint8, cv2.COLOR_HSV2BGR)
        
        # Create result with preserved alpha
        result = np.zeros_like(bgra_image)
        result[:, :, :3] = boosted_bgr
        result[:, :, 3] = alpha_channel
        
        return result
    
######################################################################################
#SATURATION
######################################################################################
    def adjust_saturation(self, bgra_image, slider_value):
        #Simple saturation adjustment
        
        if slider_value == 0:
            return bgra_image
        
        # Store alpha channel
        alpha_channel = bgra_image[:, :, 3].copy()
        
        # Extract BGR
        bgr = bgra_image[:, :, :3]
        
        # Convert to HSV
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Get saturation channel
        saturation = hsv[:, :, 1]
        
        # Calculate multiplier: 0→1.0, 100→2.0
        multiplier = 1.0 + (slider_value / 100.0)
        
        # Apply saturation boost
        hsv[:, :, 1] = saturation * multiplier
        
        # Clip to valid range (0-255)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # Convert back to BGR
        saturated_bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # Create result with preserved alpha
        result = np.zeros_like(bgra_image)
        result[:, :, :3] = saturated_bgr
        result[:, :, 3] = alpha_channel
        
        return result
    
######################################################################################
#REFINE EDGES
######################################################################################
    def refine_edges(self, bgra_image, slider_value):

        if slider_value == 0:
            return bgra_image
        
        #Extract alpha channel
        alpha = bgra_image[:, :, 3].astype(np.float32) / 255.0
        
        #Dynamic kernel size (3 to 11 - more reasonable)
        kernel_size = 3 + int((slider_value / 100.0) * 8)  # 3 to 11
        kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        
        #Sigma proportional to kernel
        sigma = 0.2 * kernel_size
        
        #Apply Gaussian blur
        smoothed = cv2.GaussianBlur(alpha, (kernel_size, kernel_size), sigma)
        
        #Add tiny gap filling at medium-high settings
        if slider_value > 40:
            close_size = 3  # Fixed small size
            kernel = np.ones((close_size, close_size), np.float32)
            smoothed = cv2.morphologyEx(smoothed, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        #Soft edges at high settings
        if slider_value > 70:
            # Light distance transform for softness
            binary = (alpha > 0.5).astype(np.uint8)
            dist = cv2.distanceTransform(binary, cv2.DIST_L2, 3)
            dist_norm = cv2.normalize(dist, None, 0, 1.0, cv2.NORM_MINMAX)
            
            # Gentle blend (max 30% distance transform)
            blend_strength = min(0.3, (slider_value - 70) / 100.0)
            smoothed = smoothed * (1 - blend_strength) + dist_norm * blend_strength
        
        # Convert back
        refined_alpha = (smoothed * 255).astype(np.uint8)
        
        # Create result
        result = bgra_image.copy()
        result[:, :, 3] = refined_alpha
        
        return result
    

