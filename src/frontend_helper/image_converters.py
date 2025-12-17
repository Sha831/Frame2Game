import cv2
from PyQt6.QtGui import QFont,QImage,QPixmap,QPainter, QColor
from PyQt6.QtCore import Qt
import numpy as np
import os


def cv2_to_qpixmap(cv_image, max_size=None):
    if cv_image is None or not isinstance(cv_image, np.ndarray):
        return create_placeholder_pixmap(max_size, "Invalid OpenCV Image")
    
    try:
        if cv_image.shape[2] == 4:  # BGRA
            # Convert BGRA to RGBA
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGBA)
            
            height, width, channels = rgb_image.shape
            bytes_per_line = channels * width
            
            # CORRECT: Use RGBA format for RGBA data
            qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888)
            
        else:  # BGR (no alpha)
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            height, width, channels = rgb_image.shape
            bytes_per_line = channels * width
            
            # Use RGB format for RGB data
            qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        return QPixmap.fromImage(qt_image)
    
    except Exception as e:
        print(f"Error converting image: {e}")
        return create_placeholder_pixmap(max_size, "Conversion Error")


def cv2_to_qpixmap_display(cv_image, max_size=None):

    if max_size:
        cv_image,size = resize_image(cv_image, max_size)
    
    # Convert to QPixmap
    return cv2_to_qpixmap(cv_image,max_size)
    

def qpixmap_to_cv2(qpixmap):
    #Convert QPixmap to OpenCV image
    
    # Convert to QImage first
    qt_image = qpixmap.toImage()
    
    # Convert to RGB format
    qt_image = qt_image.convertToFormat(QImage.Format.Format_RGB888)
    
    # Get dimensions
    width = qt_image.width()
    height = qt_image.height()
    
    # Get pointer to data
    ptr = qt_image.bits()
    ptr.setsize(qt_image.sizeInBytes())
    
    # Create numpy array from the data
    arr = np.array(ptr).reshape(height, width, 3)
    
    # Convert RGB to BGR for OpenCV
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def create_placeholder_pixmap(maxsize, text="Placeholder"):
    #Create a colored placeholder with text
    
    # Create pixmap
    pixmap = QPixmap(maxsize[0], maxsize[1])
    pixmap.fill(QColor(60, 60, 60))  # Dark gray background
    
    # Draw text
    painter = QPainter(pixmap)
    painter.setPen(QColor(200, 200, 200))  # Light gray text
    painter.setFont(QFont("Arial", 10))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    
    return pixmap



def create_thumbnail(cv_image, max_size=(150, 200)):
    #Create thumbnail from OpenCV image with aspect ratio preservation
    
    if cv_image is None:
        return create_placeholder_pixmap(max_size, "No Image")
    
    # Get original dimensions
    original_height, original_width = cv_image.shape[:2]
    max_width, max_height = max_size
    
    # Calculate scaling factor (maintain aspect ratio)
    width_ratio = max_width / original_width
    height_ratio = max_height / original_height
    scale = min(width_ratio, height_ratio)
    
    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # Resize image
    resized_image = cv2.resize(cv_image, (new_width, new_height))
    
    # Convert to QPixmap
    return cv2_to_qpixmap(resized_image,max_size)
    

def image_path_to_qpixmap(image_path, max_size=None):
    #Load image from path and convert to QPixmap with optional scaling
    
    if max_size is None:
        max_size=(200,150)

    if not image_path:
        return create_placeholder_pixmap(max_size, "No Path")
    
    try:
        # Load image
        cv_image = cv2.imread(image_path,cv2.IMREAD_UNCHANGED)
        if cv_image is None:
            return create_placeholder_pixmap(max_size, f"Not Found: {os.path.basename(image_path)}")
        
        # Apply scaling if requested
        if max_size:
            cv_image,size = resize_image(cv_image, max_size)
        
        # Convert to QPixmap
        return cv2_to_qpixmap(cv_image,max_size)
        
    except Exception as e:
        print(f"Error loading {image_path}: {e}")
        return create_placeholder_pixmap(max_size, "Load Error")

