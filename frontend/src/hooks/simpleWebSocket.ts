import { useEffect, useRef, useState, useCallback } from 'react';
import type { Message } from '../types/chat';

export const useSimpleWebSocket = (
  chatUuid: string | null,
  onMessage: (message: any) => void
) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const onMessageCallback = useCallback(onMessage, [onMessage]);

  useEffect(() => {
    if (!chatUuid) return;

    // Use environment variable for WebSocket URL, fallback to localhost for development
    const wsBaseUrl = import.meta.env.VITE_API_URL?.replace('https://', 'wss://').replace('http://', 'ws://') || 'ws://localhost:8000';
    const wsUrl = `${wsBaseUrl}/api/chat/ws/${chatUuid}`;

    console.log('Connecting to WebSocket:', wsUrl);
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connection established.');
      setIsConnected(true);
      setConnectionError(null);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'connection_established') {
            onMessageCallback(data);
        } else {
            console.log("System Message: Connection acknowledged. State:", data.chat_state);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket connection closed.');
      setIsConnected(false);
    };

    wsRef.current.onerror = (event) => {
      console.error('WebSocket error:', event);
      setConnectionError('WebSocket connection failed');
    };

    return () => {
      wsRef.current?.close();
    };
  }, [chatUuid, onMessageCallback]);

  const sendMessage = (content: string, message_type: 'text' | 'button_response' | 'multi_select_response' | 'feeling_response') => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload = {
        type: "user_message",
        message_type: message_type,
        content: content,
      };
      wsRef.current.send(JSON.stringify(payload));
    } else {
      console.error("Cannot send message, WebSocket is not open.");
    }
  };

  return { isConnected, sendMessage, connectionError };
}; 