## Description

This folder contains a script to list potential BC Gov-affiliated GitHub organizations. It is VERY simple and just searches for organizations with the string "bc" in the name using the GitHub API.

## Usage

The shell script `/run.sh` runs the nodejs script `app.js` and also assigns a value GitHub access token to the environment variable `GIHUB_TOKEN` from a 1password vault. Users of this script should adapt it to provide a value to the environment variable by whatever (secure) means is appropriate for them. `app.js` uses the value of the environment variable to authenticate calls to the GitHub API.   

```shell
./run.sh
```
