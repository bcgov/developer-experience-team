# Stack Overflow for Teams Utilities

This directory contains various utilities for working with Stack Overflow for Teams data.

## Stack Overflow for Teams Data Export (so4t_data_export.py)
An API script for Stack Overflow for Teams that creates a JSON export of users, user groups, tags, articles, questions, answers, and comments. It uses a combination of both versions of the API (i.e., 2.3 and 3) in order to create the most comprehensive export possible.


### Requirements
* A Stack Overflow for Teams instance (Basic, Business, or Enterprise)
* Python 3.x ([download](https://www.python.org/downloads/))
* Operating system: Linux, MacOS, or Windows

### Setup
[Download](https://github.com/StackExchange/so4t_data_export/archive/refs/heads/main.zip) and unpack the contents of this repository

**Installing Dependencies**

* Open a terminal window (or, for Windows, a command prompt)
* Navigate to the directory where you unpacked the files
* Install the dependencies: `pip3 install -r requirements.txt`

**API Authentication**

You'll need an API token for the basic and business tiers. You'll need to obtain an API key and an API token for Enterprise.

* For Basic or Business, instructions for creating a personal access token (PAT) can be found in [this KB article](https://stackoverflow.help/en/articles/4385859-stack-overflow-for-teams-api).
* For Enterprise, documentation for creating the key and token can be found within your instance at this url: `https://[your_site]/api/docs/authentication`

Creating an access token for Enterprise can sometimes be tricky for people who haven't done it before. Here are some (hopefully) straightforward instructions:
* Go to the page where you created your API key. Take note of the "Client ID" associated with your API key.
* Go to the following URL, replacing the base URL, the `client_id`, and the base URL of the `redirect_uri` with your own:
`https://YOUR.SO-ENTERPRISE.URL/oauth/dialog?client_id=111&redirect_uri=https://YOUR.SO-ENTERPRISE.URL/oauth/login_success`
* You may be prompted to log in to Stack Overflow Enterprise if you're not already. Either way, you'll be redirected to a page that simply says "Authorizing Application."
* In the URL of that page, you'll find your access token. Example: `https://YOUR.SO-ENTERPRISE.URL/oauth/login_success#access_token=YOUR_TOKEN`

### Usage
In a terminal window, navigate to the directory where you unpacked the script. 
Run the script using the following format, replacing the URL, token, and/or key with your own:
* For Basic and Business: `python3 so4t_data_export.py --url "https://stackoverflowteams.com/c/TEAM-NAME" --token "YOUR_TOKEN"`
* For Enterprise: `python3 so4t_data_export.py --url "https://SUBDOMAIN.stackenterprise.co" --key "YOUR_KEY" --token "YOUR_TOKEN"`

The script can take several minutes to run, particularly as it gathers data via the API. As it runs, it will update the terminal window with the tasks it performs.

When the script completes, it will indicate the JSON files will be created in the same directory where the script is located. The files will be named articles.json, questions_answers_comments.json, tags.json, user_groups.json, and users.json.

### Known Limitations
* Images are not exported
* Collections and Communities do not have an API endpoint, so they are not exported

### Support, security, and legal
If you encounter problems using the script, please leave feedback in the Github Issues. You can also clone and change the script to suit your needs. It is provided as-is, with no warranty or guarantee of any kind.

All data obtained via the API is handled locally on the device from which the script is run. The script does not transmit data to other parties like Stack Overflow. All API calls performed are read-only, so there is no risk of editing or adding content to your Stack Overflow for Teams instance.

## Stack Overflow Data Analysis (so_explore.py)
A utility script that uses DuckDB to run SQL queries against the JSON data exported by so4t_data_export.py. This tool helps analyze Stack Overflow content by enabling queries on tags, questions, answers, users, and other exported data.

### Requirements
* Python 3.x
* Dependencies listed in requirements.txt

### Setup
Install the required dependencies:
```
pip install -r requirements.txt
```

### Usage
The script contains several pre-written SQL queries for analyzing the Stack Overflow data. By default, it runs a query that shows tag names, counts, and age since last activity. You can modify the script to uncomment or add different queries for various types of analysis.

Examples of analyses you can perform:
- Count questions per user
- View answers for specific questions
- Count answers per user
- Analyze tag usage and activity

To use the script:
1. Place the script in the same directory as your exported JSON files
2. Edit the script to uncomment/modify the queries you want to run
3. Run the script: `python so_explore.py`

## Stack Overflow to GitHub Discussion Migration (populate_discussion.py)
A script that helps migrate Stack Overflow content to GitHub Discussions. It creates labels in GitHub repositories based on Stack Overflow tags and transfers Stack Overflow questions and answers to GitHub Discussions format.

### Requirements
* Python 3.x
* Dependencies listed in requirements.txt
* GitHub App with appropriate permissions (Contents, Discussions, Metadata)

### Setup
1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set up GitHub App authentication by setting these environment variables:
   ```
   export GHD_INSTALLATION_ID=your_installation_id
   export GHD_APP_ID=your_github_app_id
   export GHD_PRIVATE_KEY=/path/to/your/private-key.pem
   ```

### Usage
```
python populate_discussion.py --repo OWNER/REPO --category CATEGORY_NAME [options]
```

#### Parameters
- `--repo` (required): GitHub repository in format owner/name
- `--category` (required): GitHub Discussion category name to post to
- `--questions-file`: Path to questions JSON file (default: questions_answers_comments.json)
- `--tags-file`: Path to tags JSON file (default: tags.json)
- `--limit`: Limit number of questions to process
- `--image-folder`: Path to local folder containing images (default: discussion_images_temp)
- `--clean`: Delete all discussions, comments, and labels before import
- `--clean-only`: Delete all discussions, comments, and labels, then exit
- `--clean-category`: Used with --category and --clean or --clean-only to delete discussions in the specified category only

#### Example
```
python populate_discussion.py --repo bcgov/developer-experience-team --category Q&A --limit 10
```

#### Clean Operations
To clean discussions in a specific category before importing:
```
python populate_discussion.py --repo bcgov/developer-experience-team --category Q&A --clean --clean-category
```

To clean all discussions and exit:
```
python populate_discussion.py --repo bcgov/developer-experience-team --category Q&A --clean-only
```

### Features
- Converts Stack Overflow questions and answers to GitHub Discussions
- Creates GitHub labels based on Stack Overflow tags
- Preserves original author information and timestamps
- Handles comments on both questions and answers
- Supports image migration when used with so_export_images.py

## Stack Overflow Image Exporter (so_export_images.py)
A utility to download and save images from Stack Overflow posts. This script extracts image URLs from both markdown and HTML content in Stack Overflow posts and downloads them to a local directory, addressing the limitation that images are not included in the standard data export.

### Requirements
* Python 3.x
* Dependencies listed in requirements.txt

### Setup
Install the required dependencies:
```
pip install -r requirements.txt
```

### Usage
```
python so_export_images.py --api-base-url API_BASE_URL [options]
```

#### Parameters
- `--api-base-url` (required): Stack Overflow for Teams API base URL (e.g., https://stackoverflow.developer.gov.bc.ca/api/v3)
- `--input`: Input JSON file (default: questions_answers_comments.json)
- `--output`: Output folder for images (default: so_exported_images)
- `--token`: API token for authentication (if required)

#### Example
```
python so_export_images.py --api-base-url https://stackoverflow.developer.gov.bc.ca/api/v3 --token YOUR_TOKEN
```

### Features
- Extracts image URLs from question and answer content
- Supports both markdown and HTML image formats
- Downloads images to a local folder
- Preserves original filenames
- Can be used in conjunction with populate_discussion.py for complete content migration
