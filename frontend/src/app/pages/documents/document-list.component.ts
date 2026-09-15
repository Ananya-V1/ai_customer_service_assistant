import { Component, EventEmitter, Input, Output } from '@angular/core';
import { DocumentItem } from './documents.service';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [],
  template: `
    <div class="list-card">
      <div class="list-header">
        <h3>Documents</h3>
        <button type="button" (click)="refresh.emit()">Refresh</button>
      </div>
      @if (documents.length === 0) {
        <p class="empty">No documents uploaded yet.</p>
      } @else {
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Knowledge base</th>
              <th>Status</th>
              <th>Pages</th>
            </tr>
          </thead>
          <tbody>
            @for (doc of documents; track doc.id) {
              <tr>
                <td>{{ doc.title }}</td>
                <td>{{ doc.knowledge_base_name }}</td>
                <td>
                  <span class="status" [class]="doc.status">{{ doc.status }}</span>
                  @if (doc.status === 'failed' && doc.error_message) {
                    <div class="error-message">{{ doc.error_message }}</div>
                  }
                </td>
                <td>{{ doc.page_count ?? '—' }}</td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
  styles: [
    `
    .list-card {
      background: white;
      border-radius: 8px;
      padding: 1.25rem;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }
    .list-header { display: flex; justify-content: space-between; align-items: center; }
    .list-header button {
      background: transparent;
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 0.35rem 0.7rem;
      cursor: pointer;
    }
    .empty { color: #666; }
    table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; }
    th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }
    .status {
      display: inline-block;
      padding: 0.15rem 0.6rem;
      border-radius: 12px;
      font-size: 0.75rem;
      text-transform: capitalize;
    }
    .status.pending, .status.processing { background: #fff3cd; color: #7a5b00; }
    .status.ready { background: #d4edda; color: #1a6b2f; }
    .status.failed { background: #f8d7da; color: #a01c2a; }
    .error-message { font-size: 0.75rem; color: #a01c2a; margin-top: 0.25rem; }
    `,
  ],
})
export class DocumentListComponent {
  @Input() documents: DocumentItem[] = [];
  @Output() refresh = new EventEmitter<void>();
}
