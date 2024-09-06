import os
import sys
import json
from typing import Any

from rocketchat_API.rocketchat import RocketChat

rc_user_id = os.getenv("RC_USER_ID")
rc_auth_token = os.getenv("RC_AUTH_TOKEN")

if not (rc_user_id or rc_auth_token):
	sys.exit("Please set environment variables 'RC_USER_ID' and 'RC_AUTH_TOKEN' in order to run this tool.")

rocket = RocketChat(user_id=rc_user_id, auth_token=rc_auth_token,
					server_url='https://chat.developer.gov.bc.ca')

current_offset = 0
limit = 5000
users_cache: list[Any] = []

while len(users_cache) < limit:
	response_data = rocket.users_list(offset=current_offset, count=100).json()
	users_cache.extend(response_data['users'])
	limit = response_data['total']
	current_offset = len(users_cache)
#
print(json.dumps(users_cache))
