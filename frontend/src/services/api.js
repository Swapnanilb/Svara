import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    if (error.code === 'ECONNREFUSED' || error.message === 'Network Error') {
      console.error('Backend server is not running on port 5001');
    }
    throw error;
  }
);

export const musicAPI = {
  // Player controls
  async getStatus() {
    const response = await api.get('/status');
    return response.data;
  },

  async play(playlistId, songIndex) {
    const response = await api.post('/play', {
      playlist_id: playlistId,
      song_index: songIndex
    });
    return response.data;
  },

  async togglePause() {
    const response = await api.post('/pause');
    return response.data;
  },

  async nextSong() {
    const response = await api.post('/next');
    return response.data;
  },

  async previousSong() {
    const response = await api.post('/previous');
    return response.data;
  },

  async setVolume(volume) {
    const response = await api.post('/volume', { volume });
    return response.data;
  },

  async seek(position) {
    const response = await api.post('/seek', { position });
    return response.data;
  },

  // Playlist management
  async getPlaylists() {
    const response = await api.get('/playlists');
    return response.data;
  },

  async getPlaylistSongs(playlistId) {
    const response = await api.get(`/playlist/${playlistId}/songs`);
    return response.data;
  },

  async addPlaylist(url) {
    const response = await api.post('/playlist/add', { url });
    return response.data;
  },

  async toggleShuffle() {
    const response = await api.post('/shuffle');
    return response.data;
  },

  async toggleRepeat() {
    const response = await api.post('/repeat');
    return response.data;
  },

  async checkSong(url, playlistId = null) {
    const response = await api.post('/song/check', {
      url,
      playlist_id: playlistId
    }, { timeout: 30000 }); // 30 second timeout for song operations
    return response.data;
  },

  async addSong(url, playlistId = null, playlistName = null) {
    const response = await api.post('/song/add', {
      url,
      playlist_id: playlistId,
      playlist_name: playlistName
    }, { timeout: 60000 }); // 60 second timeout for song addition
    return response.data;
  },

  async toggleMute() {
    const response = await api.post('/mute');
    return response.data;
  },

  async loadPlaylist(playlistId) {
    const response = await api.post('/playlist/load', {
      playlist_id: playlistId,
      song_index: 0
    });
    // Preload songs in background
    this.preloadPlaylist(playlistId).catch(console.error);
    return response.data;
  },

  async refreshPlaylist(playlistId) {
    const response = await api.post(`/playlist/${playlistId}/refresh`);
    return response.data;
  },

  async preloadPlaylist(playlistId) {
    const response = await api.post('/playlist/preload', {
      playlist_id: playlistId,
      song_index: 0
    });
    return response.data;
  },

  async deletePlaylist(playlistId) {
    const response = await api.delete(`/playlist/${playlistId}`);
    return response.data;
  }
};

export const getCacheStats = async () => {
  const response = await api.get('/cache/stats');
  return response.data;
};

export const clearCache = async () => {
  const response = await api.post('/cache/clear');
  return response.data;
};

export default api;