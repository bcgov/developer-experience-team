## How to run

> Note: `app.js` depends on a set of environment variables being set that all it to authenticate as a GitHub App. Currently, these are set up in `run.sh` using values in `1password`. In the future, credentials could be moved into `Vault` or other secure, central location to allow other team members to run the app using the shared credentials.

- run linked [users report](../../idir/get_linked_users.sh) and dump to file
- update `run.sh` with name of latest linked users report and desired output json file
- run `run.sh`
- update `collaborator_report_permissions.sh` with name of output file from above and desired output CSV file 
- run `collaborator_report_permissions.sh`

### To check for potential orphaned repos

- using output csv file from above, run command below, replacing `collab_repo_permissions6.csv` with current output file.

```shell
awk '{print $1,$9,$10}' collab_repo_permissions6.csv | grep false | sort | uniq | wc -l 
```
