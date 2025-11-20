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

          <form (ngSubmit)="onUpdate()" #updateForm="ngForm">
            <div class="form-group">
              <label for="researchProject">Research Project *</label>
              <select
                id="researchProject"
                name="researchProject"
                [(ngModel)]="selectedProject"
                required
              >
                <option value="">Select a project</option>
                <option *ngFor="let project of allProjects" [value]="project">
                  {{ project }}
                </option>
              </select>
            </div>

            <div *ngIf="updateError" class="error">{{ updateError }}</div>
            <div *ngIf="updateSuccess" class="success">{{ updateSuccess }}</div>

            <div class="button-group">
              <button
                type="submit"
                class="btn btn-primary"
                [disabled]="updating || !updateForm.valid"
              >
                <span *ngIf="!updating">Update & Next</span>
                <span *ngIf="updating">Updating...</span>
              </button>
            </div>
          </form>
        </div>

        <div class="stats-container">
          <div class="card stats-card">
            <h3>Recent Worklogs (Last 14 Days)</h3>
            <div *ngIf="issueData.sorted_projects.length > 0" class="projects-list">
              <div *ngFor="let project of issueData.sorted_projects" class="project-item">
                <span class="project-name">{{ project.project }}</span>
                <span class="project-hours">{{ project.hours }}h</span>
              </div>
            </div>
            <div *ngIf="issueData.projects_without_time.length > 0" class="projects-without-time">
              <h4>Projects without time:</h4>
              <div class="project-tags">
                <span *ngFor="let project of issueData.projects_without_time" class="tag">
                  {{ project }}
                </span>
              </div>
            </div>
            <div *ngIf="issueData.pie_chart" class="chart-container">
              <img [src]="'data:image/png;base64,' + issueData.pie_chart" alt="Time Distribution Chart" />
            </div>
          </div>

          <div class="card worklog-card" *ngIf="issueData.worklog_issues.length > 0">
            <h3>Worklog Issues</h3>
            <div class="worklog-list">
              <div *ngFor="let worklog of issueData.worklog_issues" class="worklog-item">
                <div class="worklog-key">{{ worklog.key }}</div>
                <div class="worklog-name">{{ worklog.name }}</div>
                <div class="worklog-meta">
                  <span>{{ worklog.research_project }}</span>
                  <span>{{ worklog.time_spent_hours }}h</span>
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

      .button-group {
        margin-top: 24px;
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
        this.currentIssueIndex = this.totalIssues - (this.totalIssues - 1);
        this.selectedProject = this.currentIssue?.research_project || '';
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.message || 'Failed to load issue';
      }
    });
  }

  onUpdate() {
    if (!this.currentIssue || !this.selectedProject) {
      this.updateError = 'Please select a research project';
      return;
    }

    this.updating = true;
    this.updateError = '';
    this.updateSuccess = '';

    // Chargeable ID is always set to fixed value in background
    this.apiService.updateIssue(
      this.currentIssue.key,
      this.selectedProject,
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

