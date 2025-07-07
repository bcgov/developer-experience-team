'''
This Python script is a working proof of concept example of using Stack Overflow APIs for Data export.
If you run into difficulties, please leave feedback in the Github Issues.
'''

# Standard library imports
import argparse
import json
import time

# Third-party library imports
import requests


def main():

    args = get_args()
    api_data = data_collector(args)
    data_exporter(api_data)


def get_args():

    parser = argparse.ArgumentParser(
        prog='so4t_data_export.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description= 'Export data from a Stack Overflow for Teams instance',
        epilog = 'Example for Stack Overflow Business: \n'
                'python3 so4t_data_export.py --url "https://stackoverflowteams.com/c/TEAM-NAME" '
                '--token "YOUR_TOKEN" \n\n'
                'Example for Stack Overflow Enterprise: \n'
                'python3 so4t_data_export.py --url "https://SUBDOMAIN.stackenterprise.co" '
                '--key "YOUR_KEY" --token "YOUR_TOKEN"\n\n')
    parser.add_argument('--url',
                        type=str,
                        help='[REQUIRED] Base URL for your Stack Overflow for Teams instance.')
    parser.add_argument('--token',
                        type=str,
                        help='[REQUIRED] API token for your Stack Overflow for Teams instance.')
    parser.add_argument('--key',
                    type=str,
                    help='API key value. Only required if using Stack Overflow Enterprise.')

    return parser.parse_args()


def data_collector(args):

    # instantiate API clients for API v2.3 and v3
    v2client = V2Client(args)
    v3client = V3Client(args)

    api_data = {}
    api_data['users'] = get_users(v2client)
    api_data['user_groups'] = v3client.get_all_user_groups()
    api_data['questions_answers_comments'] = get_questions_answers_comments(v2client, v3client)
    api_data['articles'] = get_articles(v2client)
    api_data['tags'] = get_tags(v2client, v3client)

    return api_data


