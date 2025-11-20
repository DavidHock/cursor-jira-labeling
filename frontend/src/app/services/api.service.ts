import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { IssueResponse } from '../models/issue.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // Use relative URL - nginx will proxy /api to backend
  private apiUrl = '/api';
  
  // HTTP options with credentials
  private httpOptions = {
    withCredentials: true,
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  constructor(private http: HttpClient) {}

  login(email: string, apiToken: string, jiraInstance?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, {
      email,
      api_token: apiToken,
      jira_instance: jiraInstance
    }, this.httpOptions);
  }

  logout(): Observable<any> {
    return this.http.post(`${this.apiUrl}/logout`, {}, this.httpOptions);
  }

  getSession(): Observable<any> {
    return this.http.get(`${this.apiUrl}/session`, this.httpOptions);
  }

  searchIssue(filterId: string): Observable<{ issue_key: string; total_issues: number }> {
    return this.http.post<{ issue_key: string; total_issues: number }>(
      `${this.apiUrl}/search_issue`,
      { filter_id: filterId },
      this.httpOptions
    );
  }

  fetchIssue(issueKey: string, totalIssues: number): Observable<IssueResponse> {
    return this.http.get<IssueResponse>(
      `${this.apiUrl}/fetch_issue?issue_key=${issueKey}&total_issues=${totalIssues}`,
      this.httpOptions
    );
  }

  updateIssue(issueKey: string, researchProject: string, chargeable: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/update_issue`, {
      issue_key: issueKey,
      research_project: researchProject,
      chargeable
    }, this.httpOptions);
  }
}

