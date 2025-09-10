#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def run_command(cmd, cwd=None):
    """Run command and handle errors"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=== Building Windows Executable ===")
    
    # Step 1: Build React App
    print("\n1. Building React frontend...")
    frontend_dir = os.path.join(base_dir, "frontend")
    if not run_command("npm run build", cwd=frontend_dir):
        print("Failed to build React app")
        return False
    
    # Step 2: Package Python Backend
    print("\n2. Packaging Python backend...")
    backend_dir = os.path.join(base_dir, "backend")
    
    # Create PyInstaller spec if it doesn't exist
    spec_content = '''
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE

a = Analysis(
    ['api_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('playlists.json', '.'),
        ('song_url_cache.json', '.'),
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.http.h11_impl',
        'vlc',
        'yt_dlp'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='api_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    spec_file = os.path.join(backend_dir, "api_server.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content.strip())
    
    # Install PyInstaller if not present
    if not run_command("pip install pyinstaller", cwd=backend_dir):
        print("Failed to install PyInstaller")
        return False
    
    # Build executable
    if not run_command("pyinstaller api_server.spec --clean", cwd=backend_dir):
        print("Failed to build Python executable")
        return False
    
    # Step 3: Configure Electron Builder
    print("\n3. Installing Electron dependencies...")
    electron_dir = os.path.join(base_dir, "electron")
    if not run_command("npm install", cwd=electron_dir):
        print("Failed to install Electron dependencies")
        return False
    
    # Step 4: Build Electron App
    print("\n4. Building Electron executable...")
    if not run_command("npm run build", cwd=electron_dir):
        print("Failed to build Electron app")
        return False
    
    print("\n=== Build Complete! ===")
    print(f"Executable created in: {os.path.join(electron_dir, 'dist')}")
    return True

if __name__ == "__main__":
    if main():
        print("Build successful!")
        sys.exit(0)
    else:
        print("Build failed!")
        sys.exit(1)