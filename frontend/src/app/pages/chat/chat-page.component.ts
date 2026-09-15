import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

interface Source {
  knowledge_base: string;
  document: string;
  document_id: number;
  chunk_id: number;
  distance: number;
}

interface ChatResponse {
  conversation_id: number;
  answer: string;
  sources: Source[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="chat">
      <div class="messages">
        @if (messages().length === 0) {
          <p class="empty">Ask a question about our products or policies to get started.</p>
        }
        @for (message of messages(); track $index) {
          <div class="bubble" [class.user]="message.role === 'user'">
            <p>{{ message.content }}</p>
            @if (message.sources && message.sources.length > 0) {
              <div class="sources">
                Sources:
                @for (source of message.sources; track source.chunk_id) {
                  <span class="source-chip">{{ source.knowledge_base }} / {{ source.document }}</span>
                }
              </div>
            }
          </div>
        }
        @if (loading()) {
          <div class="bubble">
            <p>Thinking…</p>
          </div>
        }
      </div>
      <form class="composer" (ngSubmit)="send()">
        <input
          name="message"
          [(ngModel)]="draft"
          placeholder="Type your question…"
          [disabled]="loading()"
          autocomplete="off"
        />
        <button type="submit" [disabled]="loading() || !draft.trim()">Send</button>
      </form>
    </div>
  `,
  styles: [
    `
    .chat { display: flex; flex-direction: column; height: calc(100vh - 140px); }
    .messages {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 0.5rem 0;
    }
    .empty { color: #666; text-align: center; margin-top: 2rem; }
    .bubble {
      background: white;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      max-width: 75%;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    }
    .bubble p { margin: 0; white-space: pre-wrap; }
    .bubble.user {
      align-self: flex-end;
      background: #1a1a2e;
      color: white;
    }
    .sources {
      margin-top: 0.5rem;
      font-size: 0.75rem;
      color: #666;
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      align-items: center;
    }
    .source-chip {
      background: #eef1f5;
      border-radius: 12px;
      padding: 0.15rem 0.6rem;
    }
    .composer { display: flex; gap: 0.5rem; padding-top: 0.75rem; }
    .composer input {
      flex: 1;
      padding: 0.7rem;
      border: 1px solid #ccc;
      border-radius: 6px;
    }
    .composer button {
      padding: 0.7rem 1.2rem;
      background: #1a1a2e;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }
    .composer button:disabled { opacity: 0.6; cursor: default; }
    `,
  ],
})
export class ChatPageComponent {
  messages = signal<ChatMessage[]>([]);
  draft = '';
  loading = signal(false);
  private conversationId: number | null = null;

  constructor(private http: HttpClient) {}

  send(): void {
    const question = this.draft.trim();
    if (!question) {
      return;
    }
    this.messages.update((msgs) => [...msgs, { role: 'user', content: question }]);
    this.draft = '';
    this.loading.set(true);

    this.http
      .post<ChatResponse>(`${environment.apiUrl}/chat/`, {
        message: question,
        conversation_id: this.conversationId,
      })
      .subscribe({
        next: (res) => {
          this.conversationId = res.conversation_id;
          this.messages.update((msgs) => [
            ...msgs,
            { role: 'assistant', content: res.answer, sources: res.sources },
          ]);
          this.loading.set(false);
        },
        error: () => {
          this.messages.update((msgs) => [
            ...msgs,
            { role: 'assistant', content: 'Something went wrong. Please try again.' },
          ]);
          this.loading.set(false);
        },
      });
  }
}
