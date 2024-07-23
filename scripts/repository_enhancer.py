import json
from pathlib import Path
from packageurl import PackageURL
from typing import Dict, Optional

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


def get_github_repo_sbom(full_name: str) -> Optional[Dict[str, any]]:
    """
    Gathers GitHub Software Bill of Materials (SBOM) data
    given a full_name (org/repo_name).

    See here for more information:
    https://docs.github.com/en/rest/dependency-graph/sboms
    """

    try:
        # attempt to receive sbom for a repo
        response = requests.get(
            f"https://api.github.com/repos/{full_name}/dependency-graph/sbom",
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
        print(f"Experienced SBOM request error for `{full_name}`: ", err)
        return None


def load_wolfi_repositories() -> list[str]:
    repos = list()
    with open("repository_names.txt") as file:
        for line in file:
            repository = line.strip()
            if repository.startswith("jenkinsci"):
                # My account is banned from forking Jenkins repositories 😭
                # https://github.com/jenkinsci/continuum-plugin/pull/2#issuecomment-1858768225
                continue
            repos.append(repository)
    return repos


if __name__ == '__main__':
    # get sbom for a repo

    repositories = load_wolfi_repositories()
    purls = set()
    missing_purl = {}
    missing_purl_by_ecosystem = {}
    for repo in repositories:
        sbom_content = get_github_repo_sbom(repo)
        if not sbom_content:
            continue
        sbom = sbom_content['sbom']
        packages = sbom['packages']

        for package in packages:
            name = package['name']
            if 'externalRefs' not in package:
                missing_purl[sbom['documentNamespace']] = sbom
                ecosystem = name.split(':')[0]
                missing_purl_by_ecosystem[ecosystem] = missing_purl_by_ecosystem.get(ecosystem, 0) + 1
                continue
            purl_found = False
            for external_ref in package['externalRefs']:
                reference_type = external_ref['referenceType']
                if reference_type != 'purl':
                    continue
                purl_found = True
                purl_string = external_ref['referenceLocator']
                purl = PackageURL.from_string(purl_string)
                purl = purl._replace(version=None)  # remove version to simplify
                purls.add(purl.to_string())
                break
            if not purl_found:
                raise ValueError(
                    f"`externalRefs` but missing PURL for {package['name']} in {sbom['documentNamespace']}")

    print('PURLs:')
    for purl in sorted(purls):
        print(f'\t{purl}')

    with open('purls.txt', 'w') as f:
        for purl in sorted(purls):
            f.write(f'{purl}\n')

    print('Missing PURLs:')
    for key in missing_purl:
        url = key
        sbom = missing_purl[key]
        print(f'\t{"/".join(url.split("/")[:-2])}/network/dependencies')
        # JSON Dump the SBOM deeply indented below the URL
        sbom_string = json.dumps(sbom, indent=2)
        for line in sbom_string.split('\n'):
            print(f'\t\t{line}')

    print('Missing PURLs by ecosystem:')
    for key in missing_purl_by_ecosystem:
        print(f'\t{key}: {missing_purl_by_ecosystem[key]}')
