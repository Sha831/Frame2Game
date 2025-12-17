       
from pathlib import Path
import sys
import json
import shutil
import requests
import zipfile


class FileManager:
    def __init__(self):
        self.base_dir = self.get_base_dir()
        self.models_dir = self.base_dir / "models"
        self.config_path = self.models_dir / "models_config.json"


    def get_base_dir(self):
        if getattr(sys, "frozen", False):
            # Running from EXE/PyInstaller(basically main.py)
            return Path(sys.executable).parent
        else:
            # Running from source code
            return Path(__file__).resolve().parent.parent.parent  # Adjust as needed
        


    def get_model_path(self, model_type):
        # Load JSON config
        with open(self.config_path, 'r') as f:
            config = json.load(f)


        # Build model path relative to base_dir
        model_path = self.base_dir / "models" / config['models'][model_type]['path']

        # Optional config file path
        model_config_path = None
        if config['models'][model_type].get("config", None):
            model_config_path = self.base_dir / "models" / config['models'][model_type]['config_path']

        return str(model_path), str(model_config_path)
 

    def check_if_required_models_exist(self):

        if self.models_dir.exists() and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                        config = json.load(f)

                all_present = True
                # Check detector
                detector_file = self.models_dir / config["models"]["detector"]["path"]
                if not detector_file.exists():
                    print(f" Missing: {detector_file}")
                    all_present = False
                
                # Check segmentor
                segmentor_file = self.models_dir / config["models"]["segmentor"]["path"]
                if not segmentor_file.exists():
                    print(f" Missing: {segmentor_file}")
                    all_present = False

                #Returns: (success)
                if all_present:
                    print("All models present")
                    return True
                else:
                    print(" Some files missing, re-downloading...")
                    return False
                

            except Exception as e:
                print(f"Config error: {e}, re-downloading...")
                return False
            
        else:
            return False
        

    def download_models(self,progress_callback, zip_url: str, ) -> bool:
        #Download and extract models with progress tracking
        temp_dir = self.base_dir / "temp_download"

        def clear_files_if_download_fails():
            if self.models_dir.exists():
                shutil.rmtree(self.models_dir)
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        clear_files_if_download_fails()
        try:
            # Clean up existing
            if self.models_dir.exists():
                clear_files_if_download_fails()
                print("deleted old models folder")
            
            # Create temp directory
            temp_dir.mkdir(exist_ok=True)
            zip_path = temp_dir / "models.zip"
            
            # Download with progress
            response = requests.get(zip_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            download_speed = 5 * 1024 * 1024
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=download_speed):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Report progress (0-50% for download, 50-100% for extraction)
                        if total_size > 0 and progress_callback:
                            download_percent = int((downloaded / total_size) * 50)  # First half
                            progress_callback.emit(download_percent)
            

            # Report extraction start
            if progress_callback:
                progress_callback.emit(50)  
            
            # Extract
            print("Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list):
                    zip_ref.extract(file, self.base_dir)
                    
                    # Report extraction progress
                    if progress_callback:
                        extract_percent = 50 + int((i + 1) / total_files * 50)  # Second half
                        progress_callback.emit(extract_percent)
            
            # Verify structure
            config_file_path = self.models_dir / "models_config.json"
            if config_file_path.exists():
                try:
                    with open(config_file_path, 'r') as f:
                        config = json.load(f)
                    
                    expected_structure = [
                        config_file_path,
                        self.base_dir / "models" / config['models']['detector']['path'],
                        self.base_dir / "models" / config['models']['segmentor']['path'],
                    ]
            
                    for path in expected_structure:
                        if not path.exists():
                            raise Exception(f"Missing after extraction: {path}")
                        
                        
                except Exception as e:
                    clear_files_if_download_fails()
                    print(f"File structure is wrong/missing: {e}")
                    return False,e
                
            else:
                raise Exception("Missing 'models_config.json' after extraction")
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            # Report completion
            if progress_callback:
                progress_callback.emit(100)
            
            print("Models downloaded successfully!")
            return True,'Download Completed'
            
        except Exception as e:
            clear_files_if_download_fails()
            print(f"Download failed: {e}")
            return False,e
        
