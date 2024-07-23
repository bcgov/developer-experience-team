import asyncio

from azure.identity import InteractiveBrowserCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.reference_create import ReferenceCreate

credential = InteractiveBrowserCredential()

client = GraphServiceClient(credentials=credential)


async def add_user_to_group(email, group_id):
	user = await client.users.by_user_id(email).get()
	if user:
		print("Found user.")

		request_body = ReferenceCreate(
			odata_id=f'https://graph.microsoft.com/v1.0/directoryObjects/{user.id}',
		)
		print("Created Reference.")
		print(request_body)

		await client.groups.by_group_id(group_id).members.ref.post(request_body)

	else:
		raise


async def main():
	await add_user_to_group("<EMAIL_OF_USER_TO_ADD>", "<GROUP ID FROM AZURE/ENTRA ID>")

asyncio.run(main())
