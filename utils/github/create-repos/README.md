# GitHub Repository Creator

This project automates the creation of GitHub repositories in an organization and assigns users and teams to each repository with specific permissions. A repository with no users and no teams is skipped. Repo visibility is hard coded to 'private'.

## Prerequisites

- Node.js 26 or later
- A GitHub fine grain personal access token with permissions:
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

The JSON file should be an array of repository objects. Each object can include a `name`, a `users` list, and a `teams` list.

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
      { "name": "team1", "permission": "maintain" }
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

Run the script with the organization name and a JSON file that defines repositories:

```bash
npm start -- --org <organization-name> --file <path-to-json>
```

Example:

```bash
npm start -- --org bcgov-c --file example.json
```

You can also run the script directly with Node:

```bash
node src/index.js --org bcgov-c --file example.json
```

## Notes

- Repositories are created as `private`.
- A repository with no users and no teams is skipped.
- Users are only assigned if they are already members of the target organization.
- The script logs status messages as it processes organizations, repositories, users, and teams.

