import { Routes } from '@angular/router';
import { adminGuard } from './core/admin.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/chat/chat-page.component').then((m) => m.ChatPageComponent),
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'documents',
    canActivate: [adminGuard],
    loadComponent: () =>
      import('./pages/documents/documents-page.component').then((m) => m.DocumentsPageComponent),
  },
  { path: '**', redirectTo: '' },
];
