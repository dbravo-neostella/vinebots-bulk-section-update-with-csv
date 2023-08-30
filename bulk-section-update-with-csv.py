import csv
import requests
from credentials import API_KEY, API_SECRET, BASE_URL
from filevine_utils import (
    TOKENS_TEMPLATE,
    create_headers,
    handle_authentication,
    handle_rate_limit
)

headers_authentication = {"Content-Type": "application/json"}

tokens = TOKENS_TEMPLATE.copy()

status, access_token, refresh_token = handle_authentication(
    BASE_URL, headers_authentication, API_KEY, API_SECRET, tokens
)

headers = create_headers(access_token, refresh_token)

# Section and Field Selectors to update
section_selector = "projectOverview"
field_selectors = {
    "campaignSimplyConvert": "Posted via Braver Law",
    "referralType": "API"
}

successful_updates = []
failed_updates = []

projects_from_csv = []

with open('input_csv/input-test.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        projects_from_csv.append({
            "projectId": int(row["FV Project ID"])
        })

# Iterate through the list of contacts and remove emails
for project in projects_from_csv:
    project_id = project["projectId"]

    try:
        response = requests.patch(
            BASE_URL + f"/core/projects/{project_id}/forms/{section_selector}",
            headers=headers,
            json=field_selectors
        )
        handle_rate_limit()
        if response.status_code == 200:
            successful_updates.append(project_id)
        else:
            failed_updates.append({
                "projectId": project_id,
                "error": response.text
            })
    except Exception as e:
        print("\nError occurred:", e)
        handle_rate_limit()
        failed_updates.append({
            "projectId": project_id,
            "error": str(e)
        })

# Writing results to CSV files
with open('successful_updates.csv', 'w') as file:
    file.write("ContactID\n")
    for pid in successful_updates:
        file.write(f"{pid}\n")

with open('failed_updates.csv', 'w') as file:
    file.write("ContactID,Error\n")
    for entry in failed_updates:
        file.write(f"{entry['projectId']},{entry['error']}\n")
