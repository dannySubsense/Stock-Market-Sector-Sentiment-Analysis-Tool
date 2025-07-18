/**
 * Real-Time Data Hook - Slice 1A Implementation
 * Manages WebSocket connections for real-time sector sentiment updates
 * Provides fallback to polling and graceful error handling
 */
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

// Types for real-time data
interface SectorUpdate {
  sector: string;
  sentiment_score: number;
  color_classification: string;
  trading_signal: string;
  confidence_level: number;
  timeframe_scores: {
    '30min': number;
    '1day': number;
    '3day': number;
    '1week': number;
  };
  top_bullish?: any[];
  top_bearish?: any[];
  last_updated: string;
}

interface RealTimeData {
  sectors: SectorUpdate[];
  lastUpdated: string;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  error?: string;
}

interface UseRealTimeDataOptions {
  enableWebSocket?: boolean;
  pollingInterval?: number; // milliseconds
  reconnectAttempts?: number;
  apiBaseUrl?: string;
}

interface UseRealTimeDataReturn extends RealTimeData {
  refreshData: () => Promise<void>;
  forceRefresh: () => Promise<void>;
  isLoading: boolean;
  retry: () => void;
}

const useRealTimeData = (options: UseRealTimeDataOptions = {}): UseRealTimeDataReturn => {
  const {
    enableWebSocket = true,
    pollingInterval = 30000, // 30 seconds default
    reconnectAttempts = 3,
    apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  } = options;

  // State management
  const [data, setData] = useState<RealTimeData>({
    sectors: [],
    lastUpdated: '',
    connectionStatus: 'disconnected'
  });
  
  const [isLoading, setIsLoading] = useState(false);
  
  // Refs for connection management
  const socketRef = useRef<Socket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const mountedRef = useRef(true);

  // Fetch data from API
  const fetchSectorData = useCallback(async (): Promise<SectorUpdate[]> => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/sectors`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Handle different response formats
      if (result.sectors && Array.isArray(result.sectors)) {
        return result.sectors;
      } else if (Array.isArray(result)) {
        return result;
      } else {
        console.warn('Unexpected API response format:', result);
        return [];
      }
    } catch (error) {
      console.error('Error fetching sector data:', error);
      throw error;
    }
  }, [apiBaseUrl]);

  // Update data state
  const updateData = useCallback((newSectors: SectorUpdate[], status: RealTimeData['connectionStatus'] = 'connected') => {
    if (!mountedRef.current) return;
    
    setData(prevData => ({
      ...prevData,
      sectors: newSectors,
      lastUpdated: new Date().toISOString(),
      connectionStatus: status,
      error: undefined
    }));
  }, []);

  // Handle connection errors
  const handleError = useCallback((error: string, status: RealTimeData['connectionStatus'] = 'error') => {
    if (!mountedRef.current) return;
    
    console.error('Real-time data error:', error);
    setData(prevData => ({
      ...prevData,
      connectionStatus: status,
      error
    }));
  }, []);

  // Refresh data manually
  const refreshData = useCallback(async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      const newSectors = await fetchSectorData();
      updateData(newSectors);
    } catch (error) {
      handleError(error instanceof Error ? error.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchSectorData, updateData, handleError, isLoading]);

  // Force refresh (ignores loading state)
  const forceRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const newSectors = await fetchSectorData();
      updateData(newSectors);
    } catch (error) {
      handleError(error instanceof Error ? error.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [fetchSectorData, updateData, handleError]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || socketRef.current?.connected) return;

    try {
      setData(prevData => ({ ...prevData, connectionStatus: 'connecting' }));
      
      const socket = io(apiBaseUrl, {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: reconnectAttempts,
        reconnectionDelay: 2000
      });

      socket.on('connect', () => {
        console.log('WebSocket connected');
        reconnectCountRef.current = 0;
        setData(prevData => ({ ...prevData, connectionStatus: 'connected', error: undefined }));
        
        // Join sector updates room
        socket.emit('join_sector_updates');
      });

      socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setData(prevData => ({ ...prevData, connectionStatus: 'disconnected' }));
      });

      socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        reconnectCountRef.current++;
        
        if (reconnectCountRef.current >= reconnectAttempts) {
          handleError('WebSocket connection failed, falling back to polling', 'error');
          startPolling(); // Fallback to polling
        }
      });

      // Listen for sector updates
      socket.on('sector_update', (sectorUpdate: SectorUpdate) => {
        console.log('Received sector update:', sectorUpdate);
        
        setData(prevData => {
          const updatedSectors = prevData.sectors.map(sector =>
            sector.sector === sectorUpdate.sector ? sectorUpdate : sector
          );
          
          // If sector doesn't exist, add it
          if (!updatedSectors.find(s => s.sector === sectorUpdate.sector)) {
            updatedSectors.push(sectorUpdate);
          }
          
          return {
            ...prevData,
            sectors: updatedSectors,
            lastUpdated: new Date().toISOString()
          };
        });
      });

      // Listen for full sector data updates
      socket.on('sectors_update', (sectorsData: SectorUpdate[]) => {
        console.log('Received full sectors update');
        updateData(sectorsData);
      });

      // Listen for analysis completion
      socket.on('analysis_complete', (result: any) => {
        console.log('Analysis completed:', result);
        // Refresh data after analysis completion
        refreshData();
      });

      socketRef.current = socket;
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      handleError('Failed to establish WebSocket connection', 'error');
      startPolling(); // Fallback to polling
    }
  }, [apiBaseUrl, enableWebSocket, reconnectAttempts, handleError, updateData, refreshData]);

  // Polling fallback
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return; // Already polling
    
    console.log('Starting polling fallback');
    
    const poll = async () => {
      if (!mountedRef.current) return;
      
      try {
        const newSectors = await fetchSectorData();
        updateData(newSectors, 'connected');
      } catch (error) {
        console.error('Polling error:', error);
        handleError('Polling failed', 'error');
      }
    };

    // Initial poll
    poll();
    
    // Set up interval
    pollingIntervalRef.current = setInterval(poll, pollingInterval);
  }, [fetchSectorData, updateData, handleError, pollingInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
  }, []);

  // Retry connection
  const retry = useCallback(() => {
    reconnectCountRef.current = 0;
    setData(prevData => ({ ...prevData, error: undefined }));
    
    // Disconnect existing connections
    disconnectWebSocket();
    stopPolling();
    
    // Retry based on preference
    if (enableWebSocket) {
      connectWebSocket();
    } else {
      startPolling();
    }
  }, [enableWebSocket, connectWebSocket, startPolling, disconnectWebSocket, stopPolling]);

  // Initialize connection on mount
  useEffect(() => {
    mountedRef.current = true;
    
    // Initial data fetch
    refreshData();
    
    // Start real-time connection
    if (enableWebSocket) {
      connectWebSocket();
    } else {
      startPolling();
    }

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      disconnectWebSocket();
      stopPolling();
    };
  }, [enableWebSocket, connectWebSocket, startPolling, disconnectWebSocket, stopPolling, refreshData]);

  // Handle visibility change (pause/resume updates)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, pause updates
        if (socketRef.current?.connected) {
          socketRef.current.emit('pause_updates');
        }
      } else {
        // Page is visible, resume updates
        if (socketRef.current?.connected) {
          socketRef.current.emit('resume_updates');
        }
        // Refresh data when page becomes visible
        refreshData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [refreshData]);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      console.log('Network came back online');
      retry();
    };

    const handleOffline = () => {
      console.log('Network went offline');
      handleError('Network connection lost', 'disconnected');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [retry, handleError]);

  return {
    ...data,
    refreshData,
    forceRefresh,
    isLoading,
    retry
  };
};

export default useRealTimeData;

// Export types for use in components
export type { SectorUpdate, RealTimeData, UseRealTimeDataOptions, UseRealTimeDataReturn }; 