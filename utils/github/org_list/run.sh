
export GITHUB_TOKEN=$(op item get Github --fields label=pat)

node app.js
