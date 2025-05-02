#!/bin/zsh
usage() {
  echo "Usage: $1 <org_name> [-r|--remove]"
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage "$0"
fi

ORG="$1"
REMOVE_FLAG=""

if [[ $# -eq 2 ]]; then
  case "$2" in
    -r|--remove)
      REMOVE_FLAG="-r"
      ;;
    *)
      usage "$0"
      ;;
  esac
fi

 gh api graphql --paginate -F org=$ORG -f query='query($org: String!, $endCursor:String) {
  organization(login: $org) {
    samlIdentityProvider {
      externalIdentities(first: 100, after: $endCursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
        edges {
          node {
            guid
            samlIdentity {
              nameId
            }
            user {
              login
              name
              email
              id
            }
          }
        }
      }
    }
  }
}' | jq  -r  '.data.organization.samlIdentityProvider.externalIdentities.edges[] | [.node.samlIdentity.nameId, .node.user.login] | @csv' | python check_idir_status.py $ORG $REMOVE_FLAG
