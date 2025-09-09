#!/usr/bin/env python3
"""
Build script for Music Player App
Builds backend, frontend, and Electron app
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    try:
        subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def build_backend():
    backend_dir = Path("backend")
    return (run_command("pip install -r requirements.txt", cwd=backend_dir) and
            run_command("pyinstaller --onefile --name api_server api_server.py", cwd=backend_dir))

def build_frontend():
    frontend_dir = Path("frontend")
    return (run_command("npm install", cwd=frontend_dir) and
            run_command("npm run build", cwd=frontend_dir))

def build_electron():
    electron_dir = Path("electron")
    return (run_command("npm install", cwd=electron_dir) and
            run_command("npm run build", cwd=electron_dir))

def main():
    if not Path("backend").exists() or not Path("frontend").exists():
        print("Run from project root directory")
        sys.exit(1)
    
    success = True
    if "--backend" in sys.argv or len(sys.argv) == 1: success &= build_backend()
    if "--frontend" in sys.argv or len(sys.argv) == 1: success &= build_frontend()
    if "--electron" in sys.argv or len(sys.argv) == 1: success &= build_electron()
    
    print("Build completed" if success else "Build failed")
    if not success: sys.exit(1)

if __name__ == "__main__":
    main()