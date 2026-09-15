import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AsyncPipe } from '@angular/common';
import { AuthService } from './core/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, AsyncPipe],
  template: `
    <header class="topbar">
      <a routerLink="/" class="brand">Customer Service Agent</a>
      <nav>
        @if (auth.isAdmin()) {
          <a routerLink="/documents">Documents</a>
        }
        @if (auth.isAuthenticated()) {
          <button (click)="auth.logout()">Log out</button>
        } @else {
          <a routerLink="/login">Admin login</a>
        }
      </nav>
    </header>
    <main>
      <router-outlet></router-outlet>
    </main>
  `,
  styles: [
    `
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 1.5rem;
      background: #1a1a2e;
      color: white;
    }
    .brand { color: white; text-decoration: none; font-weight: 600; }
    nav { display: flex; gap: 1rem; align-items: center; }
    nav a { color: #cbd5e1; text-decoration: none; }
    nav button {
      background: transparent;
      border: 1px solid #cbd5e1;
      color: #cbd5e1;
      border-radius: 4px;
      padding: 0.3rem 0.7rem;
      cursor: pointer;
    }
    main { max-width: 900px; margin: 0 auto; padding: 1.5rem; }
    `,
  ],
})
export class AppComponent {
  constructor(public auth: AuthService) {}
}
