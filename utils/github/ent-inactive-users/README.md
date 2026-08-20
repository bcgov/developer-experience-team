# ent-inactive-users

This utility identifies GitHub Enterprise members who have been inactive for a given number of days based on:

- organization audit log activity, and
- recent commit activity in the organizations they belong to.

The script is designed for GitHub Enterprise owners or administrators who can access the enterprise and the relevant organizations.

## What it checks

For each member returned by the enterprise consumed-licenses endpoint, the script does the following:

1. Checks whether the user has any audit-log activity in the relevant organization(s) since the inactivity cutoff.
2. Checks whether the user has any commit activity in the relevant organization(s) since the cutoff.
3. Reports only users who have no activity in either source.

This avoids false positives when activity is recorded in organization audit logs but not enterprise-level logs, and it stops checking additional organizations as soon as one shows recent activity.

## Requirements

- Node.js 26 or newer
- A GitHub personal access token with access to the enterprise and organizations
- Token permissions required:
  - `read:audit_log`
  - `read:enterprise`
  - `read:org`
  - `repo`

## Install

```bash
npm install
```

## Usage

The entry point is `src/index.js` and it expects `GITHUB_TOKEN` plus the target enterprise name.

By default it will use all organizations and check activity for the last 90 days.

```bash
export GITHUB_TOKEN=xxx
npm run run -- --enterprise <enterprise-slug>
```

To limit the scan to specific organizations:

```bash
export GITHUB_TOKEN=xxx
npm run run -- --enterprise <enterprise-slug> --org <org-slug-1> --org <org-slug-2>
```

If `--org` is omitted, the script uses all organizations in the enterprise.

Use the `--inactiveDays` flag to specify a period other than 90 days:

```bash
export GITHUB_TOKEN=xxx
npm run run -- --enterprise <enterprise-slug> --org <org-slug-1> --org <org-slug-2> --inactiveDays <days>
```

### Parameters

```
-e --enterprise = Required. The enterprise slug
-o --org = Optional. Specify one or more orgs that will be used to check for activity
-d --inactiveDays = Defaults to 90 days. If provided must be between 1 and 180.
```

### Common commands

```bash
npm start -- --enterprise my-enterprise
npm start -- --enterprise my-enterprise --inactiveDays 60
npm run run -- --enterprise my-enterprise --org engineering --org platform
node src/index.js --enterprise my-enterprise
```

## Output

The script writes a CSV report to the current working directory. 


```csv
userName,email
alice,alice@example.com
bob,bob@example.com
```

## Testing

```bash
npm test
```



