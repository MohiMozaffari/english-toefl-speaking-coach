import { useCallback, useEffect, useRef } from "react";
import { playNeural } from "../speech";

// Plays short snippets with a real neural voice (edge-tts) — and falls back to
// the browser voice if that's unreachable. Guarantees only one snippet plays at
// a time and that audio stops when the component unmounts. American English by
// default (the Pronunciation Lab is American-English focused).
export function useNeuralPlayer(accent = "en-US") {
  const ref = useRef<{ stop: () => void } | null>(null);

  const stop = useCallback(() => {
    ref.current?.stop();
    ref.current = null;
  }, []);

  const play = useCallback(
    (text: string, rate = 1) => {
      ref.current?.stop();
      ref.current = playNeural(text, { accent, rate });
    },
    [accent]
  );

  useEffect(() => stop, [stop]);

  return { play, stop };
}
