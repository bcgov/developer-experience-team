# GitHub Repository Creator

This project automates the creation of private GitHub repositories in an organization and assigns users and teams to each repository with the stated permission. 

The input file is validated before it is processed. The validation fails on any of the following:

- User is not a member of the organization
- Team does not exist in the organization
- JSON file does not match the expected schema

Check the log file for results and errors after the run completes.

>[!WARNING]
>Validation of a user's org membership and assignment of that user to a repo are seperate tasks. There is no option to combine as one transaction. This means between the valdiation and assignment it is possible the user was removed from the org. 
>This means a user could be assigned to the repo as an outside collaborator. If this happens an error message is logged to the log file. The probability of this scenario is low.


## Prerequisites

- Node.js 26 or later
- A GitHub fine-grain personal access token with permissions:
  - Organization permissions:
    - Read access to members
  - Repository permissions:
    - Read access to metadata
    - Read and Write access to administration
  - The PAT owner will need the underlying permissions to run the script

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Create a local environment file from the example if needed:

   ```bash
   cp .env.example .env
   ```

3. Set your GitHub token in the environment:

   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

   Alternatively, set it in a `.env` file:

   ```bash
   GITHUB_TOKEN=your_github_token_here
   ```

## Usage

### Input file format

The JSON file should be an array of repository objects. Each object must include a `name`, and either or both a `users` list, and a `teams` list.

Structure:

* `name` - The repo name. It must NOT contain the owner, org or url data
* `users[].name` - The GitHub username
* `users[].permission` - Refer to [Supported permissions](#supported-permissions) below
* `teams[].slug` - The GitHub team slug, not the team name (e.g. `team-bravo` is the team slug for GitHub Team `Team Bravo`)
* `teams[].permission` - Refer to [Supported permissions](#supported-permissions) below

Example:

```json
[
  {
    "name": "example-repo-1",
    "users": [
      { "name": "user1", "permission": "admin" },
      { "name": "user2", "permission": "push" }
    ],
    "teams": [
      { "slug": "team-bravo", "permission": "maintain" }
    ]
  }
]
```

### Supported permissions

Valid permissions are:

- `pull`
- `triage`
- `push`
- `maintain`
- `admin`

Reference `permission` field in [Add or update team repository permissions](https://docs.github.com/en/rest/teams/teams?apiVersion=2026-03-10#add-or-update-team-repository-permissions) documentation.

### Running

```bash
npm start -- --org <organization-name> --input <path-to-json> --output <path-to-results>
```
**Arguments**

- `--org`, `-o`: GitHub organization name.
- `--input`, `-i`: Path to the input JSON file.
- `--output`, `-u`: Path to the output file. Existing files are overwritten.

Example:

```bash
npm start -- --org bcgov-c --input example.json --output results.txt
```

```bash
node src/index.js --org bcgov-c --input example.json --output results.txt
```

## Tests

```bash
npm test
```
