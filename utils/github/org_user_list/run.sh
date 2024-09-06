
export GITHUB_TOKEN=$(op item get Github --fields label=pat)

node app.js BCDevOps bcgov invitees.json uninvitees.json removed_bcgov_users.csv

