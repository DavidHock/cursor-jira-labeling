from flask import Flask, render_template, request, redirect, url_for, session
import logging
import json
import os
from dotenv import load_dotenv
from utils.issue_lookup import get_issue_hierarchy, get_recent_worklogs, search_issue_by_filter, generate_pie_chart
import requests
from datetime import timedelta

log_file = "/shared/app.log"
logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a", format="%(asctime)s - %(message)s")

session_file = "/shared/session_data.json"

def save_session():
    with open(session_file, "w") as f:
        json.dump(dict(session), f)

def load_session():
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            session.update(json.load(f))

app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)  # 1 Stunde gültig

@app.route('/')
def home():
    load_session()
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def login():
    session["jira_email"] = request.form["email"]
    session["jira_api_token"] = request.form["api_token"]
    session["jira_instance"] = "infosim.atlassian.net"
    save_session()

    logging.debug("🔹 Session nach Login gesetzt:", session)  # Debug-Ausgabe
    
    return redirect(url_for("search_issue"))

@app.route('/search_issue', methods=['GET', 'POST'])
def search_issue():
    if 'jira_email' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        filter_id = request.form.get('filter_id', '10456')
        session['filter_id'] = filter_id
        issue_key,total_issues = search_issue_by_filter(filter_id, session['jira_email'], session['jira_api_token'], session['jira_instance'])
        logging.debug(f"Total issues: {total_issues}")
        if issue_key:
            return redirect(url_for('fetch_issue', issue_key=issue_key, total_issues=total_issues))
        else:
            return "No issues found for the given filter.", 404

    return render_template('search.html', filter_id=session.get('filter_id', '10456'))

@app.route('/fetch_issue', methods=['GET'])
def fetch_issue():
    if 'jira_email' not in session:
        return redirect(url_for('home'))

    issue_key = request.args.get('issue_key')

    if not issue_key:
        return redirect(url_for('search_issue'))

    logging.debug(f"Fetching issue: {issue_key}")

    issues_info = get_issue_hierarchy(issue_key, session['jira_email'], session['jira_api_token'], session['jira_instance'])

    if not issues_info:
        return "Issue not found or unauthorized access.", 404

    assignee_id = issues_info[0].get('assignee_id')  # FIXED
    assignee_name = issues_info[0].get('assignee_name', 'Unassigned')
    task_time_spent = issues_info[0].get('timespent', 0)

    logging.debug(f"Assignee ID: {assignee_id}, Assignee Name: {assignee_name}")

    worklog_issues, worklog_data = get_recent_worklogs(
        assignee_id, session['jira_email'], session['jira_api_token'], session['jira_instance']
    ) if assignee_id else ([], {})

    sorted_projects = sorted(worklog_data.items(), key=lambda x: x[1], reverse=True)
    
    pie_chart = generate_pie_chart(dict(sorted_projects)) if sorted_projects else None
    
    total_issues = request.args.get("total_issues", 1)  # Get total issues from search_issue()

    return render_template(
        'issues.html',
        issues=issues_info,
        total_issues=total_issues,  # ✅ Pass total issue count
        assignee_name=assignee_name,
        task_time_spent=task_time_spent,
        worklog_issues=worklog_issues,
        sorted_projects=sorted_projects,
        projects_without_time=[
            p for p in ["6G-NETFAB", "GREENFIELD", "INTENSE", "N-DOLLI", "QuINSiDa", "SASPIT", "SUSTAINET", "SHINKA", "PARTIALLY ASSIGNABLE", "NOT ASSIGNABLE"]
            if p not in worklog_data
        ],
        pie_chart=pie_chart  # ✅ Make sure pie chart is passed
    )

@app.route('/update_issue', methods=['POST'])
def update_issue():
    data = request.get_json()
    issue_key = data.get('issue_key')
    research_project = data.get('research_project')
    chargeable = data.get('chargeable')
    
    if not issue_key or not research_project:
        return {"message": "Missing required fields."}, 400

    logging.debug(f"Updating Issue {issue_key}: Research Project -> {research_project}, Chargeable -> {chargeable}")

    update_data = {
        "fields": {
            "customfield_10097": {"value": research_project},
            "customfield_10384": {"id": chargeable}
        }
    }

    url = f"https://{session['jira_instance']}/rest/api/3/issue/{issue_key}"
    auth = (session['jira_email'], session['jira_api_token'])
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = requests.put(url, json=update_data, auth=auth, headers=headers)

    if response.status_code == 204:
        next_issue_key,total_issues = search_issue_by_filter(session.get("filter_id", "10456"), session["jira_email"], session["jira_api_token"], session["jira_instance"])
        
                # Add current user as watcher
        watcher_url = f"https://{session['jira_instance']}/rest/api/3/issue/{issue_key}/watchers"
        watcher_response = requests.post(
            watcher_url,
            data=json.dumps(session['jira_email']),  # email als JSON-String
            auth=auth,
            headers={"Content-Type": "application/json"}
        )

        if watcher_response.status_code not in [204, 400]:  # 400 if user is already a watcher
            logging.warning(f"Failed to add watcher: {watcher_response.status_code} - {watcher_response.text}")

        if next_issue_key:
            with open("/shared/updated_issues.log", "a") as f:
                f.write(f"Updated Issue: {issue_key}\n")
            return {"message": "Issue updated successfully.", "next_issue": next_issue_key,"total_issues": total_issues}, 200
        else:
            return {"message": "Issue updated, but no more issues found.", "next_issue": None}, 200

    # 🔴 HIER NEU: Immer etwas zurückgeben, auch bei Fehlern!
    else:
        logging.error(f"Failed to update issue {issue_key}: {response.status_code} - {response.text}")
        return {
            "message": "Failed to update issue.",
            "jira_response": response.text
        }, response.status_code

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=8081,
        ssl_context=("localhost.pem", "localhost-key.pem"),
        debug=True
    )
