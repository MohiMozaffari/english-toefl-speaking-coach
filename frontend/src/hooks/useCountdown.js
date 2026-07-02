import { useCallback, useEffect, useRef, useState } from "react";

// Simple imperative countdown timer in whole seconds.
export function useCountdown() {
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);
  const onCompleteRef = useRef(null);

  const start = useCallback((seconds, onComplete) => {
    onCompleteRef.current = onComplete || null;
    setSecondsLeft(seconds);
    setRunning(true);
  }, []);

  const stop = useCallback(() => {
    setRunning(false);
  }, []);

  useEffect(() => {
    if (!running) return undefined;
    intervalRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(intervalRef.current);
          setRunning(false);
          if (onCompleteRef.current) onCompleteRef.current();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, [running]);

  return { secondsLeft, running, start, stop };
}
