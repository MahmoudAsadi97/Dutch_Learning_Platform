/** Serializes draft writes, including blank drafts. A failed save can be retried without poisoning the queue. */
export class DraftSaver {
  private tail: Promise<void> = Promise.resolve();
  private pending = 0;
  private saved: string;
  private readonly write: (text: string) => Promise<void>;

  constructor(initial: string, write: (text: string) => Promise<void>) {
    this.saved = initial;
    this.write = write;
  }

  isSaved(text: string): boolean {
    // An earlier in-flight write can still change the server, even if the editor returned to its original text.
    return this.pending === 0 && text === this.saved;
  }

  save(text: string): Promise<void> {
    this.pending++;
    const operation = this.tail.then(async () => {
      if (text === this.saved) return;
      await this.write(text);
      this.saved = text;
    }).finally(() => { this.pending--; });
    this.tail = operation.catch(() => undefined);
    return operation;
  }
}
