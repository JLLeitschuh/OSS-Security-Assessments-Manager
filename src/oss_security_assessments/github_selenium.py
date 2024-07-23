from dataclasses import dataclass

from github import UnknownObjectException, GithubException
from github.Repository import Repository
from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from oss_security_assessments.onepassword_wrapper import OnePassword


def _is_fork_complete(repository: Repository) -> bool:
    """Check if the fork has completed."""
    try:
        repository.get_contents("")
        return True
    except GithubException as e:
        if "This repository is empty" in e.data["message"] or "Not Found" in e.data["message"]:
            return False
        else:
            raise e


class GitHubSelenium:
    """A wrapper over GitHub using selenium to interact with the GitHub website."""
    _one_password: OnePassword
    _d: webdriver.Chrome
    _base_url: str

    def __init__(self, op: OnePassword):
        self._one_password = op

    def __enter__(self):
        """Enter the context manager."""
        self._d = webdriver.Chrome()
        self._base_url = "https://github.com/"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self._d.quit()

    def _get(self, path: str):
        return self._d.get(self._base_url + path)

    def _find_element_by_id(self, id: str) -> WebElement:
        return self._d.find_element(By.ID, id)

    def login(self):
        """Login to GitHub."""
        op = self._one_password
        self._get("login")
        self._find_element_by_id("login_field").send_keys(op.load_github_username())
        self._find_element_by_id("password").send_keys(op.load_github_password())
        self._d.find_element(By.NAME, "commit").click()
        self._get("sessions/two-factor/app")
        self._find_element_by_id("app_totp").send_keys(op.current_github_otp_value())

    @staticmethod
    def _has_github_actions(repository: Repository) -> bool:
        """Look for a GitHub actions directory using a HEAD request to see if it exists."""
        try:
            workflows_dir = repository.get_contents(".github/workflows")
        except UnknownObjectException:
            return False
        if workflows_dir is None:
            return False
        else:
            return True

    def enable_github_actions(self, repository: Repository):
        print(f"Enabling GitHub Actions for {repository.full_name} ...")
        retry = True
        while retry:
            try:
                self._get(repository.full_name + "/actions")
            except WebDriverException as e:
                if "disconnected: not connected to DevTools" in str(e):
                    print("\tDevTools disconnected. Retrying ...")
                    self.__enter__()
                    self.login()
                    continue
            try:
                self._d.find_element(
                    By.XPATH,
                    "//*[@id=\"repo-content-pjax-container\"]/div/div/div/div/div/div/form/input[1]"
                ).click()
            except NoSuchElementException:
                if not _is_fork_complete(repository):
                    print("\tFork isn't complete. Retrying ...")
                    continue
                if not self._has_github_actions(repository):
                    print("\tGitHub Actions directory doesn't exist. Skipping ...")
                    break
                if self._d.current_url.endswith("/new"):
                    continue
                # Already enabled
                break
