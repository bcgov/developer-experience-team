# ent-remove-users

A small Node.js utility for removing GitHub users from a GitHub Enterprise using the GitHub GraphQL API.

## What it does

This tool:

- reads a CSV file containing GitHub usernames
- resolves each GitHub username to a GitHub user ID
- removes each user from the specified GitHub Enterprise
- supports a safe dry-run mode by default

## Prerequisites

- Node.js 26 or newer
- A GitHub token with permissions `admin:enterprise`

## Installation

From this directory, install dependencies:

```bash
npm install
```

## Environment

Set a GitHub token before running the script:

```bash
export GITHUB_TOKEN=your_token_here
```

## Usage

Run the script in dry-run mode (default):

```bash
npm run start -- --enterprise <enterprise-slug> --file <path-to-csv>
```

To actually remove users, add the `--remove` flag:

```bash
npm run start -- --enterprise <enterprise-slug> --file <path-to-csv> --remove
```

### Arguments

- `--enterprise` or `-e`: GitHub Enterprise slug
- `--file` or `-f`: Path to the CSV file containing usernames
- `--remove` or `-r`: Perform the removal; without this flag, the script runs in safe preview mode

## CSV format

The CSV file must include a `userName` column. All other columns are ignored.

Example:

```csv
userName
octocat
hubot
```

## Safety notes

- The script prompts for confirmation before proceeding.
- Without `--remove`, it will not remove users and instead simulates the process.
- Review the target enterprise and CSV contents carefully before running the removal flow.
