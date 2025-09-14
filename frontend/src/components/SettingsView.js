import React, { useState, useEffect } from 'react';
import { getCacheStats, clearCache } from '../services/api';

const SettingsView = ({ theme, onThemeChange }) => {
  const [cacheStats, setCacheStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCacheStats();
  }, []);

  const loadCacheStats = async () => {
    try {
      const stats = await getCacheStats();
      setCacheStats(stats);
    } catch (error) {
      console.error('Failed to load cache stats:', error);
    }
  };

  const handleClearCache = async () => {
    setLoading(true);
    try {
      await clearCache();
      await loadCacheStats();
    } catch (error) {
      console.error('Failed to clear cache:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '40px',
      color: theme === 'dark' ? '#fff' : '#333'
    }}>
      <h2 style={{ 
        fontSize: '28px', 
        fontWeight: '700', 
        marginBottom: '30px',
        color: theme === 'dark' ? '#fff' : '#333'
      }}>
        Settings
      </h2>
      
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ 
          fontSize: '18px', 
          fontWeight: '600', 
          marginBottom: '15px',
          color: theme === 'dark' ? '#fff' : '#333'
        }}>
          Appearance
        </h3>
        
        <div style={{ display: 'flex', gap: '15px' }}>
          <button
            onClick={() => onThemeChange('light')}
            style={{
              padding: '10px 20px',
              border: theme === 'light' ? '2px solid #ff6b35' : '1px solid #ddd',
              borderRadius: '8px',
              background: theme === 'light' ? '#fff3f0' : (theme === 'dark' ? '#333' : 'white'),
              color: theme === 'dark' ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Light Theme
          </button>
          
          <button
            onClick={() => onThemeChange('dark')}
            style={{
              padding: '10px 20px',
              border: theme === 'dark' ? '2px solid #ff6b35' : '1px solid #ddd',
              borderRadius: '8px',
              background: theme === 'dark' ? '#444' : 'white',
              color: theme === 'dark' ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Dark Theme
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ 
          fontSize: '18px', 
          fontWeight: '600', 
          marginBottom: '15px',
          color: theme === 'dark' ? '#fff' : '#333'
        }}>
          Cache Management
        </h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
          <button
            onClick={loadCacheStats}
            style={{
              padding: '8px 16px',
              border: '1px solid #4CAF50',
              borderRadius: '6px',
              background: 'transparent',
              color: '#4CAF50',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Refresh Stats
          </button>
          {cacheStats && (
            <span style={{ fontSize: '12px', opacity: 0.7 }}>
              URL: {cacheStats.url_cache_count} | Metadata: {cacheStats.metadata_cache_count}
            </span>
          )}
        </div>
        
        {cacheStats && (
          <div style={{
            background: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
            border: `1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '15px'
          }}>
            {/* Cache Visualization with aligned text */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '15px' }}>
              {/* URL Cache */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  background: `conic-gradient(#ff6b35 0deg ${(cacheStats.url_cache_count / Math.max(cacheStats.url_cache_count + cacheStats.metadata_cache_count, 1)) * 360}deg, ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} ${(cacheStats.url_cache_count / Math.max(cacheStats.url_cache_count + cacheStats.metadata_cache_count, 1)) * 360}deg)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: theme === 'dark' ? '0 4px 20px rgba(255,107,53,0.3)' : '0 4px 20px rgba(255,107,53,0.2)',
                  marginBottom: '10px'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: theme === 'dark' ? '#1a1a1a' : '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#ff6b35'
                  }}>
                    {cacheStats.url_cache_count}
                  </div>
                </div>
                <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '5px', textAlign: 'center' }}>URL Cache</div>
                <div style={{ fontSize: '16px', fontWeight: '600', textAlign: 'center' }}>{cacheStats.url_cache_count} songs</div>
              </div>
              
              {/* Metadata Cache */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  background: `conic-gradient(#4CAF50 0deg ${(cacheStats.metadata_cache_count / Math.max(cacheStats.url_cache_count + cacheStats.metadata_cache_count, 1)) * 360}deg, ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} ${(cacheStats.metadata_cache_count / Math.max(cacheStats.url_cache_count + cacheStats.metadata_cache_count, 1)) * 360}deg)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: theme === 'dark' ? '0 4px 20px rgba(76,175,80,0.3)' : '0 4px 20px rgba(76,175,80,0.2)',
                  marginBottom: '10px'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: theme === 'dark' ? '#1a1a1a' : '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#4CAF50'
                  }}>
                    {cacheStats.metadata_cache_count}
                  </div>
                </div>
                <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '5px', textAlign: 'center' }}>Metadata Cache</div>
                <div style={{ fontSize: '16px', fontWeight: '600', textAlign: 'center' }}>{cacheStats.metadata_cache_count} songs</div>
              </div>
            </div>
            
            <div style={{ fontSize: '12px', opacity: 0.6 }}>
              Cache improves loading times by storing song URLs and metadata locally
            </div>
          </div>
        )}
        
        <button
          onClick={handleClearCache}
          disabled={loading}
          style={{
            padding: '10px 20px',
            border: '1px solid #ff6b35',
            borderRadius: '8px',
            background: loading ? (theme === 'dark' ? '#333' : '#f5f5f5') : 'transparent',
            color: loading ? (theme === 'dark' ? '#666' : '#999') : '#ff6b35',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            transition: 'all 0.2s ease'
          }}
        >
          {loading ? 'Clearing...' : 'Clear Cache'}
        </button>
      </div>
    </div>
  );
};

export default SettingsView;