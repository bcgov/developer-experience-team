## Description

This folder contains a script to produce a report on users' membership within multiple BC Gov-managed organizations. It is a bit complicated and makes use of the GitHub API along with GitHub event log dumpfile to assemble the report. The purpose of the report is inform decisions about consolidation users' memberships across accounts.   

## Usage

The shell script `/run.sh` runs the nodejs script `app.js` and also assigns a GitHub access token to the environment variable `GIHUB_TOKEN` from a 1password vault. Users of this script should adapt it to provide a value to the environment variable by whatever (secure) means is appropriate for them. `app.js` uses the value of the environment variable to authenticate calls to the GitHub API.

The `run.sh` script requires that a file containing the contents of the GitHub audit log in the same directory as the script. The script should be updated to reflect the name of the file. This file can be produced by an organizations owner from the GitHub web interface with this link, or creating the equivalent query manually in the GitHub UI. In either case, the Export -> CSV option should be chosen and the file saved in the same directory as `run.sh`. 

```shell
./run.sh
```
