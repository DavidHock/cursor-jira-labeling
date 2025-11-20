import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { IssueResponse } from '../models/issue.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // Use relative URL in production (nginx proxy), absolute in development
  private apiUrl = window.location.hostname === 'localhost' 
    ? 'http://localhost:8082/api' 
    : '/api';

  constructor(private http: HttpClient) {}

  login(email: string, apiToken: string, jiraInstance?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, {
      email,
      api_token: apiToken,
      jira_instance: jiraInstance
    });
  }

  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/logout`, {});
  }

  getSession(): Observable<any> {
    return this.http.get(`${this.apiUrl}/session`);
  }

  searchIssue(filterId: string): Observable<{ issue_key: string; total_issues: number }> {
    return this.http.post<{ issue_key: string; total_issues: number }>(
      `${this.apiUrl}/search_issue`,
      { filter_id: filterId }
    );
  }

  fetchIssue(issueKey: string, totalIssues: number): Observable<IssueResponse> {
    return this.http.get<IssueResponse>(
      `${this.apiUrl}/fetch_issue?issue_key=${issueKey}&total_issues=${totalIssues}`
    );
  }

  updateIssue(issueKey: string, researchProject: string, chargeable: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/update_issue`, {
      issue_key: issueKey,
      research_project: researchProject,
      chargeable
    });
  }
}

