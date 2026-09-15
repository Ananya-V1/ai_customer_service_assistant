import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface KnowledgeBase {
  id: number;
  name: string;
  slug: string;
  description: string;
  document_count: number;
}

export interface DocumentItem {
  id: number;
  knowledge_base: number;
  knowledge_base_name: string;
  title: string;
  file: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  page_count: number | null;
  error_message: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class DocumentsService {
  constructor(private http: HttpClient) {}

  listKnowledgeBases(): Observable<KnowledgeBase[]> {
    return this.http.get<KnowledgeBase[]>(`${environment.apiUrl}/knowledge-bases/`);
  }

  createKnowledgeBase(name: string): Observable<KnowledgeBase> {
    return this.http.post<KnowledgeBase>(`${environment.apiUrl}/knowledge-bases/`, { name });
  }

  listDocuments(): Observable<DocumentItem[]> {
    return this.http.get<DocumentItem[]>(`${environment.apiUrl}/documents/`);
  }

  uploadDocument(knowledgeBaseId: number, file: File): Observable<DocumentItem> {
    const formData = new FormData();
    formData.append('knowledge_base', String(knowledgeBaseId));
    formData.append('file', file);
    return this.http.post<DocumentItem>(`${environment.apiUrl}/documents/`, formData);
  }
}
