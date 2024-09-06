export GITHUB_APP_ID=$(op item get "Developer Experience Reporting GitHub App" --fields label=app_id)
export GITHUB_APP_INSTALLATION_ID=$(op item get "Developer Experience Reporting GitHub App" --fields label=installation_id)
export GITHUB_APP_CLIENT_ID=$(op item get "Developer Experience Reporting GitHub App" --fields label=client_id)
export GITHUB_APP_CLIENT_SECRET=$(op item get "Developer Experience Reporting GitHub App" --fields label=client_secret)
export GITHUB_APP_PRIVATE_KEY=$(op read "op://Employee/Developer Experience Reporting GitHub App/private-key-pkcs8.key")

node app.js linked_users_jul25.csv repo_collaboration_details6.json bcgov

