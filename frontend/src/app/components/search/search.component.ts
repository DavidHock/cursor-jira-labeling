import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <div class="card">
        <h1>Search Jira Issues</h1>
        <p class="subtitle">Enter a filter ID to find issues</p>
        
        <form (ngSubmit)="onSearch()" #searchForm="ngForm">
          <div class="form-group">
            <label for="filterId">Filter ID</label>
            <input
              type="text"
              id="filterId"
              name="filterId"
              [(ngModel)]="filterId"
              required
              placeholder="e.g., 10456"
            />
          </div>
          
          <div *ngIf="error" class="error">{{ error }}</div>
          
          <button
            type="submit"
            class="btn btn-primary"
            [disabled]="loading || !searchForm.valid"
          >
            <span *ngIf="!loading">Search</span>
            <span *ngIf="loading">Searching...</span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .card {
      max-width: 500px;
      margin: 40px auto;
    }
    
    h1 {
      color: #667eea;
      margin-bottom: 8px;
    }
    
    .subtitle {
      color: #666;
      margin-bottom: 24px;
    }
  `]
})
export class SearchComponent {
  filterId = '10456';
  loading = false;
  error = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  onSearch() {
    if (!this.filterId) {
      this.error = 'Please enter a filter ID';
      return;
    }

    this.loading = true;
    this.error = '';

    this.apiService.searchIssue(this.filterId).subscribe({
      next: (response) => {
        console.log('[FRONTEND] search - Received response:', response);
        console.log('[FRONTEND] search - response.total_issues:', response.total_issues);
        console.log('[FRONTEND] search - Navigating with total_issues:', response.total_issues);
        this.router.navigate(['/issue', response.issue_key], {
          queryParams: { total_issues: response.total_issues }
        });
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || 'Failed to search issues. Please try again.';
      }
    });
  }
}

