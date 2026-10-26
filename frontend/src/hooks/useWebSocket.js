import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket(url = 'ws://localhost:8000/ws/client') {
  const [isConnected, setIsConnected] = useState(false);
  const [appState, setAppState] = useState('IDLE');
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  const [devices, setDevices] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [latency, setLatency] = useState(0);

  const wsRef = useRef(null);
  const pingStartRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // Start ping loop
        pingStartRef.current = Date.now();
        ws.send(JSON.stringify({ type: 'PING' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'PONG') {
            setLatency(Date.now() - pingStartRef.current);
          } else if (data.type === 'INITIAL_STATE') {
            const p = data.payload;
            setAppState(p.state || 'IDLE');
            setActiveWorkflow(p.workflow || null);
            setIsPaused(p.is_paused || false);
            setIsStopped(p.is_stopped || false);
            if (p.contacts) setContacts(p.contacts);
            if (p.logs) setLogs(p.logs);
            if (p.devices) setDevices(p.devices);
          } else if (data.type === 'STATE_CHANGE') {
            setAppState(data.payload.state);
            setActiveWorkflow(data.payload.workflow);
            if (data.payload.state === 'PAUSED') setIsPaused(true);
            else setIsPaused(false);
            if (data.payload.state === 'STOPPED') setIsStopped(true);
            else if (data.payload.state === 'RUNNING') setIsStopped(false);
          } else if (data.type === 'AUDIT_LOG') {
            setLogs((prev) => [data.payload, ...prev.slice(0, 199)]);
          } else if (data.type === 'DEVICE_CONNECTED') {
            setDevices((prev) => {
              const filtered = prev.filter((d) => d.device_id !== data.payload.device_id);
              return [...filtered, data.payload];
            });
          }
        } catch (e) {
          console.error('Error handling WS message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2500);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      console.error('Failed to create WebSocket', e);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, [url]);

  useEffect(() => {
    connect();

    const interval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        pingStartRef.current = Date.now();
        wsRef.current.send(JSON.stringify({ type: 'PING' }));
      }
    }, 15000);

    return () => {
      clearInterval(interval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendEmergencyStop = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'EMERGENCY_STOP' }));
    }
  }, []);

  return {
    isConnected,
    appState,
    activeWorkflow,
    isPaused,
    isStopped,
    devices,
    contacts,
    setContacts,
    logs,
    setLogs,
    latency,
    sendEmergencyStop
  };
}
