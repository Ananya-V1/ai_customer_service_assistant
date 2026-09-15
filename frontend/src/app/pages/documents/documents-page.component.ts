import { Component, OnInit } from '@angular/core';
import { DocumentUploadComponent } from './document-upload.component';
import { DocumentListComponent } from './document-list.component';
import { DocumentItem, DocumentsService, KnowledgeBase } from './documents.service';

@Component({
  selector: 'app-documents-page',
  standalone: true,
  imports: [DocumentUploadComponent, DocumentListComponent],
  template: `
    <h2>Knowledge base management</h2>
    <app-document-upload
      [knowledgeBases]="knowledgeBases"
      (uploaded)="loadDocuments()"
      (knowledgeBaseCreated)="loadKnowledgeBases()"
    ></app-document-upload>
    <app-document-list [documents]="documents" (refresh)="loadDocuments()"></app-document-list>
  `,
})
export class DocumentsPageComponent implements OnInit {
  knowledgeBases: KnowledgeBase[] = [];
  documents: DocumentItem[] = [];

  constructor(private documentsService: DocumentsService) {}

  ngOnInit(): void {
    this.loadKnowledgeBases();
    this.loadDocuments();
  }

  loadKnowledgeBases(): void {
    this.documentsService.listKnowledgeBases().subscribe((kbs) => (this.knowledgeBases = kbs));
  }

  loadDocuments(): void {
    this.documentsService.listDocuments().subscribe((docs) => (this.documents = docs));
  }
}
