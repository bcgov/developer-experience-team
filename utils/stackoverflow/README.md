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
- `--id-mapping`: Path to JSON file mapping user_id to github_login
- `--limit`: Limit number of questions to process
- `--image-folder`: Path to local folder containing images (default: discussion_images_temp)
- `--clean`: Delete all discussions, comments, and labels before import
- `--clean-only`: Delete all discussions, comments, and labels, then exit
- `--clean-category`: Used with --category and --clean or --clean-only to delete discussions in the specified category only
- `--api-delay`: Minimum seconds between API calls (default: 1.0)
- `--ignore-tags`: List of tags to ignore (space-separated). Questions tagged with these tag(s) will not be processed.
- `--tag-min-threshold`: Minimum number of questions a tag must be associated with to be considered for label creation (default: 1)
- `--popular-tag-min-threshold`: Minimum number of views a question must have in SO for the `popular-in-so` label to be applied to it (default: 200)

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

## Extract Questions Script (extract_questions.py)
A utility script that extracts specific questions from `questions_answers_comments.json` based on question IDs. It's particularly useful for re-processing questions that failed during `populate_discussion.py` runs due to timeout issues.

### Requirements
* Python 3.x
* A questions_answers_comments.json file (generated by so4t_data_export.py)

### Usage

#### Method 1: Command Line IDs
```bash
python extract_questions.py --ids 1354 1320 1321 --output failed_questions.json
```

#### Method 2: File with IDs
```bash
python extract_questions.py --file failed_ids.txt --output retry_questions.json
```

#### Method 3: Custom Input File
```bash
python extract_questions.py --input backup_questions.json --ids 1354 --output single_question.json
```

### File Format for Question IDs

Create a text file with one question ID per line:
```
# Failed question IDs from populate_discussion.py run
# Lines starting with # are ignored

1354
1320
1321
1285
```

### Features

