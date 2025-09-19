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

  // Hide menu bar in production
  if (!isDev) {
    mainWindow.setMenuBarVisibility(false);
  }

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
      backendPath = path.join(process.resourcesPath, 'music_player_backend.exe');
      
      // Set VLC paths if bundled
      const vlcPath = path.join(__dirname, '../vlc');
      if (fs.existsSync(vlcPath)) {
        process.env.VLC_PLUGIN_PATH = path.join(vlcPath, 'plugins');
        process.env.PATH = vlcPath + ';' + process.env.PATH;
        console.log('VLC path added to PATH:', vlcPath);
        console.log('VLC plugins path set to:', process.env.VLC_PLUGIN_PATH);
      }
      console.log('Looking for backend at:', backendPath);
      console.log('Backend exists:', fs.existsSync(backendPath));
      
      if (!fs.existsSync(backendPath)) {
        reject(new Error(`Backend executable not found at ${backendPath}`));
        return;
      }
      
      console.log('Starting backend process...');
      
      backendProcess = spawn(backendPath, [], {
        stdio: ['pipe', 'pipe', 'pipe'],
        detached: false
      });
      
      console.log('Backend process spawned, PID:', backendProcess.pid);
      
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
    }
  });
}

async function stopBackend() {
  if (!isDev && process.platform === 'win32') {
    // Production: Kill by port and process name
    spawn('netstat', ['-ano'], { stdio: 'pipe' }).stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      lines.forEach(line => {
        if (line.includes(':5001') && line.includes('LISTENING')) {
          const pid = line.trim().split(/\s+/).pop();
          if (pid && !isNaN(pid)) {
            spawn('taskkill', ['/f', '/pid', pid], { stdio: 'ignore' });
          }
        }
      });
    });
    
    // Also kill by executable name
    spawn('taskkill', ['/f', '/im', 'music_player_backend.exe'], { stdio: 'ignore' });
  }
  
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill('SIGKILL');
    backendProcess = null;
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
  app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', async (event) => {
  event.preventDefault();
  await stopBackend();
  app.exit(0);
});

// Handle app termination
process.on('SIGINT', async () => {
  await stopBackend();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await stopBackend();
  process.exit(0);
});

process.on('exit', () => {
  if (!isDev && process.platform === 'win32') {
    // Kill any process using port 5001
    const { execSync } = require('child_process');
    try {
      execSync('for /f "tokens=5" %a in (\'netstat -ano ^| findstr :5001\') do taskkill /f /pid %a', { stdio: 'ignore' });
    } catch (e) {}
    
    try {
      execSync('taskkill /f /im music_player_backend.exe', { stdio: 'ignore' });
    } catch (e) {}
  }
});