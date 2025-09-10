const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow;
let backendProcess;

// Check if running in development mode
const isDev = process.argv.includes('--dev');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, './logo/Svara_Logo.png'),
    show: false // Don't show until ready
  });

  // Load the React app
  if (isDev) {
    // Development: Load from React dev server
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: Load from built React app
    const indexPath = path.join(__dirname, '../frontend/build/index.html');
    mainWindow.loadFile(indexPath);
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  return new Promise(async (resolve, reject) => {
    // Kill existing processes on port 5001
    if (process.platform === 'win32') {
      spawn('taskkill', ['/f', '/im', 'python.exe'], { stdio: 'ignore' });
    }
    
    let backendPath;
    
    if (isDev) {
      // Development: Check if backend is already running
      try {
        const response = await fetch('http://127.0.0.1:5001/api/status');
        if (response.ok) {
          console.log('Backend already running');
          resolve();
          return;
        }
      } catch (e) {
        // Backend not running, skip starting it since batch file handles it
        console.log('Backend will be started by batch file');
        resolve();
        return;
      }
    } else {
      // Production: Run compiled executable
      backendPath = path.join(process.resourcesPath, 'backend/api_server.exe');
      
      if (!fs.existsSync(backendPath)) {
        // Fallback to local path if not in resources
        backendPath = path.join(__dirname, '../backend/dist/api_server.exe');
      }
      
      if (!fs.existsSync(backendPath)) {
        reject(new Error(`Backend executable not found at ${backendPath}`));
        return;
      }
      
      backendProcess = spawn(backendPath, [], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
    }

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    // Give backend time to start
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        resolve();
      } else {
        reject(new Error('Backend failed to start'));
      }
    }, 3000);
  });
}

async function stopBackend() {
  // First try to stop music playback gracefully
  try {
    const response = await fetch('http://127.0.0.1:5001/api/stop', { method: 'POST' });
    console.log('Music stopped');
  } catch (error) {
    console.log('Could not stop music gracefully');
  }
  
  if (backendProcess && !backendProcess.killed) {
    console.log('Stopping backend process...');
    backendProcess.kill('SIGTERM');
    
    // Force kill after 2 seconds
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill('SIGKILL');
      }
    }, 2000);
  }
}

app.whenReady().then(async () => {
  try {
    console.log('Starting backend server...');
    await startBackend();
    console.log('Backend started successfully');
    
    createWindow();
  } catch (error) {
    console.error('Failed to start application:', error);
    
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the music player backend: ${error.message}`
    );
    
    app.quit();
  }
});

app.on('window-all-closed', async () => {
  await stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', async () => {
  await stopBackend();
});

// Handle app termination
process.on('SIGINT', () => {
  stopBackend();
  app.quit();
});

process.on('SIGTERM', () => {
  stopBackend();
  app.quit();
});