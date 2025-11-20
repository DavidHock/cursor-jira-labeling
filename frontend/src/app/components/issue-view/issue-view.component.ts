import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { IssueResponse, Issue } from '../../models/issue.model';

@Component({
  selector: 'app-issue-view',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <div class="header">
        <h1>Jira Issue Labeling</h1>
        <div class="progress-info">
          <span>Issue {{ currentIssueIndex }} of {{ totalIssues }}</span>
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
            <p>{{ currentIssue?.description || 'No description available' }}</p>
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
                [class.has-hours]="hasHoursForProject(project)"
                [class.no-hours]="!hasHoursForProject(project) && project !== 'NOT ASSIGNABLE' && project !== 'PARTIALLY ASSIGNABLE'"
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

        <div class="stats-container">
          <div class="card stats-card">
            <h3>Time Distribution (Last 14 Days)</h3>
            <div *ngIf="issueData.pie_chart" class="chart-container">
              <img [src]="'data:image/png;base64,' + issueData.pie_chart" alt="Time Distribution Chart" />
            </div>
            <div *ngIf="!issueData.pie_chart && issueData.sorted_projects.length === 0" class="no-data">
              <p>No worklog data available for the last 14 days.</p>
            </div>
          </div>

          <div class="card worklog-card" *ngIf="issueData.worklog_issues.length > 0">
            <h3>Recent Worklog Issues</h3>
            <div class="worklog-list">
              <div *ngFor="let worklog of issueData.worklog_issues" class="worklog-item">
                <div class="worklog-key">{{ worklog.key }}</div>
                <div class="worklog-name">{{ worklog.name }}</div>
                <div class="worklog-meta">
                  <span class="worklog-project">{{ worklog.research_project }}</span>
                  <span class="worklog-hours">{{ worklog.time_spent_hours }}h</span>
                </div>
              </div>
            </div>
          </div>
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
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
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

    @media (max-width: 968px) {
      .issue-container {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class IssueViewComponent implements OnInit {
  issueData: IssueResponse | null = null;
  currentIssue: Issue | null = null;
  currentIssueIndex = 1;
  totalIssues = 1;
  loading = true;
  error = '';
  updating = false;
  updateError = '';
  updateSuccess = '';
  
  selectedProject = '';
  
  // Fixed chargeable ID - always sent in background, not user-changeable
  private readonly CHARGEABLE_ID = '10396';
  
  allProjects = [
    '6G-NETFAB',
    'GREENFIELD',
    'INTENSE',
    'N-DOLLI',
    'QuINSiDa',
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
    this.route.params.subscribe(params => {
      const issueKey = params['issueKey'];
      this.route.queryParams.subscribe(queryParams => {
        this.totalIssues = +queryParams['total_issues'] || 1;
        if (issueKey) {
          this.loadIssue(issueKey);
        }
      });
    });
  }

  loadIssue(issueKey: string) {
    this.loading = true;
    this.error = '';
    this.updateError = '';
    this.updateSuccess = '';

    this.apiService.fetchIssue(issueKey, this.totalIssues).subscribe({
      next: (data) => {
        this.issueData = data;
        this.currentIssue = data.issues[0];
        // Calculate current issue index correctly
        // When we navigate to next issue, totalIssues decreases
        this.currentIssueIndex = this.totalIssues;
        this.selectedProject = this.currentIssue?.research_project || '';
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || 'Failed to load issue';
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

    this.updating = true;
    this.updateError = '';
    this.updateSuccess = '';

    // Chargeable ID is always set to fixed value in background
    this.apiService.updateIssue(
      this.currentIssue.key,
      selectedProject,
      this.CHARGEABLE_ID
    ).subscribe({
      next: (response) => {
        this.updating = false;
        this.updateSuccess = response.message || 'Issue updated successfully';
        
        if (response.next_issue) {
          setTimeout(() => {
            this.router.navigate(['/issue', response.next_issue], {
              queryParams: { total_issues: response.total_issues }
            });
          }, 1000);
        } else {
          this.updateSuccess += ' - No more issues found';
        }
      },
      error: (err) => {
        this.updating = false;
        this.updateError = err.error?.message || 'Failed to update issue';
      }
    });
  }
}

