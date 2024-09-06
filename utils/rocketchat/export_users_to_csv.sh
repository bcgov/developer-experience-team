#!/bin/zsh

export RC_USER_ID=$(op item get "Rocket.Chat token" --fields label=username)
export RC_AUTH_TOKEN=$(op item get "Rocket.Chat token" --fields label=credential)

python export_users.py | jq -r '.[] | [.name, .username, .emails[0].address, .roles[0], .roles[1], .roles[2], .roles[3], .active, .lastLogin] | @csv' > rocketchat_users.csv
