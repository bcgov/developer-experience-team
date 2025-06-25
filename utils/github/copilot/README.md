# Copilot Onboarding Script

## Description

This script automates the process of assigning GitHub Copilot licenses to users, inviting them to a GitHub organization, and adding them to a specific team within the organization. It is designed to streamline the onboarding process for GitHub Copilot users in a structured and efficient manner.

## Prerequisites

- A GitHub personal access token with the necessary permissions:
  - `admin:org` for managing organization memberships.
  - `write:copilot` for assigning Copilot licenses.
- Node.js (v16 or higher) installed on your system
- yarn, if using
- The required dependencies installed via `npm install` or `yarn`.
- GITHUB_TOKEN defined as an environment variable, or in a .env (not stored in version control)

## How It Works

1. **Input Handling**:  
   The script accepts a list of GitHub usernames either via a CSV file or standard input. Each username represents a user to be onboarded.

2. **License Assignment**:  
   For each user, the script assigns a GitHub Copilot license using the GitHub API.

3. **Ading user to a team within an organization **:  
   The script checks if the user is already a member of the specified cohort organization:
   - If the user is a member, they are added to the specified team within the organization.
   - If the user is not a member, an invitation is sent to join the organization. The user is not added to the team until they accept the invitation.

4. **Error Handling**:  
   The script logs any errors encountered during the process, such as API failures or invalid input.

## Setup

1. Clone the repository or navigate to the script directory, if you've already cloned.
2. Install dependencies:
   ```bash
   npm install
   ```

   or 

   ```bash
   yarn
   ```
## Usage

Run the script using Node.js with the following command:

```bash
node copilot_onboarding.ts <org_name> <cohort_org_name> <cohort_team_name> [csv_file_path]
```

### Arguments

- `<org_name>`: The name of the organization where Copilot licenses will be assigned.
- `<cohort_org_name>`: The name of the organization containing the team to which users will be added.
- `<cohort_team_name>`: The name of the team within the cohort organization to which users will be added.
- `[csv_file_path]` (optional): The path to a CSV file containing GitHub usernames. If omitted, the script will read usernames from standard input.

### CSV File Format

The CSV file should have a column named `github_id` containing the GitHub usernames. Example:

```csv
github_id
user1
user2
user3
```

### Examples

Assign licenses and onboard users from a CSV file:

```bash
node copilot_onboarding.ts my-org cohort-org cohort-team users.csv
```

Assign licenses and onboard users from standard input:

```bash
echo "johndoe" | node copilot_onboarding.ts my-org cohort-org cohort-team
```

## Logging

The script uses `console-log-level` for logging. Currently, a mix of infromational messages and errors are logged. The logging behaviour can be modified in the script if needed.

## Notes

- Ensure that the GitHub token has the required permissions.
- Users who are not members of the cohort organization will receive an invitation. They must accept the invitation before being added to the team the next time the script is run.
- The script handles errors gracefully, loggin any issues encountered during execution with a specific user and continuing with the next user in the input.