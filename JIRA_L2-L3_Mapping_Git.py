# This script fetches parent tickets from Jira, identifies those linked to IOT projects, 
# and updates a Confluence page with the details in a structured table format with serial number.

import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retry = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
# ==============================
# CONFIGURATION
# ==============================

JIRA_BASE_URL = "https://abc.atlassian.net"
JIRA_EMAIL = "abc@xyz.com"
JIRA_API_TOKEN = "API Token"

CONFLUENCE_BASE_URL = "https://abc.atlassian.net/wiki"
CONFLUENCE_EMAIL = "abc@xyz.com"
CONFLUENCE_API_TOKEN = "API Token"
CONFLUENCE_PAGE_ID = "Page ID"

INC2_PROJECT = "INC2"
MS_PROJECT = "MS"
IOT_PROJECTS = ["IOTAPP", "IOTEDGE", "IOTBKND"]

# MODE: append | refresh | hybrid
MODE = "hybrid"

# ==============================
# LOGGING
# ==============================

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ==============================
# FETCH JIRA ISSUES (LAST 6 MONTHS)
# ==============================

def fetch_jira_issues():
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    all_issues = []
    next_page_token = None

    while True:
        params = {
            "jql": f"project in ({INC2_PROJECT}, {MS_PROJECT}) AND created >= -180d",
            "fields": "key,summary,status,priority,reporter,assignee,issuelinks",
            "expand": "issuelinks",
            "maxResults": 100
        }

        if next_page_token:
            params["nextPageToken"] = next_page_token

        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
            params=params
        )

        response.raise_for_status()
        data = response.json()

        all_issues.extend(data.get("issues", []))

        if data.get("isLast", True):
            break

        next_page_token = data.get("nextPageToken")

    logging.info(f"Fetched {len(all_issues)} parent tickets from Jira.")
    return all_issues

# ==============================
# FILTER ONLY IOT LINKED TICKETS
# ==============================

def filter_iot_linked(issues):
    result = {}

    for issue in issues:
        parent_key = issue["key"]
        parent_summary = issue["fields"].get("summary", "")
        parent_status = issue["fields"].get("status", {}).get("name", "")
        parent_priority = issue["fields"].get("priority", {}).get("name", "")
        fields = issue.get("fields", {})

        parent_reporter = (
            fields.get("reporter", {}).get("displayName")
            if fields.get("reporter")
            else "Unassigned"
        )

        parent_assignee = (
            fields.get("assignee", {}).get("displayName")
            if fields.get("assignee")
            else "Unassigned"
        )
 
 
        links = issue["fields"].get("issuelinks", [])

        iot_map = {proj: [] for proj in IOT_PROJECTS}

        for link in links:
            linked_issue = None

            if "outwardIssue" in link:
                linked_issue = link["outwardIssue"]
            elif "inwardIssue" in link:
                linked_issue = link["inwardIssue"]

            if linked_issue:
                key = linked_issue.get("key")
                summary = linked_issue.get("fields", {}).get("summary", "")

                if key:
                    project_prefix = key.split("-")[0]

                    if project_prefix in IOT_PROJECTS:

                        #Fetch full issue details separately
                        issue_url = f"{JIRA_BASE_URL}/rest/api/3/issue/{key}"
                        issue_response = requests.get(
                            issue_url,
                            headers={"Accept": "application/json"},
                            auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
                        )

                        issue_response.raise_for_status()
                        full_issue = issue_response.json()
                        fields = full_issue.get("fields", {})

                        status = fields.get("status", {}).get("name", "")

                        reporter = (
                            fields.get("reporter", {}).get("displayName")
                            if fields.get("reporter")
                            else "Unassigned"
                        )

                        assignee = (
                            fields.get("assignee", {}).get("displayName")
                            if fields.get("assignee")
                            else "Unassigned"
                        )

                        iot_map[project_prefix].append({
                            "key": key,
                            "summary": summary,
                            "status": status,
                            "reporter": reporter,
                            "assignee": assignee
                        })
 

        if any(iot_map.values()):
            result[parent_key] = {
                "summary": parent_summary,
                "status": parent_status,
                "priority": parent_priority,
                "reporter": parent_reporter,
                "assignee": parent_assignee,
                "iot_links": iot_map
            }

    return result
 

# ==============================
# BUILD HTML TABLE
# ==============================

