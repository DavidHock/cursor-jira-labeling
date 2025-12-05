export interface Issue {
  key: string;
  name: string;
  description: string;
  assignee_name: string;
  assignee_id?: string;
  timespent: number;
  research_project: string;
  link_type: string;
}

export interface WorklogIssue {
  key: string;
  name: string;
  research_project: string;
  time_spent_hours: number;
}

export interface ProjectTime {
  project: string;
  hours: number;
}

export interface IssueResponse {
  issues: Issue[];
  total_issues: number;
  assignee_name: string;
  task_time_spent: number;
  worklog_issues: WorklogIssue[];
  sorted_projects: ProjectTime[];
  projects_without_time: string[];
  pie_chart?: string; // Deprecated, use treemap_data instead
  treemap_data?: any;
}

