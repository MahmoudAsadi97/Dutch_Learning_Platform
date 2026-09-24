/** Coordinate synthetic players without retaining DOM nodes or learner audio in application state. */
let active: { owner: symbol; stop: () => void } | null = null;
let nativeObservers = 0;
let recordingLocks = 0;
const recordingListeners = new Set<() => void>();

export function isAudioRecording() { return recordingLocks > 0; }
export function subscribeAudioRecording(listener: () => void): () => void { recordingListeners.add(listener); return () => recordingListeners.delete(listener); }

/** Pause all playback before microphone permission/recording, then hold focus through the recording tail. */
export function suspendAudioForRecording(): () => void {
  recordingLocks++;
  stopFocusedAudio();
  pauseNativePlayers();
  recordingListeners.forEach(listener => listener());
  let released = false;
  return () => {
    if (released) return;
    released = true;
    recordingLocks = Math.max(0, recordingLocks - 1);
    recordingListeners.forEach(listener => listener());
  };
}

function pauseNativePlayers(except?: EventTarget | null) {
  if (typeof document === "undefined") return;
  document.querySelectorAll("audio, video").forEach(element => {
    if (element !== except && element instanceof HTMLMediaElement && !element.paused) element.pause();
  });
}

function nativeStarted(event: Event) {
  if (!(event.target instanceof HTMLMediaElement)) return;
  if (isAudioRecording()) { event.target.pause(); return; }
  stopFocusedAudio();
  pauseNativePlayers(event.target);
}

/** One document listener, shared by many buttons, also coordinates native recording replay controls. */
export function observeNativeAudioFocus(): () => void {
  if (typeof document === "undefined") return () => {};
  if (nativeObservers++ === 0) document.addEventListener("play", nativeStarted, true);
  let removed = false;
  return () => {
    if (removed) return;
    removed = true;
    if (--nativeObservers === 0) document.removeEventListener("play", nativeStarted, true);
  };
}

export function claimAudioFocus(owner: symbol, stop: () => void) {
  if (isAudioRecording()) return false;
  if (active?.owner === owner) return true;
  const previous = active;
  active = null;
  previous?.stop();
  pauseNativePlayers();
  active = { owner, stop };
  return true;
}

export function releaseAudioFocus(owner: symbol) {
  if (active?.owner === owner) active = null;
}

export function stopFocusedAudio() {
  const previous = active;
  active = null;
  previous?.stop();
}
