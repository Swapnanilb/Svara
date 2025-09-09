// Preload script for security
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add any secure APIs here if needed
  platform: process.platform,
  version: process.versions.electron
});