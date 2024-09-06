#!/bin/zsh
export KEYCLOAK_HOME=~/Downloads/keycloak-24.0.4/bin
export PATH=$PATH:$KEYCLOAK_HOME
#kcadm.sh get users --limit 5000 | jq -r '.[] | [ .username, .firstName, .lastName, .email, .attributes.idir_username[0], .attributes.github_id[0], .attributes.github_username[0], .attributes.orgs[0], .attributes.display_name[0] ] | @csv'
kcadm.sh get users --limit 5000 | jq -r '.[] | ["openshift", .username, .firstName, .lastName, .email, .attributes.idir_username[0], .attributes.github_id[0], .username, .attributes.orgs[0], .attributes.displayName[0] ] | @csv'
#kcadm.sh get users --limit 5000
