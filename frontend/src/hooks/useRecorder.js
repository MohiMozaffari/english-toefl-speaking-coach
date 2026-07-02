import { useCallback, useRef, useState } from "react";

// Wraps the browser MediaRecorder API for capturing microphone audio.
export function useRecorder() {
  const [status, setStatus] = useState("idle"); // idle | recording | stopped
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerRef = useRef(null);

  const start = useCallback(async () => {
    setError(null);
    setElapsed(0);
    chunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.start();
      setStatus("recording");
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
      return true;
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setError(
          "Microphone permission was denied. Please allow microphone access for this site in your browser settings and try again."
        );
      } else if (err.name === "NotFoundError") {
        setError("No microphone was found. Please connect a microphone and try again.");
      } else {
        setError(`Could not access the microphone: ${err.message}`);
      }
      setStatus("idle");
      return false;
    }
  }, []);

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        streamRef.current?.getTracks().forEach((t) => t.stop());
        setStatus("stopped");
        resolve(blob);
      };
      recorder.stop();
    });
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setElapsed(0);
    setError(null);
    chunksRef.current = [];
  }, []);

  return { status, error, elapsed, start, stop, reset };
}