def resize_image(cv_image, max_size):
    #Resize image while maintaining aspect ratio
    height, width = cv_image.shape[:2]
    max_width, max_height = max_size
    
    # Calculate scaling
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)

    print((new_width, new_height))

    image = cv2.resize(cv_image, (new_width, new_height))
    
    return image , (new_width, new_height)


def change_coordinates_pixmap_to_cv2(image_path,max_size,widget_coordinates,img_offset=(0,0)):
    image = cv2.imread(image_path,cv2.IMREAD_UNCHANGED)

    height , width = image.shape[:2]
    max_width, max_height = max_size
    x_start , y_start = widget_coordinates.x1 , widget_coordinates.y1
    x_end , y_end = widget_coordinates.x2 , widget_coordinates.y2
    
    scale = min(max_width / width, max_height / height)

    scaled_width = int(width * scale)
    scaled_height = int(height * scale)

    if img_offset:
        offset_x,offset_y = img_offset
    else:
        offset_x = (max_width - scaled_width) / 2
        offset_y = (max_height - scaled_height) / 2

    x_start_org_image = int(round((x_start - offset_x) / scale,4))
    y_start_org_image = int(round((y_start - offset_y) / scale,4))

    x_end_org_image = int(round((x_end - offset_x) / scale,4))
    y_end_org_image = int(round((y_end - offset_y) / scale,4))

    org_image_tuple = (x_start_org_image,y_start_org_image,x_end_org_image,y_end_org_image)

    return org_image_tuple


def image_path_to_cv2(image_path):
    if image_path is not None:
        image = cv2.imread(image_path,cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"Could not read image at path: {image_path}")
        else:
            return image
    else:
        raise ValueError("image_path cannot be None")     



def resize_to_original_coordinates(points,display_size, org_image_path_or_image):

    click_x, click_y = points

    if isinstance(org_image_path_or_image,str):
        org_image = cv2.imread(org_image_path_or_image,cv2.IMREAD_UNCHANGED)
    else:
        org_image = org_image_path_or_image
    
    original_height, original_width = org_image.shape[:2]

    # Get the display dimensions (resized image dimensions)
    display_width, display_height = display_size

    # Calculate the scale factors for both width and height
    scale_x = original_width / display_width
    scale_y = original_height / display_height

    # Map the click coordinates to the original image coordinates
    orig_x = click_x * scale_x
    orig_y = click_y * scale_y

    # Return the mapped coordinates in the original image
    return int(orig_x), int(orig_y)


def get_brush_diameter(brush_dia_scaled,display_size, org_image_path_or_image):

    if isinstance(org_image_path_or_image,str):
        org_image = cv2.imread(org_image_path_or_image,cv2.IMREAD_UNCHANGED)
    else:
        org_image = org_image_path_or_image
    
    original_height, original_width = org_image.shape[:2]

    # Get the display dimensions (resized image dimensions)
    display_width, display_height = display_size

    scale_x = original_width / display_width
    scale_y = original_height / display_height

    scale_factor = (scale_x + scale_y) / 2

    original_dia = scale_factor*brush_dia_scaled

    return original_dia



def crop_to_tight_bounds(bgra_image, padding=3):
    #Crop to object bounds with padding(here 3 pixels)
    

    alpha = bgra_image[:, :, 3]
    
    # Find non-transparent pixels (alpha > 0)
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        # Fully transparent image
        return bgra_image
    
    # Get bounds
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    # Add padding (clamped to image bounds)
    h, w = alpha.shape
    y_min = max(0, y_min - padding)
    y_max = min(h - 1, y_max + padding)
    x_min = max(0, x_min - padding)
    x_max = min(w - 1, x_max + padding)
    
    # Crop
    cropped = bgra_image[y_min:y_max+1, x_min:x_max+1]
    
    return cropped