### Secrets

All environment variables are either read directly from the environment or a `.env` file in the execution directory.

The client requires a few secrets to be set in the environment:

#### GitHub API Token
Is read from
- `~/.config/hub` file
- 
### CLI Usage

To install the CLI dependencies use the following command:

```bash
pip install .[cli]
```

For live development, you can use the following command to install the CLI in editable mode:
```bash
pip install -e .[cli]
```
To see more information about developing the CLI, see the [CONTRIBUTING](CONTRIBUTING.md) guide.

To use it as a script, you can run it like this:

```bash
oss-security-assessments-manager --help
```