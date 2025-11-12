import os
import requests
import glob

LINEAR_API_KEY = os.environ.get("LINEAR_APP_API_KEY") or os.environ.get("LINEAR_APP_LONG_TOKEN")
LINEAR_API_URL = "https://api.linear.app/graphql"
TEAM_NAME = "Cloudcurio"
PROJECT_NAME = "opendiscourse.com"

HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

def get_team_id():
    query = '{ teams { nodes { id name } } }'
    resp = requests.post(LINEAR_API_URL, headers=HEADERS, json={"query": query})
    teams = resp.json()["data"]["teams"]["nodes"]
    for team in teams:
        if team["name"].lower() == TEAM_NAME.lower():
            return team["id"]
    raise Exception(f"Team '{TEAM_NAME}' not found in Linear.")

def create_issue(team_id, title, description):
    mutation = '''
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) { issue { id identifier title } }
    }
    '''
    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description[:10000]  # Linear API limit
        }
    }
    resp = requests.post(LINEAR_API_URL, headers=HEADERS, json={"query": mutation, "variables": variables})
    return resp.json()

def create_project(team_id, project_name):
    mutation = '''
    mutation ProjectCreate($input: ProjectCreateInput!) {
      projectCreate(input: $input) { project { id name } }
    }
    '''
    variables = {
        "input": {
            "teamId": team_id,
            "name": project_name
        }
    }
    resp = requests.post(LINEAR_API_URL, headers=HEADERS, json={"query": mutation, "variables": variables})
    data = resp.json()
    return data["data"]["projectCreate"]["project"]["id"]

def main():
    team_id = get_team_id()
    print(f"Using Linear team: {TEAM_NAME} (id: {team_id})")
    project_id = create_project(team_id, PROJECT_NAME)
    print(f"Using/Created Linear project: {PROJECT_NAME} (id: {project_id})")
    files = glob.glob("*.*")
    for file in files:
        if os.path.isfile(file):
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            title = f"[AutoImport] {file}"
            print(f"Pushing {file} to Linear...")
            result = create_issue(team_id, title, content)
            print(f"Result: {result}")

if __name__ == "__main__":
    main()
