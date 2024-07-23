from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

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


token = load_github_auth_from_github_hub()


@dataclass
class CodeScanningAlertResponse:
    data: List[Dict[str, any]]
    next_page: str


def get_github_org_code_scanning_page(org_name: str, page: str) -> CodeScanningAlertResponse:
    """
    List code scanning alerts for an organization

    See here for more information:
    https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2022-11-28#list-code-scanning-alerts-for-an-organization
    """

    try:
        # attempt to receive sbom for a repo
        response = requests.get(
            f"https://api.github.com/orgs/{org_name}/code-scanning/alerts?page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()

        next_page: str = response.links.get("next", {}).get("url")
        # Split the URL to get the page number
        print(next_page)
        next_page = next_page.split("page=")[1] if next_page else None
        return CodeScanningAlertResponse(
            data=response.json(),
            next_page=next_page
        )

    except requests.exceptions.RequestException as err:
        print(f"Experienced Code Scanning Alert request error for `{org_name}`: ", err)
        raise err


def get_github_org_code_scanning(org_name: str) -> List[Dict[str, any]]:
    """
    List code scanning alerts for an organization

    See here for more information:
    https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2022-11-28#list-code-scanning-alerts-for-an-organization
    """

    try:
        # attempt to receive sbom for a repo
        response = requests.get(
            f"https://api.github.com/orgs/{org_name}/code-scanning/alerts",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()

        # return the result json
        return response.json()

    except requests.exceptions.RequestException as err:
        print(f"Experienced Code Scanning Alert error for `{org_name}`: ", err)
        return None


if __name__ == "__main__":
    print(get_github_org_code_scanning_page("Chainguard-Wolfi-Bites-Back", "1").next_page)
