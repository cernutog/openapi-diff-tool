import os
import subprocess
import sys
from PIL import Image

def install_requirements():
    print("Installing requirements (pyinstaller, pillow)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pillow"])

def create_ico():
    print("Converting app_icon.png to app_icon.ico...")
    if not os.path.exists("app_icon.png"):
        print("Error: app_icon.png not found!")
        sys.exit(1)
        
    img = Image.open("app_icon.png")
    img.save("app_icon.ico", format='ICO', sizes=[(256, 256)])

def build():
    print("Running PyInstaller...")
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon=app_icon.ico",
        "--add-data=app_icon.png;.",
        "--add-data=app_icon.ico;.",
        "--name=OpenAPIDiffTool",
        "gui.py"
    ]
    subprocess.check_call(cmd)

if __name__ == "__main__":
    try:
        install_requirements()
        create_ico()
        build()
        
        # Copy templates folder to dist
        import shutil
        if os.path.exists("templates"):
            print("Copying templates to dist/templates...")
            dest = os.path.join("dist", "templates")
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree("templates", dest)
            
        print("\nSUCCESS! Executable created in 'dist/OpenAPIDiffTool.exe'")
        print("Templates copied to 'dist/templates'")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
