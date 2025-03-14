# README

## Setup

An `.env` file with the following keys is required:

GITHUB_TOKEN_DESTINATION=token requires read access to organization members
ORG_NAME_SOURCE=the org where the repos currently exist
ORG_NAME_DESTINATION=the org where the repos are to be transferred to
REPO_FILE=location of file containing the list of repos to transfer
TEAMS_FILE=location of file contain the list of teams and their permissions per repo.

The [GitHub cli](https://cli.github.com) must also be installed.

This repo has two scripts in it:

## transfer.js 

This script transfers a repo from one org to another. It assigns teams as part of the transfer. But the teams will only have read access.

Run the script with:

```
npm run transfer
```

Example input file:

```
REPO,TEAMS
repo-1,team-1
repo-2,team-1 team-2 team-3
```

A repo can have multipe teams. The teams are space delimited in the TEAMS column.
The header row is required.

## permissions.js

This script updates teams' permissions on repos. It takes a file that contains a mapping of repos to teams with the associated permission. The team and repo associations must match what was done in the transfer step.

Run the script with:

```
npm run permissions
```


Refer to [GitHub's documentation](https://docs.github.com/en/rest/teams/teams?apiVersion=2022-11-28#add-or-update-team-repository-permissions) for possible values for the permissions.

Example input file:

```
REPO,TEAM,PERMISSION
test-repo-131,developer-experience,admin
test-repo-131,test-team,push
test-repo-130,developer-experience,maintain
test-repo-130,test-team,admin
test-repo-129,developer-experience,admin
test-repo-128,developer-experience,admin
test-repo-127,test-team,admin
```


## Why are there 2 scripts
It is broken into a transfer and permission step because the transfer step takes a small amount of time. If the permissions are set right after the transfer, they fail as the transfer has not completed. Running the permissions after allows the time needed for the transfer to complete.

## Why are both the GitHub CLI and rest api used
The [repo transfer endpoint](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#transfer-a-repository) only accepts GitHub app user access tokens. The GitHub CLI meets that requirement. I already had written the code to get the team data, which uses Rest API. I was too lazy to go back and change it since it worked.