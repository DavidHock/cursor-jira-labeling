import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-container">
      <div class="login-card">
        <h1>Jira Labeling Tool</h1>
        <p class="subtitle">Sign in to continue</p>
        
        <form (ngSubmit)="onSubmit()" #loginForm="ngForm">
          <div class="form-group">
            <label for="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              [(ngModel)]="email"
              required
              placeholder="your.email@example.com"
            />
          </div>
          
          <div class="form-group">
            <label for="apiToken">API Token</label>
            <input
              type="password"
              id="apiToken"
              name="apiToken"
              [(ngModel)]="apiToken"
              required
              placeholder="Enter your Jira API token"
            />
          </div>
          
          <div class="form-group">
            <label for="jiraInstance">Jira Instance (optional)</label>
            <input
              type="text"
              id="jiraInstance"
              name="jiraInstance"
              [(ngModel)]="jiraInstance"
              placeholder="infosim.atlassian.net"
            />
          </div>
          
          <div *ngIf="error" class="error">{{ error }}</div>
          
          <button
            type="submit"
            class="btn btn-primary"
            [disabled]="loading || !loginForm.valid"
          >
            <span *ngIf="!loading">Sign In</span>
            <span *ngIf="loading">Signing in...</span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }
    
    .login-card {
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
      padding: 40px;
      width: 100%;
      max-width: 400px;
    }
    
    h1 {
      text-align: center;
      color: #667eea;
      margin-bottom: 8px;
      font-size: 32px;
    }
    
    .subtitle {
      text-align: center;
      color: #666;
      margin-bottom: 32px;
    }
  `]
})
export class LoginComponent {
  email = '';
  apiToken = '';
  jiraInstance = 'infosim.atlassian.net';
  loading = false;
  error = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  onSubmit() {
    if (!this.email || !this.apiToken) {
      this.error = 'Please fill in all required fields';
      return;
    }

    this.loading = true;
    this.error = '';

    this.apiService.login(this.email, this.apiToken, this.jiraInstance).subscribe({
      next: () => {
        this.router.navigate(['/search']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || 'Login failed. Please check your credentials.';
      }
    });
  }
}

