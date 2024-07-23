from pathlib import Path

import requests
import json

import yaml


def load_github_auth_from_github_hub() -> str:
    hub_path = Path.home().joinpath('.config/hub')
    if hub_path.exists():
        with open(hub_path) as hub_file:
            hub_config = yaml.safe_load(hub_file)
        return hub_config['github.com'][0]['oauth_token']
    else:
        raise ValueError("No GitHub Hub configuration found.")


# GitHub organization and authentication token
ORG_NAME = "Chainguard-Wolfi-Bites-Back"
TOKEN = load_github_auth_from_github_hub()
OUTPUT_FILE = 'code_scanning_alerts.json'


def fetch_code_scanning_alerts(org_name, token, output_file):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    all_alerts = []
    url = f'https://api.github.com/orgs/{org_name}/code-scanning/alerts'
    while url:
        print(f"Fetching {url}")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break

        alerts = response.json()
        all_alerts.extend(alerts)

        # Get the next page URL from the Link header
        if 'link' in response.headers:
            links = response.headers['link'].split(',')
            url = None
            for link in links:
                if 'rel="next"' in link:
                    url = link[link.find('<') + 1:link.find('>')]
                    break
        else:
            url = None

    with open(output_file, 'w') as f:
        json.dump(all_alerts, f, indent=4)

    print(f"Data written to {output_file}")


if __name__ == '__main__':
    fetch_code_scanning_alerts(ORG_NAME, TOKEN, OUTPUT_FILE)
