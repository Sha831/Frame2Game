
import cv2
import numpy as np

from src.backend.edit_options import EditOptions
from src.frontend_helper import image_converters as img_conv

class EditManager():
    def __init__(self):
        self.original_image_dict = {}
        self.cached_image_dict = {}
        self.cached_image_size_dict = {}
        self.command_stack = {'Undo':{},'Redo':{}}
        self.undo_stack = {'Undo':{},"Redo":{}}
        self.edits = EditOptions()
        

    def store_images_for_edits(self,image_name,image_path_or_image:str|np.ndarray,display_size:tuple[int,int]=None):

        if isinstance(image_path_or_image,str):
            self.original_image_dict.setdefault(image_name,image_path_or_image)
            org_image = cv2.imread(image_path_or_image, cv2.IMREAD_UNCHANGED)
        else:
            self.original_image_dict.setdefault(image_name,image_path_or_image)
            org_image = image_path_or_image

        if display_size:
            cache_image,cache_img_size = img_conv.resize_image(org_image,display_size)
        else:
            cache_image,cache_img_size = org_image , org_image.shape[:2]
       
        
        self.cached_image_dict.setdefault(image_name,cache_image)
        self.cached_image_size_dict.setdefault(image_name,cache_img_size)


        self.command_stack['Undo'].setdefault(image_name,[])
        self.undo_stack['Undo'].setdefault(image_name,[])
        self.undo_stack['Redo'].setdefault(image_name,[])


    def apply_edits_to_display(self,image_name,edit_type,edit_action,value):

        cached_image = self.cached_image_dict[image_name]

        if edit_type == 'Undo':
            print(edit_type)
            new_image = self.undo(cached_image,image_name)
            # Update both caches for undo
            self.cached_image_dict[image_name] = new_image
            return new_image

        elif edit_type == 'Redo':
            print(edit_type)
            new_image = self.redo(cached_image,image_name)
            # Update both caches for redo
            self.cached_image_dict[image_name] = new_image
            return new_image

        elif edit_type == 'Pixel':
            #edits that are done on pixel level
            print(edit_type)
            function = getattr(self.edits, edit_action)
            new_image = function(cached_image, value)
            changed = self.add_action(cached_image, new_image, image_name)
            if changed:
                self.command_stack['Undo'][image_name].append((edit_type, edit_action, value))

            self.cached_image_dict[image_name] = new_image
            print(self.command_stack['Undo'])
            

        elif edit_type == 'Image':
            #edits that are done on full image
            print(edit_type)
            org_image = self.original_image_dict[image_name]
            size = self.cached_image_size_dict[image_name]
            org_image_resized , resize = img_conv.resize_image(org_image,size)
            function = getattr(self.edits, edit_action)
            new_image = function(org_image_resized, value)
            self.cached_image_dict[image_name] = new_image
            self.command_stack['Undo'][image_name] = [(edit_type, edit_action, value)]
        

        elif edit_type == 'Assert':
            print(edit_type)
            org_image = self.original_image_dict[image_name]
            function = getattr(self.edits, edit_action)
            new_image = function(org_image, value)
            self.cached_image_dict[image_name] = new_image
            self.command_stack['Undo'][image_name] = [(edit_type, edit_action, value)]


    

    def add_action(self, org_img, edited_img, image_name):

        #difference for ALL channels including ALPHA
        diff = cv2.absdiff(org_img, edited_img)

        if diff.shape[2] == 4:
            # sum all channel differences
            gray = diff.sum(axis=2)
        else:
            # fallback (BGR only)
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Create mask of changed pixels
        mask = (gray > 0).astype(np.uint8) * 255

        #Bounding box of changed region
        ys, xs = np.where(mask > 0)
        if len(ys) == 0:
            return False  # no changes

        y1, y2 = ys.min(), ys.max()
        x1, x2 = xs.min(), xs.max()

        #Extract undo/redo patches
        undo_patch = org_img[y1:y2+1, x1:x2+1].copy()
        redo_patch = edited_img[y1:y2+1, x1:x2+1].copy()

        undo_action = {
            "bbox": (x1, y1, x2, y2),
            "undo": undo_patch,
            "redo": redo_patch
        }

        self.undo_stack['Undo'][image_name].append(undo_action)
        self.undo_stack['Redo'][image_name].clear()

        return True


    def undo(self,image,image_name):
            
        if not self.undo_stack['Undo'][image_name]:
            return image
        
        action = self.undo_stack['Undo'][image_name].pop()

        if self.command_stack['Undo'][image_name]:
            command = self.command_stack['Undo'][image_name].pop()
            self.command_stack['Redo'].setdefault(image_name,[]).append(command)

        x1, y1, x2, y2 = action["bbox"]

        # apply undo
        image[y1:y2+1, x1:x2+1] = action["undo"]


        self.undo_stack['Redo'][image_name].append(action)

        return image
        

    def redo(self, image,image_name):
            
        if not self.undo_stack['Redo'][image_name]:
            return image

        action = self.undo_stack['Redo'][image_name].pop()

        x1, y1, x2, y2 = action["bbox"]

        # apply redo
        image[y1:y2+1, x1:x2+1] = action["redo"]

        # move back to undo stack
        self.undo_stack['Undo'][image_name].append(action)

        if self.command_stack['Redo'][image_name]:
            command = self.command_stack['Redo'][image_name].pop()
            self.command_stack['Undo'][image_name].append(command)

        return image
        

    def get_cached_image_to_display(self,image_name):

        image = self.cached_image_dict[image_name]
        
        return image
    

    def get_points(self,disp_size):

        final_point_dict = {}
        for image in self.command_stack['Undo']:
            image_path = self.original_image_dict[image]
            points = []
            point_type = []
            if self.command_stack['Undo'][image]:
                for commands in self.command_stack['Undo'][image]:
                    if commands[0] == 'Pixel' and commands[1] == 'get_points':
                        point , type = commands[2]
                        org_point = img_conv.resize_to_original_coordinates(point,disp_size,image_path)
                        points.append(org_point)
                        if type == 'Object':
                            point_type.append(1)
                        elif type == 'Background':
                            point_type.append(0)

            final_point_dict[image] = (points,point_type)

        return final_point_dict
