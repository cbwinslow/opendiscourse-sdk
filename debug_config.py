import sys
import os
sys.path.append(os.getcwd())
try:
    from scripts.core.config import get_settings
    settings = get_settings()
    print("Settings loaded successfully")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()
