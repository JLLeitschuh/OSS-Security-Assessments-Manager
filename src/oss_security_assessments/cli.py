import random
from pathlib import Path
from time import sleep
from typing import Iterable, Generator

import yaml
from dotenv import load_dotenv
from github import Github, Auth, GithubException, UnknownObjectException
from github.Organization import Organization
from github.Repository import Repository

from oss_security_assessments.github_selenium import GitHubSelenium
from oss_security_assessments.onepassword_wrapper import OnePassword
from .util import fibonacci


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
    if repo.has_wiki or repo.has_projects or repo.has_issues:
        repo.edit(
            has_issues=False,
            has_projects=False,
            has_wiki=False
        )
    workflows = repo.get_workflows()
    for workflow in workflows:
        lower_name = workflow.name.lower()
        if "security" in lower_name or "codeql" in lower_name or "semgrep" in lower_name:
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


def fork_repo_to_org(org: Organization, repo: Repository) -> (Repository, bool):
    new_repo_name = repo.owner.login + "__" + repo.name
    try:
        existing_repository = org.get_repo(new_repo_name)
        print(f"Using existing fork of {repo.name} to {org.login} with name {new_repo_name} ...")
        return existing_repository, True
    except UnknownObjectException:
        pass
    print(f"Forking {repo.name} to {org.login} with name {new_repo_name} ...")
    retry_count = 0
    last_exception: GithubException = None
    while retry_count < 20:
        try:
            return org.create_fork(
                repo,
                name=new_repo_name,
                default_branch_only=True
            ), False
        except GithubException as e:
            if e.status != 403:
                raise e
            print(f"\tFork failed: {e.data['message'] if 'message' in e.data else e.data}")
            retry_count += 1
            sleep_time = fibonacci(retry_count)
            print(f"Retrying in {sleep_time} seconds...")
            sleep(sleep_time)
            last_exception = e
    raise last_exception


def fork_and_configure_repositories(
        gh_selenium: GitHubSelenium,
        organization: Organization,
        repositories: Iterable[Repository]
):
    process_later: list[Repository] = list()
    repository: Repository
    for repository in repositories:
        if repository.archived:
            print(f"Skipping {repository.name} because it's archived.")
            continue
        if repository.fork:
            print(f"Skipping {repository.name} because it's a fork.")
            continue

        new_repository, did_exist = fork_repo_to_org(organization, repository)

        if not did_exist:
            gh_selenium.enable_github_actions(new_repository)

            configure_repository_after_fork(new_repository)
        else:
            process_later.append(new_repository)

    print("🎉 Re-processing repositories that already existed ...")

    for repository in process_later:
        gh_selenium.enable_github_actions(repository)
        configure_repository_after_fork(repository)


def fork_apache_repositories():
    g = load_github()
    organization = g.get_organization("OSS-Security-Assessments")
    apache = g.get_organization("apache")

    one_password = OnePassword()

    repos_to_fork = apache.get_repos(
        sort="updated",
        direction="desc",
    )

    with GitHubSelenium() as gh_selenium:
        gh_selenium.login(one_password)

        fork_and_configure_repositories(gh_selenium, organization, repos_to_fork)


def lazy_load_wolfi_repositories(github: Github) -> Generator[Repository, None, None]:
    repos = list()
    with open("repository_names.txt") as file:
        for line in file:
            repository = line.strip()
            if repository.startswith("jenkinsci"):
                # My account is banned from forking Jenkins repositories 😭
                # https://github.com/jenkinsci/continuum-plugin/pull/2#issuecomment-1858768225
                continue
            repos.append(repository)

    random.shuffle(repos)

    for repo in repos:
        yield github.get_repo(repo)


def fork_wolfi_repositories():
    g = load_github()
    organization = g.get_organization("Chainguard-Wolfi-Bites-Back")
    one_password = OnePassword()

    repositories = lazy_load_wolfi_repositories(github=g)

    with GitHubSelenium() as gh_selenium:
        gh_selenium.login(one_password)

        fork_and_configure_repositories(gh_selenium, organization, repositories)


def cli():
    load_dotenv()
    fork_wolfi_repositories()
