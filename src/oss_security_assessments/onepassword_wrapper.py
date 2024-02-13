import subprocess

import pyotp

from oss_security_assessments.util import get_env_var


class OnePassword:
    """Wrapper for 1Password CLI tool."""

    @staticmethod
    def _load_secret(secret_reference: str) -> str:
        """Load a secret from 1Password."""
        return subprocess.check_output(
            f"op read {secret_reference}",
            shell=True,
            text=True,
        ).strip()

    def load_github_username(self) -> str:
        """Load the GitHub username from 1Password."""
        return self._load_secret(get_env_var("ONE_PASSWORD_GITHUB_USERNAME_PATH"))

    def load_github_password(self) -> str:
        """Load the GitHub password from 1Password."""
        return self._load_secret(get_env_var("ONE_PASSWORD_GITHUB_PASSWORD_PATH"))

    def load_github_oauth_token(self) -> str:
        """Load the GitHub OAuth token from 1Password."""
        return self._load_secret(get_env_var("ONE_PASSWORD_GITHUB_OTP_PATH"))

    def current_github_otp_value(self) -> str:
        totp = pyotp.TOTP(self.load_github_oauth_token())
        return totp.now()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    one_password = OnePassword()
    print(f"GitHub Username: {one_password.load_github_username()}")
    print(f"GitHub Password: {one_password.load_github_password()}")
    print(f"GitHub OAuth Token: {one_password.current_github_otp_value()}")
