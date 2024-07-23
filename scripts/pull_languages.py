import json
from pathlib import Path

import requests
import yaml


def load_github_auth_from_github_hub() -> str:
    hub_path = Path.home().joinpath('.config/hub')
    if hub_path.exists():
        with open(hub_path) as hub_file:
            hub_config = yaml.safe_load(hub_file)
        return hub_config['github.com'][0]['oauth_token']
    else:
        raise ValueError("No GitHub Hub configuration found.")


TOKEN = load_github_auth_from_github_hub()

headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}


# Function to fetch data from GitHub
def fetch_from_github(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def languages_url(repo_name: str) -> str:
    return f'https://api.github.com/repos/{repo_name}/languages'


def code_scanning_default_url(repo_name: str) -> str:
    return f'https://api.github.com/repos/{repo_name}/code-scanning/default-setup'


def transform_repository_name(repository_name: str) -> str:
    return "Chainguard-Wolfi-Bites-Back/" + repository_name.replace('/', '__')


if __name__ == '__main__':
    # Load the data from the JSON file
    repository_names = []
    with open('repository_names.txt', 'r') as file:
        # Read each line from text file
        for line in file:
            repository_names.append(line.strip())

    print(f"Loaded {len(repository_names)} repository names")

    # List to hold the output data
    output_data = []

    print("Processing repository names...")

    # Load both the repository names and the language URLs
    for repository_name in repository_names:
        # Get the repository name
        repository_name = transform_repository_name(repository_name)

        # Check if the repository exists
        try:
            fetch_from_github(f'https://api.github.com/repos/{repository_name}')
        except requests.exceptions.HTTPError as e:
            print(f"Repository {repository_name} not found, skipping...")
            continue

        # Fetch the languages data
        languages_data = fetch_from_github(languages_url(repository_name))

        # Fetch the code scanning default setup data
        code_scanning_data = fetch_from_github(code_scanning_default_url(repository_name))

        # Add the data to the output list
        output_data.append({
            'repository_name': repository_name,
            'languages': languages_data,
            'default_code_scanning': code_scanning_data
        })

    # Write the output data to a new JSON file
    with open('repository_languages.json', 'w') as file:
        json.dump(output_data, file, indent=4)

    print("Data has been written to repository_languages.json")
