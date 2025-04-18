#!/bin/zsh
 ORG=$1
 REMOVE=$2

# Check if the org name is provided
if [ -z "$ORG" ]; then
  echo "Usage: $0 <org_name> [remove]"
  exit 1
fi

# Check if remove flag is provided. If it is, set REMOVE_FLAG to "-r" otherwise set it to an empty string
if [ "$REMOVE"=="remove" ]; then
  REMOVE_FLAG="-r"
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
