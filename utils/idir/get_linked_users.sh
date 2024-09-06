#!/bin/zsh

 gh api graphql --paginate -F org=bcgov -f query='query($org: String!, $endCursor:String) {
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
}' | jq -r '.data.organization.samlIdentityProvider.externalIdentities.edges[] | [.node.samlIdentity.nameId, .node.user.login] | @csv'
