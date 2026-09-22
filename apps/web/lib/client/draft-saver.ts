/** Serializes draft writes, including blank drafts. A failed save can be retried without poisoning the queue. */
export class DraftSaver {
  private tail: Promise<void> = Promise.resolve();
  private saved: string;
  private readonly write: (text: string) => Promise<void>;

  constructor(initial: string, write: (text: string) => Promise<void>) {
    this.saved = initial;
    this.write = write;
  }

  isSaved(text: string): boolean {
    return text === this.saved;
  }

  save(text: string): Promise<void> {
    const operation = this.tail.then(async () => {
      if (this.isSaved(text)) return;
      await this.write(text);
      this.saved = text;
    });
    this.tail = operation.catch(() => undefined);
    return operation;
  }
}