def build_table(data_dict):

    table = """
    <table style="width:100%; border-collapse: collapse; font-family:Arial, sans-serif;">
        <tr>
            <th style="padding:6px;">Parent Ticket</th>
            <th style="padding:6px;">IOTAPP</th>
            <th style="padding:6px;">IOTEDGE</th>
            <th style="padding:6px;">IOTBKND</th>
        </tr>
    """

    for index, (parent, data) in enumerate(
        sorted(
            data_dict.items(),
            key=lambda x: int(x[0].split("-")[1]) if "-" in x[0] else 0,
            reverse=True
        ),
        start=1
    ):
 
        table += "<tr>"

        parent_summary = data["summary"]
        parent_status = data.get("status", "")
        parent_priority = data.get("priority", "")
        parent_reporter = data.get("reporter", "Unassigned")
        parent_assignee = data.get("assignee", "Unassigned")
        priority_color = "red" if parent_priority in ["High", "Highest", "Major"] else "orange" if parent_priority == "Medium" else "green"
        status_color = "green" if parent_status == "Closed" else \
               "orange" if parent_status == "Work in Progress" else \
               "red"
 
        parent_link = f"{JIRA_BASE_URL}/browse/{parent}"

        table += f'''
        <td style="padding:4px; vertical-align:top;">

            <div style="font-size:11px; color:#888; margin-bottom:3px;">
                #{index}
            </div>

            <div style="margin-bottom:4px;">
                <a href="{parent_link}" title="{parent_summary}" 
                    style="font-weight:600; text-decoration:none;">
                     {parent}
                </a>
            </div>

            <div style="font-size:12px; color:#555; margin-bottom:6px;">
                {parent_summary}
            </div>

            <div style="font-size:12px; margin-bottom:3px;">
                <b>Status:</b>
                <span style="color:{status_color}; font-weight:600;">
                    {parent_status}
                </span>
            </div>

            <div style="font-size:12px;">
                <b>Priority:</b>
                <span style="color:{priority_color}; font-weight:600;">
                    {parent_priority}
                </span>
            </div>

            <div style="font-size:12px; margin-top:3px;">
                <b>Reporter:</b> {parent_reporter}
            </div>

            <div style="font-size:12px;">
                <b>Assignee:</b> {parent_assignee}
            </div>
        </td>
        '''
 

        for proj in IOT_PROJECTS:
            links = data["iot_links"].get(proj, [])

            if links:  
                link_html = ""

                for item in links:
                    iot_status = item.get("status", "")
                    iot_reporter = item.get("reporter", "Unassigned")
                    iot_assignee = item.get("assignee", "Unassigned")
                    iot_color = "green" if iot_status == "Closed" else \
                                "orange" if iot_status == "Work in Progress" else \
                                "red"

                    link_html += f'''
                    <div style="margin-bottom:8px;">

                        <div>
                            <a href="{JIRA_BASE_URL}/browse/{item["key"]}"    
                                style="font-weight:600; text-decoration:none;">
                                 {item["key"]}
                            </a>
                        </div>

                        <div style="font-size:12px; color:#555; margin-bottom:3px;">
                            {item["summary"]}
                        </div>

                        <div style="font-size:12px;">
                            <span style="color:{iot_color}; font-weight:600;">
                                {iot_status}
                            </span>
                        </div>

                        <div style="font-size:12px">
                            <b>Reporter:</b> {iot_reporter}
                        </div>

                        <div style="font-size:12px">
                            <b>Assignee:</b> {iot_assignee}
                    </div>
                    '''
 
 
            else:
                link_html = "-"
            table += f'<td style="padding:4px; word-wrap:break-word;">{link_html}</td>'

        table += "</tr>"

    table += "</table>"
    return table
 
# ==============================
# GET CONFLUENCE PAGE
# ==============================

def get_confluence_page():
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}?expand=body.storage,version"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
    )
    response.raise_for_status()
    return response.json()

# ==============================
# UPDATE CONFLUENCE
# ==============================

def update_confluence(new_table_html):
    page = get_confluence_page()

    current_version = page["version"]["number"]
    title = page["title"]
    old_body = page["body"]["storage"]["value"]

    if MODE == "append":
        body = old_body + new_table_html

    elif MODE == "refresh":
        body = new_table_html

    elif MODE == "hybrid":
        body = new_table_html  # since page empty, rebuild fully

    else:
        raise ValueError("Invalid MODE")

    update_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}"

    payload = {
        "id": CONFLUENCE_PAGE_ID,
        "type": "page",
        "title": title,
        "version": {"number": current_version + 1},
        "body": {
            "storage": {
                "value": body,
                "representation": "storage"
            }
        }
    }

    response = requests.put(
        update_url,
        json=payload,
        auth=HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
        headers={"Content-Type": "application/json"}
    )

    response.raise_for_status()
    logging.info("Confluence updated successfully.")

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    logging.info("Fetching Jira issues...")
    issues = fetch_jira_issues()

    logging.info("Filtering IOT linked tickets...")
    filtered = filter_iot_linked(issues)

    total_updated = len(filtered)

    if total_updated == 0:
        logging.info("No IOT linked tickets found.")

    else:

        logging.info(f"Total parent tickets with IOT links: {total_updated}")

        logging.info("Building table...")
        table_html = build_table(filtered)

        logging.info("Updating Confluence...")
        update_confluence(table_html)

        logging.info(f"Successfully updated {total_updated} tickets to Confluence.")
 
