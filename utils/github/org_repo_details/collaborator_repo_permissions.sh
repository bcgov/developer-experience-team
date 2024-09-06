#!/bin/zsh

jq -r '.[] | . as $r | .collaborators[] as $c  | "\($r.repo_name), \($r.archived), \($r.disabled), \($r.has_admin), \($r.has_member_admin),  \($r.has_admin_team), \($r.has_workflows), \($r.has_webhooks), \($r.has_linked_collaborator), \($r.updated_at), \($c.login), \($c.is_member),  \($c.association_type), \($c.role_name)"' repo_collaboration_details6.json  | sort > collab_repo_permissions6.csv
