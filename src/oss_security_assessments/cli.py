from pathlib import Path
from time import sleep

import yaml
from dotenv import load_dotenv
from github import Github, Auth, GithubException, UnknownObjectException
from github.Organization import Organization
from github.Repository import Repository

from oss_security_assessments.github_selenium import GitHubSelenium
from oss_security_assessments.onepassword_wrapper import OnePassword


def load_github_auth_from_github_hub() -> str:
    hub_path = Path.home().joinpath('.config/hub')
    if hub_path.exists():
        with open(hub_path) as hub_file:
            hub_config = yaml.safe_load(hub_file)
        return hub_config['github.com'][0]['oauth_token']
    else:
        raise ValueError("No GitHub Hub configuration found.")


def load_github() -> Github:
    # using an access token
    auth = Auth.Token(load_github_auth_from_github_hub())

    return Github(auth=auth)


def configure_repository_after_fork(repo: Repository):
    print(f"Configuring {repo.name} ...")
    repo.edit(
        has_issues=False,
        has_projects=False,
        has_wiki=False
    )
    workflows = repo.get_workflows()
    for workflow in workflows:
        if "security" in workflow.name.lower() or "codeql" in workflow.name.lower():
            print(f"Keeping {workflow.name} enabled...")
            continue
        if "disabled" in workflow.state:
            print(f"Skipping {workflow.name} because it's already disabled.")
            continue
        print(f"Disabling {workflow.name} ...")
        # Manually disable the workflow because the API doesn't exist on PyGithub
        try:
            repo._requester.requestJsonAndCheck(
                "PUT",
                f"/repos/{repo.owner.login}/{repo.name}/actions/workflows/{workflow.id}/disable",
            )
        except GithubException as e:
            if e.status != 403:
                raise e
            print(f"\t{e.data['message'] if 'message' in e.data else e.data}")


def fork_repo_to_org(org: Organization, repo: Repository) -> Repository:
    new_repo_name = repo.owner.login + "__" + repo.name
    try:
        existing_repository = org.get_repo(new_repo_name)
        print(f"Using existing fork of {repo.name} to {org.login} with name {new_repo_name} ...")
        return existing_repository
    except UnknownObjectException:
        pass
    print(f"Forking {repo.name} to {org.login} with name {new_repo_name} ...")
    retry_count = 0
    last_exception: GithubException = None
    while retry_count < 5:
        try:
            return org.create_fork(
                repo,
                name=new_repo_name,
                default_branch_only=True
            )
        except GithubException as e:
            if e.status != 403:
                raise e
            print(f"\tFork failed: {e.data['message'] if 'message' in e.data else e.data}")
            retry_count += 1
            print(f"Retrying in {retry_count} seconds...")
            sleep(retry_count)
            last_exception = e
    raise last_exception


def cli():
    load_dotenv()
    g = load_github()
    organization = g.get_organization("OSS-Security-Assessments")
    apache = g.get_organization("apache")

    one_password = OnePassword()

    with GitHubSelenium() as gh_selenium:
        gh_selenium.login(one_password)

        repos_to_fork = apache.get_repos(
            sort="updated",
            direction="desc",
        )

        repository: Repository
        for repository in repos_to_fork:
            if repository.stargazers_count < 100:
                print(f"Skipping {repository.name} because it has less than 100 stars.")
                continue
            if repository.archived:
                print(f"Skipping {repository.name} because it's archived.")
                continue
            if repository.fork:
                print(f"Skipping {repository.name} because it's a fork.")
                continue

            new_repository = fork_repo_to_org(organization, repository)

            gh_selenium.enable_github_actions(new_repository)

            configure_repository_after_fork(new_repository)
