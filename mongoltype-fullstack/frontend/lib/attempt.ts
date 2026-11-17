type Send = (path: string, body: unknown) => Promise<unknown>;

// One instance per exercise: no mutable references shared across restarts.
export class Attempt {
  private startRequest: Promise<unknown> | null = null;
  private queue: Promise<unknown> = Promise.resolve();
  private seq = 0;
  private saving: Promise<unknown> | null = null;
  private checkpointBusy = false;

  private id: string;
  private send: Send;
  constructor(id: string, send: Send) {this.id=id;this.send=send;}

  start(recover = false): Promise<unknown> {
    if (!this.startRequest) {
      this.startRequest = this.send(`/tests/${this.id}/start`, {recover}).catch(error => {
        this.startRequest = null;
        throw error;
      });
    }
    return this.startRequest;
  }

  checkpoint(text: string, final = false): Promise<unknown> {
    if (this.checkpointBusy && !final) return this.queue;
    this.checkpointBusy = true;
    const seq = ++this.seq;
    const next = this.queue.catch(() => undefined).then(async () => {
      await this.start(true);
      return this.send(`/tests/${this.id}/checkpoint`, {seq, typed_text: text});
    }).finally(() => {if(this.queue === next)this.checkpointBusy = false;});
    this.queue = next;
    return next;
  }

  save(payload: {session_id: string; typed_text: string; elapsed_ms: number}): Promise<unknown> {
    if (!this.saving) {
      this.saving = (async () => {
        // A failed start is retried; a newly recovered start is practice only.
        await this.start(true);
        await this.queue.catch(() => undefined);
        return this.send('/results', payload);
      })().finally(() => {this.saving = null;});
    }
    return this.saving;
  }
}
