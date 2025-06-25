# GitHub Security Alerts Script

This script retrieves CodeQL security alerts for a specified GitHub repository using the GitHub API and the [PyGithub](https://pygithub.readthedocs.io/) library.

## Features

- Authenticates to GitHub using a personal access token (PAT) provided via the `GITHUB_TOKEN` environment variable.
- Retrieves CodeQL security/code scanning alerts for a given repository in a specified organization.
- Groups and displays alerts by the tool that generated them.

## Requirements

- Python 3.7+
- [PyGithub](https://pypi.org/project/PyGithub/) (see `requirements.txt`)

## Installation

1. Clone this repository or copy the script files.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Set your GitHub personal access token** (with appropriate permissions, e.g., `security_events` scope):

   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   ```

2. **Run the script**:

   ```bash
   python security_alerts_for_repo.py <org> <repo>
   ```

   Replace `<org>` with the GitHub organization name (e.g., `bcgov`) and `<repo>` with the repository name (e.g., `devhub-techdocs-publish`).

   Example:

   ```bash
   python security_alerts_for_repo.py bcgov devhub-techdocs-publish
   ```

3. **Review the output**:  
   The script will display the number of security alerts grouped by tool, along with details for each alert.

## Notes

- The script only retrieves CodeQL/code scanning alerts (not Dependabot alerts).
- Your token must have access to the repository and the required scopes to read security alerts.

## License

Apache License 2.0

