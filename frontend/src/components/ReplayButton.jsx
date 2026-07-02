import { useState } from "react";
import { speak, stopSpeaking } from "../speech.js";

export default function ReplayButton({ text, label = "🔊 Replay" }) {
  const [speaking, setSpeaking] = useState(false);

  if (!text) return null;

  const handleClick = async () => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    setSpeaking(true);
    await speak(text, { onEnd: () => setSpeaking(false) });
  };

  return (
    <button type="button" onClick={handleClick}>
      {speaking ? "⏹ Stop" : label}
    </button>
  );
}
