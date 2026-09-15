import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

interface LoginResponse {
  token: string;
  is_staff: boolean;
}

const TOKEN_KEY = 'csagent_token';
const IS_ADMIN_KEY = 'csagent_is_admin';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private tokenSignal = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  private isAdminSignal = signal<boolean>(localStorage.getItem(IS_ADMIN_KEY) === 'true');

  isAuthenticated = () => this.tokenSignal() !== null;
  isAdmin = () => this.isAdminSignal();
  get token(): string | null {
    return this.tokenSignal();
  }

  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login/`, { username, password })
      .pipe(
        tap((res) => {
          localStorage.setItem(TOKEN_KEY, res.token);
          localStorage.setItem(IS_ADMIN_KEY, String(res.is_staff));
          this.tokenSignal.set(res.token);
          this.isAdminSignal.set(res.is_staff);
        }),
      );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(IS_ADMIN_KEY);
    this.tokenSignal.set(null);
    this.isAdminSignal.set(false);
  }
}