- ✅ Preserves complete JSON structure (questions, answers, comments)
- ✅ Reports missing question IDs
- ✅ Removes duplicate IDs automatically  
- ✅ Shows progress and summary statistics
- ✅ Supports comments in ID files (lines starting with #)
- ✅ Validates input/output files

### Output

The script will:
1. Show which questions were found
2. Warn about any missing question IDs
3. Create a new JSON file with the extracted questions
4. Display summary statistics

### Integration with populate_discussion.py

Use the extracted JSON file as input to retry failed questions:
```bash
python populate_discussion.py --repo owner/repo --category "Q&A" --questions-file retry_questions.json
```

## Log File Merging (merge_so2ghd_files.py)
A utility script for merging Stack Overflow to GitHub Discussions (so2ghd) redirect log files. This tool is particularly useful when you need to combine multiple migration runs or update existing redirect mappings with new entries.

### Purpose
During Stack Overflow migrations, redirect log files are created that map Stack Overflow URLs to their corresponding GitHub Discussion URLs. This script allows you to:
- Merge redirect logs from multiple migration runs
- Update existing redirects with new URLs
- Combine partial migration logs into a complete redirect file

### Requirements
* Python 3.x
* Both base and patch log files must exist
* Log files should contain redirect entries in the format: `redir /path https://github.com/org/repo/discussions/### permanent`

### Usage
```
python merge_so2ghd_files.py --base-file BASE_LOG --patch-file PATCH_LOG --new-file OUTPUT_LOG
```

#### Parameters
- `--base-file` (required): Path to the base log file (existing redirects)
- `--patch-file` (required): Path to the patch log file (new/updated redirects) 
- `--new-file` (required): Path to the output merged log file

#### Examples

**Basic merge of two redirect logs:**
```bash
python merge_so2ghd_files.py --base-file migration_run1.log --patch-file migration_run2.log --new-file combined_redirects.log
```

**Merge multiple partial migration logs:**
```bash
# First merge
python merge_so2ghd_files.py --base-file questions_redirects.log --patch-file answers_redirects.log --new-file temp_merge.log

# Second merge  
python merge_so2ghd_files.py --base-file temp_merge.log --patch-file comments_redirects.log --new-file complete_redirects.log
```

### File Format
Both input and output files should contain redirect entries in this format:
```
redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent
redir /a/1203 https://github.com/org/repo/discussions/2810#discussioncomment-13836210 permanent
redir /questions/1201/1202 https://github.com/org/repo/discussions/2809#discussioncomment-13836211 permanent
```

### Merge Behavior
- **Overwrite Policy**: If the same path exists in both files, the patch file entry overwrites the base file entry
- **Addition Policy**: New paths from the patch file are added to the output
- **Validation**: Only valid redirect lines (4+ tokens starting with "redir") are processed
- **Error Handling**: Invalid lines are logged as warnings and skipped

### Output
The script provides detailed feedback including:
- File validation (checks that input files exist)
- Merge completion confirmation
- Warning messages for any invalid redirect lines encountered

### Integration with Other Tools
This script is commonly used in conjunction with:
- `populate_discussion.py`: Creates the initial redirect logs during migration
- **Caddy Server Configuration**: Output files can be used directly in Caddy rewrite rules

## Label Management (delete_all_labels.py)
A utility script for deleting all labels in a GitHub repository. This tool is particularly useful for cleaning up repositories after Stack Overflow migrations or when you need to reset repository labels completely.

### Requirements
* Python 3.x
* Dependencies listed in requirements.txt
* GitHub App with appropriate permissions (Contents, Metadata)

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
python delete_all_labels.py --repo OWNER/REPO [options]
```

#### Parameters
- `--repo` (required): GitHub repository in format owner/name
- `--api-delay`: Minimum seconds between API calls (default: 1.0)
- `--dry-run`: Show what would be deleted without actually deleting
- `--force`: Skip confirmation prompt 

#### Examples

**Preview what would be deleted (recommended first step):**
```bash
python delete_all_labels.py --repo bcgov/developer-experience-team --dry-run
```

**Delete all labels with confirmation:**
```bash
python delete_all_labels.py --repo bcgov/developer-experience-team
```

**Delete all labels without confirmation (for living dangerously):**
```bash
python delete_all_labels.py --repo bcgov/developer-experience-team --force
```

**Delete with custom API delay:**
```bash
python delete_all_labels.py --repo bcgov/developer-experience-team --api-delay 2.0
```


### Output
The script provides detailed feedback including:
- Total number of labels found
- Preview of labels to be deleted (first 10 shown)
- Progress updates during deletion
- Summary of successful and failed deletions
- All operations logged to `delete_labels.log`

### Safety Warnings
⚠️ **DESTRUCTIVE OPERATION**: This script permanently deletes all labels from the specified repository. This action cannot be undone.

**Best Practices:**
1. Always run with `--dry-run` first to preview changes
2. Ensure you have backups or can recreate labels if needed
3. Use `--force` only in automated scripts where confirmation isn't possible
4. Monitor the logs for any failures during bulk operations

## URL Validation with Playwright (validate_urls_playwright.py)
A browser-based URL validation tool that checks if URLs return HTTP 301 redirects. This script is used for validating redirects to GitHub that require SSO authentication, which cannot be tested programmatically with standard HTTP libraries.

### Requirements
* Python 3.x
* Dependencies listed in requirements.txt (includes Playwright)
* Browser support (Chromium/Chrome will be installed automatically by Playwright)

### Setup
1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Install Playwright browsers (one-time setup):
   ```
   playwright install chromium
   ```

### Usage
```
python validate_urls_playwright.py --file URL_FILE [options]
```

#### Parameters
- `--file` (required): Path to file containing URLs to validate (one URL per line)
- `--org`: GitHub organization name for SSO testing (e.g., bcgov, mycompany)
- `--delay`: Delay in seconds between requests (default: 1.0)

#### Examples

**Basic URL validation:**
```bash
python validate_urls_playwright.py --file sample_urls.txt
```

**Validate URLs requiring GitHub organization SSO:**
```bash
python validate_urls_playwright.py --file sample_urls.txt --org bcgov
```

**Custom delay between requests:**
```bash
python validate_urls_playwright.py --file sample_urls.txt --org mycompany --delay 2.0
```

### Authentication Workflow
The script uses a two-step authentication process:

1. **GitHub Login**: Opens a browser window for manual GitHub authentication
   - Enter username/password
   - Complete 2FA if required
   - Wait for confirmation at GitHub homepage

2. **SSO Authentication** (if `--org` specified): Tests organization access
   - Navigates to the specified GitHub organization
   - Handles Microsoft SSO redirects automatically
   - Prompts for manual SSO completion if required

### URL File Format
Create a text file with one URL per line. Comments (lines starting with #) are ignored:
Column 1 = URL to redirect
Column 2 = Expected new url
```
# Test URLs for redirects
https://example.org/old-name,https://another.org/new-name,
https://example.org/another-rename,https://another.org/another-rename
https://example.org/something/migrated-project,https://another.org/something/migrated-project2
```

### Output
The script provides detailed feedback including:
- Authentication status and SSO completion
- Per-URL validation results with redirect chains
- Summary statistics (total processed, valid 301s, failures)
- Error messages for failed validations



