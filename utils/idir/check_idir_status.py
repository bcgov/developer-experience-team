import asyncio

from azure.identity import InteractiveBrowserCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.reference_create import ReferenceCreate
from github import Github, Auth

import sys, os, re, datetime, argparse


from msgraph.generated.users.users_request_builder import UsersRequestBuilder

def remove_github_user_from_org(github_client, github_id, org_name):
    org = github_client.get_organization(org_name)
    try:
        user = github_client.get_user(github_id)
        if user:
            org.remove_from_members(user)
            return True
        else:
            print(f"User {github_id} not found in  {org_name}.")
            return False
    except Exception as e:
        print(f"Error removing {github_id} from {org_name}: {e}")
        return False

async def search(client, email):
    query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(search=[f'("mail:{email}" OR "userPrincipalName:{email}" OR "otherMails:{email}")'], select=["id", "displayName", "userPrincipalName", "mail", "otherMails"],
                                                                             )

    request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=query_params,
    )

    request_configuration.headers.add("ConsistencyLevel", "eventual")

    users = await client.users.get(request_configuration=request_configuration)
    if users:
        return users.value

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Correlate GitHub SSO identity in a GitHub organization with Entra ID accounts and optionally remove users from the organization.")
    parser.add_argument("org", help="GitHub organization name")
    parser.add_argument("-r","--remove", help="Whether to remove users from a GitHub organization when there is no Entra ID account matching their GitHub SSO identity.", action="store_true")
    args = parser.parse_args()

    # Map command line arguments to local variables
    remove_unmatched_users = args.remove
    github_org = args.org

    # authenticate with Graph API in order to search for users in Entra ID
    credential = InteractiveBrowserCredential()
    client = GraphServiceClient(credentials=credential)

    # authenticate with GitHub API
    auth = Auth.Token(os.environ['GITHUB_TOKEN'])
    github_client = Github(auth=auth)

    # read records from stdin, where each represent a GitHub user in the the organization
    for line in sys.stdin:
        line_parts = line.strip().split(",")
        user_email = line_parts[0].strip('\"')
        github_id = line_parts[1].strip('\"')

        removed_from_org = False
        message = ""
        has_idir = False

        if user_email:
            # check if user_email is an email address using regex
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_email):
                message = "Unexpected NameID format."
            else:
                users = await search(client, user_email)

                if not users:
                    has_idir = False
                    if remove_unmatched_users:
                        removed_from_org = remove_github_user_from_org(github_client, github_id, github_org)
                        message = "Removed."
                    else:
                        message = "Dry run - not removed."

                else:
                    has_idir = True
        else:
            user_email = "NO EMAIL??!!"
            message = "NameID is empty."

        if not has_idir:
            print(f"{datetime.datetime.today().strftime('%d-%m-%Y')}, {github_org}, {user_email}, {github_id}, {has_idir}, {removed_from_org},,{message}")

asyncio.run(main())
