import { useEffect } from "react";

// Placeholder hook. For now, we only simulate incoming events in mock mode.
export function useWebSocket(onMessage) {
  useEffect(() => {
    // In a real implementation, connect to wss:// endpoint and listen.
    // For now, do nothing (or you could simulate events here).
  }, [onMessage]);
}
