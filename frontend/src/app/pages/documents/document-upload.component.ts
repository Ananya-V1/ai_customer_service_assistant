import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DocumentsService, KnowledgeBase } from './documents.service';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="upload-card">
      <h3>Upload a document</h3>

      <label>
        Knowledge base
        <select [(ngModel)]="selectedKbId" name="kb">
          <option [ngValue]="null" disabled>Select a knowledge base…</option>
          @for (kb of knowledgeBases; track kb.id) {
            <option [ngValue]="kb.id">{{ kb.name }}</option>
          }
        </select>
      </label>

      <details>
        <summary>Create a new knowledge base</summary>
        <div class="new-kb">
          <input [(ngModel)]="newKbName" name="newKbName" placeholder="Knowledge base name" />
          <button type="button" (click)="createKb()" [disabled]="!newKbName.trim()">Create</button>
        </div>
      </details>

      <label>
        PDF file
        <input type="file" accept="application/pdf" (change)="onFileSelected($event)" />
      </label>

      @if (error()) {
        <p class="error">{{ error() }}</p>
      }

      <button type="button" (click)="upload()" [disabled]="!canUpload() || uploading()">
        {{ uploading() ? 'Uploading…' : 'Upload' }}
      </button>
    </div>
  `,
  styles: [
    `
    .upload-card {
      background: white;
      border-radius: 8px;
      padding: 1.25rem;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
      gap: 0.9rem;
      margin-bottom: 1.5rem;
    }
    label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.9rem; }
    select, input[type='text'], input[type='file'] {
      padding: 0.5rem;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    .new-kb { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
    .new-kb input { flex: 1; padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; }
    button {
      padding: 0.55rem 1rem;
      background: #1a1a2e;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      align-self: flex-start;
    }
    button:disabled { opacity: 0.6; cursor: default; }
    .error { color: #c0392b; font-size: 0.85rem; margin: 0; }
    `,
  ],
})
export class DocumentUploadComponent {
  @Input() knowledgeBases: KnowledgeBase[] = [];
  @Output() uploaded = new EventEmitter<void>();
  @Output() knowledgeBaseCreated = new EventEmitter<void>();

  selectedKbId: number | null = null;
  newKbName = '';
  selectedFile: File | null = null;
  uploading = signal(false);
  error = signal<string | null>(null);

  constructor(private documentsService: DocumentsService) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
  }

  canUpload(): boolean {
    return this.selectedKbId !== null && this.selectedFile !== null;
  }

  createKb(): void {
    const name = this.newKbName.trim();
    if (!name) {
      return;
    }
    this.documentsService.createKnowledgeBase(name).subscribe({
      next: () => {
        this.newKbName = '';
        this.knowledgeBaseCreated.emit();
      },
      error: () => this.error.set('Could not create knowledge base.'),
    });
  }

  upload(): void {
    if (!this.canUpload()) {
      return;
    }
    this.error.set(null);
    this.uploading.set(true);
    this.documentsService.uploadDocument(this.selectedKbId!, this.selectedFile!).subscribe({
      next: () => {
        this.uploading.set(false);
        this.selectedFile = null;
        this.uploaded.emit();
      },
      error: () => {
        this.uploading.set(false);
        this.error.set('Upload failed. The file may be too large or not a valid PDF.');
      },
    });
  }
}
