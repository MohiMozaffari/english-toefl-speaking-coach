import { useCallback, useEffect, useRef, useState } from "react";

// Simple imperative countdown timer in whole seconds.
//
// `enforced` (default true) controls what happens at 0: enforced timers fire
// onComplete (Exam mode auto-stops recording and advances). Unenforced timers
// still count down for realism but hold at 0 without firing — the learner
// finishes when ready (Practice mode).
export function useCountdown() {
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [running, setRunning] = useState(false);
  const [reachedZero, setReachedZero] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCompleteRef = useRef<(() => void) | null>(null);
  const enforcedRef = useRef(true);

  const start = useCallback((seconds: number, onComplete?: () => void, enforced = true) => {
    onCompleteRef.current = onComplete || null;
    enforcedRef.current = enforced;
    setReachedZero(false);
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
          if (intervalRef.current) clearInterval(intervalRef.current);
          setRunning(false);
          setReachedZero(true);
          if (enforcedRef.current && onCompleteRef.current) onCompleteRef.current();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running]);

  return { secondsLeft, running, reachedZero, start, stop };
}
