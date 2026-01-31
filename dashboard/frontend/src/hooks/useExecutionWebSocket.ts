import { useEffect, useRef, useCallback } from 'react';
import { useExecutionsStore } from '@/stores';
import type { ExecutionEvent } from '@/types/execution';

// Use the same host/port as the page (goes through Vite proxy in dev)
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE = `${WS_PROTOCOL}//${window.location.host}/api/executions`;

interface UseExecutionWebSocketOptions {
  taskId?: string;
  enabled?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useExecutionWebSocket(options: UseExecutionWebSocketOptions = {}) {
  const {
    taskId,
    enabled = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { handleEvent, setWsConnected, fetchActiveExecutions } = useExecutionsStore();

  const connect = useCallback(() => {
    if (!enabled) return;

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Build WebSocket URL
    const wsUrl = taskId ? `${WS_BASE}/ws/${taskId}` : `${WS_BASE}/ws`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[ExecutionWS] Connected');
        setWsConnected(true);
        reconnectCountRef.current = 0;
        // Fetch initial state
        fetchActiveExecutions();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ExecutionEvent;
          handleEvent(data);
        } catch (e) {
          console.error('[ExecutionWS] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[ExecutionWS] Error:', error);
      };

      ws.onclose = (event) => {
        console.log('[ExecutionWS] Closed:', event.code, event.reason);
        setWsConnected(false);
        wsRef.current = null;

        // Attempt reconnect if not a clean close
        if (
          enabled &&
          event.code !== 1000 &&
          reconnectCountRef.current < maxReconnectAttempts
        ) {
          reconnectCountRef.current += 1;
          const delay = Math.min(
            reconnectInterval * Math.pow(1.5, reconnectCountRef.current - 1),
            30000
          );
          console.log(`[ExecutionWS] Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };
    } catch (e) {
      console.error('[ExecutionWS] Failed to create WebSocket:', e);
      setWsConnected(false);
    }
  }, [
    enabled,
    taskId,
    reconnectInterval,
    maxReconnectAttempts,
    handleEvent,
    setWsConnected,
    fetchActiveExecutions,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Intentional disconnect');
      wsRef.current = null;
    }
    setWsConnected(false);
  }, [setWsConnected]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [enabled, taskId, connect, disconnect]);

  // Expose reconnect function
  const reconnect = useCallback(() => {
    reconnectCountRef.current = 0;
    connect();
  }, [connect]);

  return {
    reconnect,
    disconnect,
    isConnected: useExecutionsStore((state) => state.wsConnected),
  };
}
