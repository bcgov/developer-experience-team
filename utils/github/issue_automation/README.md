# Description

This script was created for DEVXT-1947. 

The task was to automate creating issues on a given list of repos. It also comments on the issues.

Repo collaborators that have `push` access to the repo will be tagged in the issue and comments. Org administrators have `push` access to all org repositories. They are excluded from the tagging so as not to overwhelm their mentions. If a repo does not have any collaborators to tag, it will use a default greeting instead.

# Setup

A [GitHub fine grain access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens) with the following permissions is required:
 
- Org 
  - read access to members
- Repository 
  - read access to metadata
  - write access to issues

Create an .env file with the following values:
```
GITHUB_TOKEN=token
FILE=/path/to/file.txt
ORG=github-org
```

The `FILE` path is a text file that contains a list of repos to be notified via issues. There should be one repo name per line. It is assumed all repos belong to the ORG.

The `ORG` is the GitHub organization the repos belong to.

Example input file:

## file.txt
```
test-repo-1
test-repo-2
test-repo-3
```


# Running

The issue and comments text are handled by [mustache](https://github.com/janl/mustache.js) templates.

The script can be run by passing in the appropriate template. The [package.json](./package.json) file has default scripts with the appropriate templates already setup.

## Create issue

Create the issue on each repo specified in the input file.


```shell
npm run notify
```

## Reminder comment

Comment on the issue.

```shell
npm run reminder
```

## Final reminder comment

Comment with a final reminder.

```shell
npm run final
```

# Known issues

This script was hardcoded for a specific use case: providing an initial GitHub issue, and then 2 comments on that issue.

## Commenting on a GitHub issue

The issue is found by searching for the hardcoded title. If the title has been changed (either in code or the repo), the issue will not be found.

## Multiple GitHub issues

The script checks if the issue with the hardcoded title already exists. If it does, a new issue will NOT be created.

The script uses the latest created issued (with the title), to apply the comment to.

