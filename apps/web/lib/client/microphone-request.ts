type Stream = { getTracks(): { stop(): void }[] };

/** A late browser permission result must not restart a cancelled or unmounted recording. */
export class MicrophoneRequestGate {
  private generation = 0;
  private pending = false;
  isPending() { return this.pending; }
  cancel() { this.generation++; this.pending = false; }

  async open<T extends Stream>(acquire: () => Promise<T>): Promise<T | null> {
    if (this.pending) return null;
    const generation = ++this.generation;
    this.pending = true;
    try {
      const stream = await acquire();
      if (generation !== this.generation) { stream.getTracks().forEach(track => track.stop()); return null; }
      return stream;
    } catch (cause) {
      if (generation !== this.generation) return null;
      throw cause;
    } finally {
      if (generation === this.generation) this.pending = false;
    }
  }
}
