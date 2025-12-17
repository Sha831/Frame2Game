from pathlib import Path
import sys

def resource_path(relative_path: str) -> Path:
    #Get absolute path to resource, works for dev and PyInstaller.
    
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller runtime
        base_path = Path(sys._MEIPASS)
    else:
        # Normal Python run
        base_path = Path(__file__).resolve().parents[2]  # adjust depth if needed


    return str(base_path / relative_path)


