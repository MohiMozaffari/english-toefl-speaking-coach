// Helpers around the browser's built-in speechSynthesis API (offline, en-US voice).

import { ttsUrl } from "./api";

let cachedVoices: SpeechSynthesisVoice[] = [];

function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    const voices = window.speechSynthesis.getVoices();
    if (voices.length) {
      cachedVoices = voices;
      resolve(voices);
      return;
    }
    const handler = () => {
      cachedVoices = window.speechSynthesis.getVoices();
      window.speechSynthesis.removeEventListener("voiceschanged", handler);
      resolve(cachedVoices);
    };
    window.speechSynthesis.addEventListener("voiceschanged", handler);
    // Fallback in case the event never fires.
    setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1000);
  });
}

function pickUsEnglishVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices || !voices.length) return null;
  const notNonUs = (v: SpeechSynthesisVoice) =>
    !/UK|United Kingdom|AU|Australia|IN|India|ZA|South Africa|GB/i.test(v.name);
  const exact = voices.find((v) => v.lang === "en-US" && notNonUs(v));
  if (exact) return exact;
  const anyEnUs = voices.find((v) => v.lang === "en-US");
  if (anyEnUs) return anyEnUs;
  const anyEn = voices.find((v) => v.lang && v.lang.startsWith("en"));
  return anyEn || voices[0];
}

export async function getUsVoice(): Promise<SpeechSynthesisVoice | null> {
  const voices = cachedVoices.length ? cachedVoices : await loadVoices();
  return pickUsEnglishVoice(voices);
}

export interface SpeakOptions {
  rate?: number;
  pitch?: number;
  onEnd?: () => void;
}

export async function speak(text: string, { rate = 1, pitch = 1, onEnd }: SpeakOptions = {}) {
  if (!text) return;
  window.speechSynthesis.cancel();
  const voice = await getUsVoice();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";
  utter.rate = rate;
  utter.pitch = pitch;
  if (voice) utter.voice = voice;
  if (onEnd) utter.onend = onEnd;
  window.speechSynthesis.speak(utter);
  return utter;
}

export interface ConversationTurn {
  speaker: string;
  line: string;
}

export async function speakConversation(
  turns: ConversationTurn[],
  { onEnd, rate = 1, announceSpeaker = true }: { onEnd?: () => void; rate?: number; announceSpeaker?: boolean } = {}
): Promise<void> {
  window.speechSynthesis.cancel();
  const voice = await getUsVoice();
  return new Promise((resolve) => {
    let i = 0;
    const next = () => {
      if (i >= turns.length) {
        if (onEnd) onEnd();
        resolve();
        return;
      }
      const turn = turns[i];
      i += 1;
      const text = announceSpeaker ? `${turn.speaker}: ${turn.line}` : turn.line;
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = "en-US";
      utter.rate = rate;
      // Alternate pitch slightly so the two speakers sound distinct.
      utter.pitch = i % 2 === 1 ? 1.15 : 0.85;
      if (voice) utter.voice = voice;
      utter.onend = next;
      window.speechSynthesis.speak(utter);
    };
    next();
  });
}

export function stopSpeaking() {
  window.speechSynthesis.cancel();
}

// Plays `text` with a real Microsoft neural voice (edge-tts, via the backend),
// the same way Shadowing mode does, and automatically falls back to the local
// speechSynthesis voice if that endpoint is unreachable (offline / blocked).
// Returns a handle whose stop() halts whichever voice is currently playing.
export function playNeural(
  text: string,
  { accent = "en-US", rate = 1, onEnd, onFallback }: { accent?: string; rate?: number; onEnd?: () => void; onFallback?: () => void } = {}
): { stop: () => void } {
  window.speechSynthesis.cancel();
  const audio = new Audio(ttsUrl(text, accent));
  audio.playbackRate = rate;
  let done = false;

  const fallBack = () => {
    if (done) return;
    done = true;
    onFallback?.();
    speak(text, { rate, onEnd });
  };
  audio.addEventListener("ended", () => {
    if (done) return;
    done = true;
    onEnd?.();
  });
  audio.addEventListener("error", fallBack);
  audio.play().catch(fallBack);

  return {
    stop: () => {
      done = true;
      audio.pause();
      window.speechSynthesis.cancel();
    },
  };
}
