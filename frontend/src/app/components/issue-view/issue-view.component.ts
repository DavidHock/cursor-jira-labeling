import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { IssueResponse, Issue } from '../../models/issue.model';
import { combineLatest, EMPTY } from 'rxjs';
import { takeUntil, switchMap, map } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-issue-view',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <div class="header">
        <h1>Jira Issue Labeling</h1>
        <div class="progress-info">
          <span>{{ formatTotalIssues(totalIssues) }}</span>
        </div>
      </div>

      <div *ngIf="loading" class="loading">Loading issue...</div>
      <div *ngIf="error" class="error">{{ error }}</div>

      <div *ngIf="issueData && !loading" class="issue-container">
        <div class="card issue-card">
          <h2>{{ currentIssue?.name }}</h2>
          <div class="issue-meta">
            <span class="issue-key">{{ currentIssue?.key }}</span>
            <span class="assignee">Assignee: {{ issueData.assignee_name }}</span>
            <span class="time-spent">Time Spent: {{ issueData.task_time_spent }}h</span>
          </div>
          
          <div class="issue-description">
            <h3>Description</h3>
            <p [innerHTML]="getHighlightedDescription()"></p>
          </div>

          <div class="related-issues" *ngIf="issueData.issues.length > 1">
            <h3>Related Issues</h3>
            <div class="related-issues-list">
              <div *ngFor="let issue of issueData.issues" class="related-issue-item" [class.main-issue]="issue.link_type === 'Self'">
                <span class="related-issue-key">{{ issue.key }}</span>
                <span class="related-issue-link-type">{{ issue.link_type }}</span>
                <span class="related-issue-name">{{ issue.name }}</span>
                <span class="related-issue-project">{{ issue.research_project || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>Research Project *</label>
            <div class="project-buttons">
              <button
                *ngFor="let project of allProjects"
                type="button"
                class="project-btn"
                [class.selected]="selectedProject === project"
                [class.not-assignable]="project === 'NOT ASSIGNABLE'"
                [class.partially-assignable]="project === 'PARTIALLY ASSIGNABLE'"
                [class.has-hours]="hasHoursForProject(project) || isProjectHighlighted(project)"
                [class.no-hours]="!hasHoursForProject(project) && !isProjectHighlighted(project) && project !== 'NOT ASSIGNABLE' && project !== 'PARTIALLY ASSIGNABLE'"
                [class.keyword-highlight]="isProjectHighlighted(project)"
                [disabled]="updating"
                (click)="onProjectSelect(project)"
              >
                <span *ngIf="!updating || selectedProject !== project">{{ project }}</span>
                <span *ngIf="updating && selectedProject === project">Updating...</span>
              </button>
            </div>
          </div>

          <div *ngIf="updateError" class="error">{{ updateError }}</div>
          <div *ngIf="updateSuccess" class="success">{{ updateSuccess }}</div>
        </div>

      </div>
    </div>
  `,
  styles: [`
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      color: white;
    }

    h1 {
      margin: 0;
      font-size: 28px;
    }

    .progress-info {
      background: rgba(255, 255, 255, 0.2);
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 600;
    }

    .issue-container {
      display: block;
      width: 100%;
    }

    .issue-card {
      h2 {
        color: #667eea;
        margin-bottom: 16px;
      }

      .issue-meta {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        flex-wrap: wrap;

        span {
          padding: 6px 12px;
          background: #f5f5f5;
          border-radius: 6px;
          font-size: 14px;
        }

        .issue-key {
          background: #667eea;
          color: white;
          font-weight: 600;
        }
      }

      .issue-description {
        margin-bottom: 24px;
        padding: 16px;
        background: #f9f9f9;
        border-radius: 8px;

        h3 {
          margin-bottom: 12px;
          color: #555;
        }

        p {
          line-height: 1.6;
          color: #666;
        }

        ::ng-deep .keyword-highlight-text {
          color: #667eea;
          font-weight: 700;
          background: rgba(102, 126, 234, 0.1);
          padding: 2px 4px;
          border-radius: 3px;
        }
      }

      .related-issues {
        margin-bottom: 24px;
        padding: 16px;
        background: #f0f4ff;
        border-radius: 8px;
        border-left: 4px solid #667eea;

        h3 {
          margin-bottom: 12px;
          color: #667eea;
          font-size: 16px;
        }

        .related-issues-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .related-issue-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          font-size: 14px;

          &.main-issue {
            background: #e3f2fd;
            font-weight: 600;
          }

          .related-issue-key {
            font-weight: 600;
            color: #667eea;
            min-width: 80px;
          }

          .related-issue-link-type {
            padding: 4px 8px;
            background: #f5f5f5;
            border-radius: 4px;
            font-size: 12px;
            color: #666;
            min-width: 100px;
          }

          .related-issue-name {
            flex: 1;
            color: #333;
          }

          .related-issue-project {
            padding: 4px 8px;
            background: #667eea;
            color: white;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            min-width: 100px;
            text-align: center;
          }
        }
      }

      .button-group {
        margin-top: 24px;
      }

      .project-buttons {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 12px;
        margin-top: 12px;
      }

      .project-btn {
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        background: #f5f5f5;
        color: #333;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        &.keyword-highlight {
          border-color: #667eea;
          background: #e3f2fd;
          box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
        }

        &.selected {
          border-width: 3px;
          box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
        }

        &.not-assignable {
          background: #fee;
          border-color: #f44;
          color: #c33;

          &.selected {
            background: #fcc;
            border-color: #f00;
          }
        }

        &.partially-assignable {
          background: #ffd;
          border-color: #ff0;
          color: #990;

          &.selected {
            background: #ffc;
            border-color: #ff0;
          }
        }

        &.has-hours {
          background: #e3f2fd;
          border-color: #667eea;
          color: #1976d2;

          &.selected {
            background: #bbdefb;
            border-color: #2196f3;
          }
        }

        &.no-hours {
          background: #f5f5f5;
          border-color: #bdbdbd;
          color: #757575;

          &.selected {
            background: #e0e0e0;
            border-color: #9e9e9e;
          }
        }
      }
    }

    .stats-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .stats-card, .worklog-card {
      h3 {
        margin-bottom: 16px;
        color: #667eea;
      }

      .projects-list {
        margin-bottom: 20px;
      }

      .project-item {
        display: flex;
        justify-content: space-between;
        padding: 12px;
        background: #f9f9f9;
        border-radius: 6px;
        margin-bottom: 8px;

        .project-name {
          font-weight: 600;
        }

        .project-hours {
          color: #667eea;
        }
      }

      .projects-without-time {
        margin-top: 20px;

        h4 {
          margin-bottom: 12px;
          color: #666;
        }

        .project-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;

          .tag {
            padding: 6px 12px;
            background: #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
          }
        }
      }

      .chart-container {
        margin-top: 20px;
        text-align: center;

        img {
          max-width: 100%;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      }

      .treemap-container {
        margin-top: 20px;

        .treemap-controls {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;

          .btn-back {
            padding: 6px 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;

            &:hover {
              background: #5568d3;
            }
          }

          .current-view {
            color: #667eea;
            font-weight: 600;
          }
        }

        .treemap {
          width: 100%;
          min-height: 300px;
          background: #f9f9f9;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

          .treemap-items {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            width: 100%;

            .treemap-item {
              min-height: 80px;
              border-radius: 6px;
              padding: 12px;
              display: flex;
              align-items: center;
              justify-content: center;
              transition: transform 0.2s, box-shadow 0.2s;
              cursor: pointer;
              position: relative;
              overflow: hidden;

              &.project-item {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: 2px solid #5568d3;

                &:hover {
                  transform: translateY(-2px);
                  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }
              }

              &.issue-item {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                border: 2px solid #e91e63;
                min-height: 60px;

                &:hover {
                  transform: translateY(-2px);
                  box-shadow: 0 4px 12px rgba(233, 30, 99, 0.4);
                }
              }

              .treemap-label {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 4px;
                text-align: center;
                width: 100%;

                .treemap-name {
                  font-weight: 600;
                  font-size: 14px;
                  white-space: nowrap;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  max-width: 100%;
                }

                .treemap-value {
                  font-size: 16px;
                  font-weight: 700;
                  opacity: 0.95;
                }

                .treemap-count {
                  font-size: 12px;
                  opacity: 0.85;
                  margin-top: 2px;
                }
              }
            }
          }
        }
      }

      .no-data {
        text-align: center;
        padding: 40px 20px;
        color: #999;

        p {
          margin: 0;
          font-style: italic;
        }
      }
    }

    .worklog-list {
      .worklog-item {
        padding: 12px;
        background: #f9f9f9;
        border-radius: 6px;
        margin-bottom: 12px;

        .worklog-key {
          font-weight: 600;
          color: #667eea;
          margin-bottom: 4px;
        }

        .worklog-name {
          margin-bottom: 8px;
          color: #555;
        }

        .worklog-meta {
          display: flex;
          justify-content: space-between;
          font-size: 14px;
          color: #666;
        }
      }
    }

  `]
})
export class IssueViewComponent implements OnInit, OnDestroy {
  issueData: IssueResponse | null = null;
  currentIssue: Issue | null = null;
  totalIssues = 1;
  loading = true;
  error = '';
  updating = false;
  updateError = '';
  updateSuccess = '';
  
  selectedProject = '';
  
  // Fixed chargeable ID - always sent in background, not user-changeable
  private readonly CHARGEABLE_ID = '10396';
  
  // For cleanup of subscriptions
  private destroy$ = new Subject<void>();
  
  // Keyword mapping for auto-detection
  private readonly keywordMapping: { [key: string]: string[] } = {
    '6G-NETFAB': ['NETCONF', 'YANG'],
    'GREENFIELD': ['REPORT'],
    'INTENSE': ['CONFIG', 'JOBS', 'NCCM'],
    'N-DOLLI': ['DISCOVERY'],
    'KIOps6G': ['USER', 'RIGHTS'],
    'SASPIT': ['TELEMETRY', 'MODULE CONTROLER'],
    'SUSTAINET': ['DASHBOARD', 'MEASUREMENT', 'AI'],
    'SHINKA': ['RESOURCE POOL']
  };
  
  allProjects = [
    '6G-NETFAB',
    'GREENFIELD',
    'INTENSE',
    'N-DOLLI',
    'KIOps6G',
    'SASPIT',
    'SUSTAINET',
    'SHINKA',
    'PARTIALLY ASSIGNABLE',
    'NOT ASSIGNABLE'
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    // Use combineLatest to properly handle both params and queryParams
    // Use switchMap to automatically cancel previous requests when navigating to a new issue
    // This avoids nested subscriptions, memory leaks, and race conditions
    combineLatest([
      this.route.params,
      this.route.queryParams
    ]).pipe(
      takeUntil(this.destroy$),
      switchMap(([params, queryParams]) => {
        const issueKey = params['issueKey'];
        const totalIssuesParam = queryParams['total_issues'];
        
        console.log('[FRONTEND] ngOnInit - params:', params, 'queryParams:', queryParams);
        console.log('[FRONTEND] ngOnInit - total_issues param:', totalIssuesParam);
        
        // Use nullish coalescing to handle 0 correctly (0 is a valid value)
        this.totalIssues = totalIssuesParam !== undefined && totalIssuesParam !== null 
          ? +totalIssuesParam 
          : 1;
        console.log('[FRONTEND] ngOnInit - totalIssues set to:', this.totalIssues);
        
        // Reset state when loading a new issue
        this.loading = true;
        this.error = '';
        this.updateError = '';
        this.updateSuccess = '';
        this.updating = false;
        this.selectedProject = '';
        
        if (issueKey) {
          // Use switchMap to cancel previous request if a new one comes in
          return this.apiService.fetchIssue(issueKey, this.totalIssues).pipe(
            map(data => ({ data, issueKey }))
          );
        } else {
          // Return empty observable if no issue key
          return EMPTY;
        }
      })
    ).subscribe({
      next: (result) => {
        if (result && result.data && result.issueKey) {
          console.log('[FRONTEND] ngOnInit - Received data:', result.data);
          console.log('[FRONTEND] ngOnInit - data.total_issues:', result.data.total_issues);
          this.issueData = result.data;
          this.currentIssue = result.data.issues[0];
          this.selectedProject = this.currentIssue?.research_project || '';
          // Update totalIssues from API response if available
          const oldTotal = this.totalIssues;
          if (result.data.total_issues !== undefined && result.data.total_issues !== null) {
            this.totalIssues = result.data.total_issues;
            console.log('[FRONTEND] ngOnInit - Updated totalIssues from', oldTotal, 'to', this.totalIssues);
          } else {
            console.log('[FRONTEND] ngOnInit - Keeping totalIssues as', this.totalIssues, '(data.total_issues was:', result.data.total_issues, ')');
          }
          this.loading = false;
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || 'Failed to load issue';
        console.error('[FRONTEND] ngOnInit - Error:', err);
      }
    });
  }

  ngOnDestroy() {
    // Clean up all subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadIssue(issueKey: string) {
    // Reset all state when loading a new issue
    this.loading = true;
    this.error = '';
    this.updateError = '';
    this.updateSuccess = '';
    this.updating = false; // Reset updating flag
    this.selectedProject = ''; // Reset selected project

    console.log('[FRONTEND] loadIssue - Calling fetchIssue with issueKey:', issueKey, 'totalIssues:', this.totalIssues);
    this.apiService.fetchIssue(issueKey, this.totalIssues)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          console.log('[FRONTEND] loadIssue - Received data:', data);
          console.log('[FRONTEND] loadIssue - data.total_issues:', data.total_issues);
          this.issueData = data;
          this.currentIssue = data.issues[0];
          this.selectedProject = this.currentIssue?.research_project || '';
          // Update totalIssues from API response if available
          const oldTotal = this.totalIssues;
          if (data.total_issues !== undefined && data.total_issues !== null) {
            this.totalIssues = data.total_issues;
            console.log('[FRONTEND] loadIssue - Updated totalIssues from', oldTotal, 'to', this.totalIssues);
          } else {
            console.log('[FRONTEND] loadIssue - Keeping totalIssues as', this.totalIssues, '(data.total_issues was:', data.total_issues, ')');
          }
          this.loading = false;
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.message || 'Failed to load issue';
          console.error('[FRONTEND] loadIssue - Error:', err);
        }
      });
  }

  hasHoursForProject(project: string): boolean {
    if (!this.issueData) {
      return false;
    }
    
    // Check if project has hours in worklogs
    if (this.issueData.sorted_projects) {
      if (this.issueData.sorted_projects.some(p => p.project === project)) {
        return true;
      }
    }
    
    // Check if any related issue has this project assigned
    if (this.issueData.issues) {
      return this.issueData.issues.some(issue => issue.research_project === project);
    }
    
    return false;
  }

  isProjectHighlighted(project: string): boolean {
    if (!this.currentIssue?.description) {
      return false;
    }
    
    const description = this.currentIssue.description.toUpperCase();
    const keywords = this.keywordMapping[project];
    
    if (!keywords) {
      return false;
    }
    
    return keywords.some(keyword => {
      const upperKeyword = keyword.toUpperCase();
      // Check for whole word matches (case insensitive)
      const regex = new RegExp(`\\b${upperKeyword.replace(/\s+/g, '\\s+')}\\b`, 'i');
      return regex.test(description);
    });
  }

  getHighlightedDescription(): string {
    if (!this.currentIssue?.description) {
      return 'No description available';
    }
    
    let description = this.currentIssue.description;
    
    // Sort keywords by length (longest first) to match longer phrases first
    const sortedKeywords = Object.values(this.keywordMapping)
      .flat()
      .sort((a, b) => b.length - a.length);
    
    // Use a marker to track already highlighted text
    const MARKER = '___HIGHLIGHTED___';
    const markers: string[] = [];
    let markerIndex = 0;
    
    // First pass: mark all matches
    sortedKeywords.forEach(keyword => {
      // Escape special regex characters
      const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      // Replace spaces with \s+ to match any whitespace
      const pattern = escapedKeyword.replace(/\s+/g, '\\s+');
      const regex = new RegExp(`\\b(${pattern})\\b`, 'gi');
      
      description = description.replace(regex, (match) => {
        const marker = `${MARKER}${markerIndex}${MARKER}`;
        markers[markerIndex] = match;
        markerIndex++;
        return marker;
      });
    });
    
    // Second pass: replace markers with highlighted HTML
    markers.forEach((originalText, index) => {
      const marker = `${MARKER}${index}${MARKER}`;
      description = description.replace(marker, `<strong class="keyword-highlight-text">${originalText}</strong>`);
    });
    
    return description;
  }

  onProjectSelect(project: string) {
    if (this.updating) {
      return; // Prevent multiple clicks while updating
    }
    
    this.selectedProject = project;
    this.updateError = '';
    this.updateSuccess = '';
    
    // Immediately submit the update
    this.onUpdate(project);
  }

  onUpdate(project?: string) {
    const selectedProject = project || this.selectedProject;
    
    if (!this.currentIssue || !selectedProject) {
      this.updateError = 'Please select a research project';
      return;
    }

    // Prevent multiple simultaneous updates
    if (this.updating) {
      console.log('[FRONTEND] onUpdate - Update already in progress, ignoring');
      return;
    }

    this.updating = true;
    this.updateError = '';
    this.updateSuccess = '';

    // Chargeable ID is always set to fixed value in background
    this.apiService.updateIssue(
      this.currentIssue.key,
      selectedProject,
      this.CHARGEABLE_ID
    )
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          console.log('[FRONTEND] onUpdate - Update response:', response);
          console.log('[FRONTEND] onUpdate - response.total_issues:', response.total_issues);
          
          if (response.next_issue) {
            console.log('[FRONTEND] onUpdate - Navigating to next issue with total_issues:', response.total_issues);
            // Reset state before navigation
            this.updating = false;
            this.updateError = '';
            this.updateSuccess = '';
            
            // Navigate immediately to next issue
            this.router.navigate(['/issue', response.next_issue], {
              queryParams: { total_issues: response.total_issues }
            }).then(() => {
              console.log('[FRONTEND] onUpdate - Navigation completed');
            }).catch((err) => {
              console.error('[FRONTEND] onUpdate - Navigation error:', err);
              this.updateError = 'Failed to navigate to next issue';
              this.updating = false;
            });
          } else {
            this.updating = false;
            this.updateSuccess = response.message || 'Issue updated successfully - No more issues found';
          }
        },
        error: (err) => {
          this.updating = false;
          this.updateError = err.error?.message || 'Failed to update issue';
          console.error('[FRONTEND] onUpdate - Error:', err);
        }
      });
  }

  formatTotalIssues(totalIssues: any): string {
    if (typeof totalIssues === 'string' && totalIssues.endsWith('+')) {
      return `${totalIssues} issues`;
    }
    const num = typeof totalIssues === 'string' ? parseInt(totalIssues, 10) : totalIssues;
    if (isNaN(num)) {
      return '0 issues';
    }
    return `${num} ${num === 1 ? 'issue' : 'issues'}`;
  }
}