def get_users(v2client):

    if v2client.soe: # Stack Overflow Enterprise requires the generation of a custom filter
        filter_attributes = [
                "user.about_me",
                "user.answer_count",
                "user.down_vote_count",
                "user.question_count",
                "user.up_vote_count",
                "user.email" # only available for Stack Overflow Enterprise
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!6WPIommaBqvsI'

    users = v2client.get_all_users(filter_string)

    return users


def get_questions_answers_comments(v2client, v3client):

    if v2client.soe: # Stack Overflow Enterprise requires the generation of a custom filter
        filter_attributes = [
            "answer.body",
            "answer.body_markdown",
            "answer.comment_count",
            "answer.comments",
            "answer.down_vote_count",
            "answer.last_editor",
            "answer.link",
            "answer.share_link",
            "answer.up_vote_count",
            "comment.body",
            "comment.body_markdown",
            "comment.link",
            "question.answers",
            "question.body",
            "question.body_markdown",
            "question.comment_count",
            "question.comments",
            "question.down_vote_count",
            "question.favorite_count",
            "question.last_editor",
            "question.notice",
            "question.share_link",
            "question.up_vote_count"
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!X9DEEiFwy0OeSWoJzb.QMqab2wPSk.X2opZDa2L'
    questions = v2client.get_all_questions(filter_string)

    # API v3 has additional question data that API v2 does not have
    additional_question_data = v3client.get_all_questions()

    # Merge question data from v2 and v3 APIs
    for question in questions:
        for question_data in additional_question_data:
            if question['question_id'] == question_data['id']:
                try:
                    question['mentioned_users'] = question_data['mentionedUsers']
                except KeyError: # no mentioned users
                    pass
                try:
                    question['mentioned_user_groups'] = question_data['mentionedUserGroups']
                except KeyError: # no mentioned user groups
                    pass
                question['is_deleted'] = question_data['isDeleted']
                question['is_obsolete'] = question_data['isObsolete']

                # Convert epoch time to human-readable format
                question['creation_date'] = question_data['creationDate']
                question['last_activity_date'] = question_data['lastActivityDate']

    return questions


def get_articles(v2client):

    if v2client.soe:
        filter_attributes = [
            "article.body",
            "article.body_markdown",
            "article.comment_count",
            "article.comments",
            "article.last_editor",
            "comment.body",
            "comment.body_markdown",
            "comment.link"
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!*Mg4Pjg9LXr9d_(v'

    articles = v2client.get_all_articles(filter_string)

    return articles


def get_tags(v2client, v3client):

    if v2client.soe: # Stack Overflow Enterprise requires the generation of a custom filter
        filter_attributes = [
            "tag.last_activity_date",
            "tag.synonyms"
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!nNPvSNMp-i'

    tags = v2client.get_all_tags(filter_string=filter_string)

    # API v3 has additional tag data that API v2 does not have
    additional_tag_data = v3client.get_all_tags()

    # Merge tag data from v2 and v3 APIs
    for tag in tags:
        tag_data_index = next(
            (index for (index, d) in enumerate(additional_tag_data) if d["name"] == tag['name']),
            None)
        if tag_data_index:
            tag_data = additional_tag_data[tag_data_index]
            tag['description'] = tag_data['description']
            tag['id'] = tag_data['id']
            tag['smes'] = v3client.get_tag_smes(tag['id']) # get subject matter experts (SMEs)

    return tags


class V2Client(object):

    def __init__(self, args):

        if not args.url:
            print("Missing required argument. Please provide a URL.")
            print("See --help for more information")
            raise SystemExit

        if "stackoverflowteams.com" in args.url:
            self.soe = False
            self.api_url = "https://api.stackoverflowteams.com/2.3"
            self.team_slug = args.url.split("https://stackoverflowteams.com/c/")[1]
            self.token = args.token
            self.api_key = None
            #Updated User-Agent
            self.headers = {
                'X-API-Access-Token': self.token,
                'User-Agent': 'so4t_data_export/1.0 (http://your-app-url.com; your-contact@email.com)'
            }
            if not self.token:
                print("Missing required argument. Please provide an API token.")
                print("See --help for more information")
                raise SystemExit
        else:
            self.soe = True
            self.api_url = args.url + "/api/2.3"
            self.team_slug = None
            self.token = None
            self.api_key = args.key
            #Updated User-Agent
            self.headers = {
                'X-API-Key': self.api_key,
                'User-Agent': 'so4t_data_export/1.0 (http://your-app-url.com; your-contact@email.com)'
            }
            if not self.api_key:
                print("Missing required argument. Please provide an API key.")
                print("See --help for more information")
                raise SystemExit

        self.ssl_verify = self.test_connection()


    def test_connection(self):

        url = self.api_url + "/tags"
        ssl_verify = True

        params = {}
        headers = {}
        if self.token:
            #Updated User-Agent
            headers = {'X-API-Access-Token': self.token, 'User-Agent': 'so4t_data_export/1.0 (http://your-app-url.com; your-contact@email.com)'}
            params['team'] = self.team_slug
        else:
            #Updated User-Agent
            headers = {'X-API-Key': self.api_key, 'User-Agent': 'so4t_data_export/1.0 (http://your-app-url.com; your-contact@email.com)'}

        print("Testing API 2.3 connection...")
        try:
            response = requests.get(url, params=params, headers=headers)
        except requests.exceptions.SSLError:
            print("SSL error. Trying again without SSL verification...")
            response = requests.get(url, params=params, headers=headers, verify=False)
            ssl_verify = False

        if response.status_code == 200:
            print("API connection successful")
            return ssl_verify
        else:
            print("Unable to connect to API. Please check your URL and API key.")
            print(response.text)
            raise SystemExit


    def get_all_articles(self, filter_string=''):

        endpoint = "/articles"
        endpoint_url = self.api_url + endpoint

        params = {
            'page': 1,
            'pagesize': 100,
        }
        if filter_string:
            params['filter'] = filter_string

        return self.get_items(endpoint_url, params)


    def get_all_questions(self, filter_string=''):

        endpoint = "/questions"
        endpoint_url = self.api_url + endpoint

        params = {
            'page': 1,
            'pagesize': 100,
        }
        if filter_string:
            params['filter'] = filter_string

        return self.get_items(endpoint_url, params)


    def get_all_tags(self, filter_string=''):

        endpoint = "/tags"
        endpoint_url = self.api_url + endpoint

        params = {
            'page': 1,
            'pagesize': 100,
        }
        if filter_string:
            params['filter'] = filter_string

        return self.get_items(endpoint_url, params)


    def get_all_users(self, filter_string=''):

            endpoint = "/users"
            endpoint_url = self.api_url + endpoint

            params = {
                'page': 1,
                'pagesize': 100,
            }
            if filter_string:
                params['filter'] = filter_string

            return self.get_items(endpoint_url, params)


    def create_filter(self, filter_attributes='', base='default'):
        # filter_attributes should be a list variable containing strings of the attributes
        # base can be 'default', 'withbody', 'none', or 'total'

        endpoint = "/filters/create"
        endpoint_url = self.api_url + endpoint

        params = {
            'base': base,
            'unsafe': False
        }

        if filter_attributes:
            # convert to semi-colon separated string
            params['include'] = ';'.join(filter_attributes)

        filter_string = self.get_items(endpoint_url, params)[0]['filter']
        print(f"Filter created: {filter_string}")

        return filter_string


    def get_items(self, endpoint_url, params={}):

        if not self.soe: # SO Basic and Business instances require a team slug in the params
            params['team'] = self.team_slug

        items = []
        while True: # Keep performing API calls until all items are received
            if params.get('page'):
                print(f"Getting page {params['page']} from {endpoint_url}")
            else:
                print(f"Getting API data from {endpoint_url}")
            response = requests.get(endpoint_url, headers=self.headers, params=params,
                                    verify=self.ssl_verify)

            if response.status_code != 200:
                # Many API call failures result in an HTTP 400 status code (Bad Request)
                # To understand the reason for the 400 error, specific API error codes can be
                # found here: https://api.stackoverflowteams.com/docs/error-handling
                print(f"/{endpoint_url} API call failed with status code: {response.status_code}.")
                print(response.text)
                print(f"Failed request URL and params: {response.request.url}")
                raise SystemExit

            items += response.json().get('items')
            if not response.json().get('has_more'): # If there are no more items, break the loop
                break

            # If the endpoint gets overloaded, it will send a backoff request in the response
            # Failure to backoff will result in a 502 error (throttle_violation)
            if response.json().get('backoff'):
                backoff_time = response.json().get('backoff') + 1
                print(f"API backoff request received. Waiting {backoff_time} seconds...")
                time.sleep(backoff_time)

            params['page'] += 1

        return items


class V3Client(object):

    def __init__(self, args):

        if not args.url:
            print("Missing required argument. Please provide a URL.")
            print("See --help for more information")
            raise SystemExit

        if not args.token:
            print("Missing required argument. Please provide an API token.")
            print("See --help for more information")
            raise SystemExit
        else:
            self.token = args.token
            #Updated User-Agent
            self.headers = {
                'Authorization': f'Bearer {self.token}',
                'User-Agent': 'so4t_data_export/1.0 (http://your-app-url.com; your-contact@email.com)'
            }

        if "stackoverflowteams.com" in args.url:
            self.team_slug = args.url.split("https://stackoverflowteams.com/c/")[1]
            self.api_url = f"https://api.stackoverflowteams.com/v3/teams/{self.team_slug}"
        else:
            self.api_url = args.url + "/api/v3"

        self.ssl_verify = self.test_connection()


    def test_connection(self):

        endpoint = "/tags"
        endpoint_url = self.api_url + endpoint
        headers = {'Authorization': f'Bearer {self.token}'}
        ssl_verify = True

        print("Testing API v3 connection...")
        try:
            response = requests.get(endpoint_url, headers=headers)
        except requests.exceptions.SSLError:
            print("SSL error. Trying again without SSL verification...")
            response = requests.get(endpoint_url, headers=headers, verify=False)
            ssl_verify = False

        if response.status_code == 200:
            print("API connection successful")
            return ssl_verify
        else:
            print("Unable to connect to API. Please check your URL and API key.")
            print(response.text)
            raise SystemExit


    def get_all_tags(self):

        method = "get"
        endpoint = "/tags"
        params = {
            'page': 1,
            'pagesize': 100,
        }
        tags = self.send_api_call(method, endpoint, params)

        return tags


    def get_all_questions(self):

        method = "get"
        endpoint = "/questions"
        params = {
            'page': 1,
            'pagesize': 100,
        }
        questions = self.send_api_call(method, endpoint, params)

        return questions


    def get_tag_smes(self, tag_id):

        method = "get"
        endpoint = f"/tags/{tag_id}/subject-matter-experts"
        smes = self.send_api_call(method, endpoint)

        return smes


    def get_all_user_groups(self):

        method = "get"
        endpoint = "/user-groups"
        params = {
            'page': 1,
            'pagesize': 100,
        }
        user_groups = self.send_api_call(method, endpoint, params)

        return user_groups


    def send_api_call(self, method, endpoint, params={}):

        get_response = getattr(requests, method, None)
        endpoint_url = self.api_url + endpoint
        headers = {'Authorization': f'Bearer {self.token}'}

        data = []
        while True:
            if method == 'get':
                response = get_response(endpoint_url, headers=headers, params=params,
                                        verify=self.ssl_verify)
            else:
                response = get_response(endpoint_url, headers=headers, json=params,
                                        verify=self.ssl_verify)

            # check for rate limiting thresholds
            # print(response.headers)
            if response.status_code not in [200, 201, 204]:
                print(f"API call to {endpoint_url} failed with status code {response.status_code}")
                print(response.text)
                raise SystemExit

            try:
                json_data = response.json()
            except json.decoder.JSONDecodeError: # some API calls do not return JSON data
                print(f"API request successfully sent to {endpoint_url}")
                return

            if type(params) == dict and params.get('page'): # check request for pagination
                print(f"Received page {params['page']} from {endpoint_url}")
                data += json_data['items']
                if params['page'] == json_data['totalPages']:
                    break
                params['page'] += 1
            else:
                print(f"API request successfully sent to {endpoint_url}")
                data = json_data
                break

        return data


def data_exporter(api_data):

    for data_name, data in api_data.items():
        export_to_json(data_name, data)


def export_to_json(data_name, data):

    file_name = data_name + '.json'

    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)

    print(f'JSON file created: {file_name}')


if __name__ == '__main__':

    main()
