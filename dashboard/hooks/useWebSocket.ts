'use client';

import { useEffect, useRef } from 'react';

export default function useWebSocket(
  url: string,
  onMessage: (data: unknown) => void,
) {
  const cb = useRef(onMessage);
  cb.current = onMessage;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(url);

      ws.onopen = () => {
        /* connected */
      };

      ws.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          cb.current(parsed);
        } catch {
          /* skip non-JSON messages */
        }
      };

      ws.onclose = () => {
        timer = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      clearTimeout(timer);
      ws?.close();
    };
  }, [url]);
}
