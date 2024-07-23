import asyncio

from azure.identity import InteractiveBrowserCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.reference_create import ReferenceCreate
import sys

from msgraph.generated.users.users_request_builder import UsersRequestBuilder


async def find_user_by_email(client, email):
	query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
		filter=f"mail eq '{email}'",
	)

	request_configuration = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
		query_parameters=query_params,
	)

	users = await client.users.get(request_configuration=request_configuration)
	if users:
		return users.value


async def find_user_by_user_principal(client, email):
	return await client.users.by_user_id(email).get()


async def main():
	credential = InteractiveBrowserCredential()
	client = GraphServiceClient(credentials=credential)

	for line in sys.stdin:
		user_email = line.strip()
		user_found = False
		try:
			user = await find_user_by_user_principal(client, user_email)

			if user:
				user_found = True

		except Exception as e:
			users = await find_user_by_email(client, user_email)
			if users:
				for user in users:
					if user.mail == user_email:
						user_found = True

		print(f"{user_email}, {user_found}")


asyncio.run(main())
