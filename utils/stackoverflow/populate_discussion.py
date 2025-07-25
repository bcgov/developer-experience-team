import json
import os
import logging
import argparse
from github import Github, Auth
from github.GithubException import GithubException
from typing import Dict, List, Any, Optional
import re
from urllib.parse import urlparse
import html
from collections import namedtuple
from datetime import datetime, timezone, timedelta
from populate_discussion_helpers import RateLimiter, GitHubAuthManager, GraphQLHelper
from enum import StrEnum


# Get logger for this module
logger = logging.getLogger(__name__)

# Get URL mapping logger (but don't configure it unless we're the main script)
url_mapping_logger = logging.getLogger('url_mapping')

Category = namedtuple('Category', ['id', 'name'])
class MetaAction(StrEnum):
    ANSWERED = "answered"
    ASKED = "asked"
    COMMENTED = "commented on"

# Setup logging - only when running as main script
def setup_populate_discussion_logging():
    """Setup logging for populate_discussion.py when run as main script."""
    # Configure root logger to handle all modules
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_file_handler = logging.FileHandler('populate_discussion.log')
    logger_file_handler.setFormatter(formatter)
    logger_console_handler = logging.StreamHandler()
    logger_console_handler.setFormatter(formatter)
    root_logger.addHandler(logger_file_handler)
    root_logger.addHandler(logger_console_handler)

    # Setup URL mapping logger
    url_mapping_logger = logging.getLogger('url_mapping')
    url_mapping_logger.setLevel(logging.INFO)
    url_mapping_handler = logging.FileHandler(datetime.now().strftime('so2ghd_%d_%m_%Y_%H_%M_.log'))
    url_mapping_formatter = logging.Formatter('%(message)s')
    url_mapping_handler.setFormatter(url_mapping_formatter)
    url_mapping_logger.addHandler(url_mapping_handler)
    url_mapping_logger.propagate = False  # Prevent messages from going to root logger

def load_json(filename: str) -> List[Dict[str, Any]]:
    """Load and parse a JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        raise

def get_labels(repo):
    """Get all labels in the repository"""
    return {label.name: label for label in repo.get_labels()}

def create_label(repo, name: str, description: str = None):
    """Create a new label in the repository, ensuring description is < 100 chars"""
    if description and len(description) > 100:
        description = description[:97] + '...'
    try:
        repo.create_label(name=name, color="ededed", description=description)
        logger.info(f"Created label: {name}")
        return True
    except GithubException as e:
        logger.warning(f"Could not create label {name}. Error: {e}")
        return False


def get_category_id(github_graphql, owner: str, name: str, category_name: str):
    """Get the ID of a discussion category by name using GraphQL via PyGitHub"""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussionCategories(first: 50) {
          nodes {
            id
            name
          }
        }
      }
    }
    """
    variables = {
        'owner': owner,
        'name': name
    }
    data = github_graphql.github_graphql_request(query, variables)
    categories = data['repository']['discussionCategories']['nodes']
    for category in categories:
        if category['name'] == category_name:
            return category['id']
    raise ValueError(f'Category {category_name} not found')

def get_repo_node_id(github_graphql, owner: str, name: str):
    """Fetch the repository node_id using a GraphQL query."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
      }
    }
    """
    variables = {'owner': owner, 'name': name}
    data = github_graphql.github_graphql_request(query, variables)
    return data['repository']['id']

def get_label_node_ids(github_graphql, owner: str, name: str, label_names: List[str]) -> List[str]:
    """Fetch label node IDs for the given label names via GraphQL (case-insensitive, strip whitespace, paginated)."""
    if not label_names:
        return []
    all_labels = []
    has_next_page = True
    end_cursor = None
    while has_next_page:
        query = """
        query($owner: String!, $name: String!, $after: String) {
          repository(owner: $owner, name: $name) {
            labels(first: 100, after: $after) {
              nodes {
                name
                id
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """
        variables = {'owner': owner, 'name': name, 'after': end_cursor}
        data = github_graphql.github_graphql_request(query, variables)
        label_data = data['repository']['labels']
        all_labels.extend(label_data['nodes'])
        has_next_page = label_data['pageInfo']['hasNextPage']
        end_cursor = label_data['pageInfo']['endCursor']
    name_to_id = {l['name'].strip().lower(): l['id'] for l in all_labels}
    node_ids = []
    for label in label_names:
        key = label.strip().lower()
        if key in name_to_id:
            node_ids.append(name_to_id[key])
        else:
            logger.warning(f"Label '{label}' not found in repo, skipping. Available labels: {list(name_to_id.keys())}")
    return node_ids

def add_labels_to_discussion(github_graphql, discussion_node_id: str, label_node_ids: List[str]):
    """Add labels to a discussion using addLabelsToLabelable mutation."""
    if not label_node_ids:
        return
    mutation = """
    mutation($labelableId: ID!, $labelIds: [ID!]!) {
      addLabelsToLabelable(input: {labelableId: $labelableId, labelIds: $labelIds}) {
        labelable {
          ... on Discussion {
            id
          }
        }
      }
    }
    """
    variables = {
        'labelableId': discussion_node_id,
        'labelIds': label_node_ids
    }
    github_graphql.github_graphql_request(mutation, variables)

def create_discussion(github_graphql, owner, name, title: str, body: str, category_id: str, labels_list: List[str]):
    """Create a new discussion using GraphQL, then add labels via addLabelsToLabelable."""
    mutation = """
    mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {
        repositoryId: $repositoryId,
        categoryId: $categoryId,
        title: $title,
        body: $body
      }) {
        discussion {
          id
          number
          url
        }
      }
    }
    """
    repo_node_id = get_repo_node_id(github_graphql, owner, name)
    variables = {
        'repositoryId': repo_node_id,
        'categoryId': category_id,
        'title': title,
        'body': body
    }
    data = github_graphql.github_graphql_request(mutation, variables)
    discussion = data['createDiscussion']['discussion']
    discussion_number = discussion['number']
    discussion_node_id = discussion['id']
    discussion_url = discussion['url']
    logger.info(f"Created discussion #{discussion_number}: {title}")
    if labels_list:
        label_node_ids = get_label_node_ids(github_graphql, owner, name, labels_list)
        add_labels_to_discussion(github_graphql, discussion_node_id, label_node_ids)
    return discussion_number, discussion_url

def add_comment(github_graphql, owner: str, name: str, discussion_number: int, body: str, reply_to_id: Optional[str] = None):
    """Add a comment to an existing discussion using GraphQL via requests. Returns the comment node ID if successful, else None."""
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        discussion(number: $number) {
          id
        }
      }
    }
    """
    variables = {
        'owner': owner,
        'name': name,
        'number': discussion_number
    }
    data = github_graphql.github_graphql_request(query, variables)
    discussion_id = data['repository']['discussion']['id']
    mutation = """
    mutation($discussionId: ID!, $body: String!, $replyToId: ID) {
      addDiscussionComment(input: {
        discussionId: $discussionId,
        body: $body,
        replyToId: $replyToId
      }) {
        comment {
          id
          url
        }
      }
    }
    """
    variables = {
        'discussionId': discussion_id,
        'body': body,
        'replyToId': reply_to_id
    }
    data = github_graphql.github_graphql_request(mutation, variables)
    logger.info(f"Added comment to discussion #{discussion_number}")
    return data['addDiscussionComment']['comment']['id'], data['addDiscussionComment']['comment']['url']

def find_discussion_by_title(github_graphql, owner: str, name: str, title: str, category: Optional[Category] = None):
    """Return discussion_node_id if a discussion with the given title exists, else None."""
    if category:
        logger.info(f"Searching for discussion in category '{category.name}'")
    else:
        logger.info("Searching for discussion in all categories")
    has_next_page = True
    end_cursor = None
    while has_next_page:
      query = """
      query($owner: String!, $name: String!, $after: String, $categoryId: ID) {
        repository(owner: $owner, name: $name) {
          discussions(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: DESC}, categoryId: $categoryId) {
            nodes {
              id
              title
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
      """
      variables = {'owner': owner, 'name': name, 'after': end_cursor, 'categoryId': category.id if category else None}
      data = github_graphql.github_graphql_request(query, variables)
      discussions = data['repository']['discussions']['nodes']
      logger.debug(f"Found {len(discussions)} discussions in repository '{owner}/{name}'")
      for d in discussions:
          if d['title'].strip() == title.strip():
              return d['id']
      has_next_page = data['repository']['discussions']['pageInfo']['hasNextPage']
      end_cursor = data['repository']['discussions']['pageInfo']['endCursor']
    return None

def clean_repo_discussions(github_graphql, owner: str, name: str, category: Optional[Category] = None):
    """Delete all discussions, their comments, and unlabel them from the repo. Optionally filter by category."""

    if not category:
        logger.warning("Cleaning all discussions, comments, and labels from the repository!")
    else:
        logger.warning(f"Cleaning discussions in category '{category.name}', comments, and labels from the repository!")

    has_next_page = True
    end_cursor = None
    while has_next_page:
        query = """
        query($owner: String!, $name: String!, $after: String, $categoryId: ID) {
          repository(owner: $owner, name: $name) {
            discussions(first: 50, after: $after, categoryId: $categoryId) {
              nodes {
                id
                number
                title
                comments(first: 100) {
                  nodes {
                    id
                  }
                }
                labels(first: 100) {
                  nodes {
                    id
                  }
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """
        variables = {'owner': owner, 'name': name, 'after': end_cursor, 'categoryId': category.id if category else None}
        data = github_graphql.github_graphql_request(query, variables)
        repo = data['repository']
        discussions = repo['discussions']['nodes']
        for d in discussions:
            discussion_id = d['id']
            label_ids = [l['id'] for l in d['labels']['nodes']]
            if label_ids:
                mutation = """
                mutation($labelableId: ID!, $labelIds: [ID!]!) {
                  removeLabelsFromLabelable(input: {labelableId: $labelableId, labelIds: $labelIds}) {
                    clientMutationId
                  }
                }
                """
                variables_rm = {'labelableId': discussion_id, 'labelIds': label_ids}
                github_graphql.github_graphql_request(mutation, variables_rm)
            for c in d['comments']['nodes']:
                comment_id = c['id']
                mutation = """
                mutation($id: ID!) {
                  deleteDiscussionComment(input: {id: $id}) {
                    clientMutationId
                  }
                }
                """
                variables_del = {'id': comment_id}
                github_graphql.github_graphql_request(mutation, variables_del)
            mutation = """
            mutation($id: ID!) {
              deleteDiscussion(input: {id: $id}) {
                clientMutationId
              }
            }
            """
            variables_del = {'id': discussion_id}
            github_graphql.github_graphql_request(mutation, variables_del)
        has_next_page = repo['discussions']['pageInfo']['hasNextPage']
        end_cursor = repo['discussions']['pageInfo']['endCursor']

def extract_image_urls(text):
    """Extract image URLs from markdown and HTML image tags."""
    # Markdown: ![alt](url)
    md_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
    # HTML: <img src="url" ...>
    html_pattern = r'<img [^>]*src=["\']([^"\'>]+)["\']'
    urls = re.findall(md_pattern, text or '')
    urls += re.findall(html_pattern, text or '')
    return urls

def ensure_discussion_images_folder(repo):
    """Ensure the discussion_images folder exists in the repo. Creates it if missing."""
    try:
        repo.get_contents('discussion_images')
    except Exception:
        repo.create_file('discussion_images/.gitkeep', 'create discussion_images folder', '', branch='main')

def commit_image_to_repo(repo, local_path):
    """Commit a local image file to the discussion_images folder in the repo. Returns the repo path."""
    with open(local_path, 'rb') as f:
        content = f.read()
    filename = os.path.basename(local_path)
    repo_path = f'discussion_images/{filename}'
    # Check if file exists
    try:
        existing = repo.get_contents(repo_path)
        repo.update_file(repo_path, f'update {repo_path}', content, existing.sha, branch='main')
    except Exception:
        repo.create_file(repo_path, f'add {repo_path}', content, branch='main')
    return repo_path

def replace_image_urls(text, url_map):
    """Replace image URLs in markdown/html with new repo paths."""
    def md_repl(match):
        url = match.group(1)
        return match.group(0).replace(url, url_map.get(url, url))
    def html_repl(match):
        url = match.group(1)
        return match.group(0).replace(url, url_map.get(url, url))
    text = re.sub(r'!\[[^\]]*\]\(([^)]+)\)', md_repl, text or '')
    text = re.sub(r'<img [^>]*src=["\']([^"\'>]+)["\']', html_repl, text)
    return text

def decode_html_entities(text: str) -> str:
    """Decode HTML entities like &#39; to their proper characters."""
    if not text:
        return text
    return html.unescape(text)

def process_image_fields(text, local_image_folder, owner, name, repo, logger):
    """Extract image URLs, upload local images to GitHub, and replace URLs in the text."""
    # Decode HTML entities first
    text = decode_html_entities(text)
    img_urls = extract_image_urls(text)
    url_map = {}
    for url in img_urls:
        filename = os.path.basename(url)
        local_path = os.path.join(local_image_folder, filename)
        if os.path.exists(local_path):
            repo_path = commit_image_to_repo(repo, local_path)
            url_map[url] = f'https://github.com/{owner}/{name}/blob/main/{repo_path}?raw=true'
        else:
            logger.warning(f"Local image not found for URL {url}, skipping upload.")
    return replace_image_urls(text, url_map)

def get_url_redir_str(stackoverflow_url: str, github_discussion_url: str):
    parsed_url = urlparse(stackoverflow_url)
    redirect_path = parsed_url.path + '#' + parsed_url.fragment if parsed_url.fragment else parsed_url.path
    return f'redir {redirect_path} {github_discussion_url} permanent'

def log_url_mapping(stackoverflow_urls: List[str], github_discussion_url: str):
    """Log the mapping between Stack Overflow and GitHub Discussion URLs
    This mapping will be used for redirects in Caddy server
    StackOverflow URLs have multiple links for an entry, a link plus a share link.
    So we'll log all of them
    """
    for stackoverflow_url in stackoverflow_urls:
        if stackoverflow_url:
            url_mapping_logger.info(get_url_redir_str(stackoverflow_url, github_discussion_url))
        else:
            logger.warning("Empty Stack Overflow URL found, skipping logging for this entry.")


def remove_tags_under_threshold(tags_under_threshold: List[str], tags: List[str]) -> List[str]:
    """Remove tags that are under the threshold from the given tags list.
    
    Args:
        tags_under_threshold: List of tag names that are under threshold
        tags: List of tag names to filter
        
    Returns:
        List of tag names with under-threshold tags removed
    """
    return [tag for tag in tags if tag not in tags_under_threshold]

def get_tags_under_threshold(min_threshold: int, tags_data: List[Dict[str, Any]]) -> List[str]:
    """Get tag names for tags with count below the minimum threshold.
    
    Args:
        min_threshold: Minimum count threshold
        tags_data: List of tag dictionaries from tags.json
        
    Returns:
        List of tag names (strings) for tags with count < min_threshold
    """
    return [tag['name'] for tag in tags_data if tag.get('count', 0) < min_threshold]

def get_tags_at_or_above_threshold(min_threshold: int, tags_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get tag objects for tags with count at or above the minimum threshold.
    
    Args:
        min_threshold: Minimum count threshold
        tags_data: List of tag dictionaries from tags.json
        
    Returns:
        List of tag dictionaries for tags with count >= min_threshold
    """
    return [tag for tag in tags_data if tag.get('count', 0) >= min_threshold]

def get_readable_date(the_date):
    """Convert creation_date to a readable string format"""
    unknown_date = "Unknown Date"
    if the_date:
        try:
            if isinstance(the_date, (int, float)):
                # Handle Unix timestamp
                dt = datetime.fromtimestamp(the_date, tz=timezone.utc)
            elif isinstance(the_date, str):
                # Handle ISO 8601 datetime string like "2023-06-28T13:00:59.323"
                # Parse the ISO string and ensure it's in UTC
                if the_date.endswith('Z'):
                    # Already has UTC indicator
                    dt = datetime.fromisoformat(the_date.replace('Z', '+00:00'))
                elif '+' in the_date or the_date.endswith('UTC'):
                    # Has timezone info or UTC suffix
                    dt = datetime.fromisoformat(the_date.replace('UTC', '+00:00'))
                else:
                    # Assume UTC if no timezone specified
                    dt = datetime.fromisoformat(the_date).replace(tzinfo=timezone.utc)
            else:
                logger.warning(f"date is not instance of int, float, or string: {type(the_date)} - {the_date}")
                return unknown_date
            
            # Apply consistent formatting to both cases
            the_date = dt.strftime('%b %d, %Y at %H:%M %Z')
            
        except Exception as e:
            logger.error(f"Error converting date '{the_date}': {e}")
            the_date = unknown_date
    else:
        the_date = unknown_date
    return the_date


def mark_discussion_comment_as_answer(github_graphql, comment_node_id):
    """Mark a discussion comment as the accepted answer using the GraphQL mutation."""
    mutation = """
    mutation($id: ID!) {
      markDiscussionCommentAsAnswer(input: {id: $id}) {
        discussion {
          id
        }
      }
    }
    """
    variables = {'id': comment_node_id}
    data = github_graphql.github_graphql_request(mutation, variables)
    logger.info(f"Marked comment {comment_node_id} as accepted answer.")
    return True

def format_header_data(json_data: Dict[str, Any], action: MetaAction) -> str:
    """Format metadata for the discussion note section."""

    formatted_creation_date = get_readable_date(json_data.get("creation_date"))
    formatted_author = get_formatted_author(json_data)
    score = json_data.get("score", 0)
    vote = "votes"
    if isinstance(score, int) and score == 1:
        vote = "vote"

    return f"> [!NOTE]\n> Originally {action.value} by {formatted_author} on {formatted_creation_date} in BC Gov Stack Overflow.\n" + \
           f"> It had {score} {vote}.\n\n"

def get_formatted_author(json_data: Dict[str, Any]) -> str:
    """
    Get the formatted author name from the JSON data.
    """
    author = None
    if 'owner' in json_data and json_data['owner']:
        display_name = json_data['owner'].get('display_name')
        if display_name:
            author = display_name
        else:
            first = json_data['owner'].get('first_name', '')
            last = json_data['owner'].get('last_name', '')
            author = f"{first} {last}".strip() or None
    if not author:
        author = "Unknown User"
    return author

def main():
    # Setup logging for this script
    setup_populate_discussion_logging()
    
    parser = argparse.ArgumentParser(description='Populate GitHub Discussions from Q&A data')
    parser.add_argument('--repo', required=True, help='Repository in format owner/name')
    parser.add_argument('--category', required=True, help='Discussion category name')
    parser.add_argument('--questions-file', default='questions_answers_comments.json',
                        help='Path to questions JSON file')
    parser.add_argument('--tags-file', default='tags.json', help='Path to tags JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of questions to process')
    parser.add_argument('--image-folder', default='discussion_images_temp', help='Path to local folder containing images')
    parser.add_argument('--api-delay', type=float, default=1.0, help='Minimum seconds between API calls (default: 1.0)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--clean', action='store_true', help='Delete all discussions, comments, and labels in the repo before import')
    group.add_argument('--clean-only', action='store_true', help='Delete all discussions, comments, and labels, in the repo then exit')
    parser.add_argument('--clean-category', action='store_true', help='Used with --category and --clean or --clean-only to delete all discussions, comments, and labels in the specified category')
    parser.add_argument('--ignore-tags', 
                         type=str, 
                         nargs='+',
                         help='List of tags to ignore (space-separated). Questions tagged with these tag(s) will not be processed.')
    parser.add_argument('--tag-min-threshold',
                         type=int,
                         default=1,
                         help='Minimum number of questions a tag must be associated with to be considered for label creation (default: 1)')
    args = parser.parse_args()

    if args.tag_min_threshold < 0:
        logger.warning("Negative tag minimum threshold specified, defaulting to 1")
        args.tag_min_threshold = 1

    if args.api_delay < 0:
        logger.warning("Negative API delay specified, defaulting to 1.0 seconds")
        args.api_delay = 1.0

    # Set the global API delay based on user preference
    rate_limiter = RateLimiter(min_interval=args.api_delay)
    logger.info(f"Using API delay of {args.api_delay} seconds between requests")

    SO_LINK = "link"
    SO_SHARE_LINK = "share_link"

    # Initialize GitHub authentication
    github_auth_manager = GitHubAuthManager()
    github_auth_manager.initialize()

    github_graphql = GraphQLHelper(github_auth_manager, rate_limiter)
    
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        raise ValueError("Repository must be in format 'owner/name'")

    owner, name = repo_parts
    repo = github_auth_manager.get_client().get_repo(f"{owner}/{name}")

    logger.info(f"Using repo '{repo.full_name}'")



    # Get discussion category ID
    category_id = get_category_id(github_graphql, owner, name, args.category)
    category = Category(category_id, args.category)

    # Clean repository discussions, comments, and labels if --clean or --clean-only flag is set
    if args.clean or args.clean_only:
        clean_repo_discussions(github_graphql, owner, name, category if args.clean_category else None)
        if args.clean_only:
            logger.info('Cleanup complete. Exiting due to --clean-only flag.')
            return
          
    tags_to_ignore_helper = TagsToIgnore(args.ignore_tags if args.ignore_tags else None)
    
    # Load data
    questions = load_json(args.questions_file)
    tags_data = load_json(args.tags_file)
    
    tags_under_threshold = get_tags_under_threshold(args.tag_min_threshold, tags_data)
    
    tags_meeting_threshold = get_tags_at_or_above_threshold(args.tag_min_threshold, tags_data)

    # Get or create tags as labels
    existing_labels = get_labels(repo)
    tag_to_description = {tag['name']: tag.get('description', '') for tag in tags_meeting_threshold}

    for tag_name, description in tag_to_description.items():
        if tag_name not in existing_labels and not tags_to_ignore_helper.should_ignore([tag_name]):
            create_label(repo, tag_name, description)

    logger.info(f"category_id for '{args.category}': {category_id}")

    # Process questions with limit if specified
    if args.limit:
        questions = questions[:args.limit]

    # Sort questions by creation_date (chronological order)
    questions_sorted = sorted(questions, key=lambda q: q.get('creation_date', 0))

    # Ensure discussion_images folder exists in the repo
    ensure_discussion_images_folder(repo)
    local_image_folder = args.image_folder  # Use user-specified or default image folder
    os.makedirs(local_image_folder, exist_ok=True)

    # Create discussions and comments
    for i, question in enumerate(questions_sorted):
        try:
            
            # Extract question data
            title = decode_html_entities(question.get('title', f"Question #{i+1}"))
            
            # Extract tags
            tags = question.get('tags', [])
            if tags_to_ignore_helper.should_ignore(tags):
                logger.info(f"Skipping question {question.get('question_id', 'Unknown ID')} - {title} due to its tags containing ignored tag(s): {', '.join(tags)}")
                continue
            
            tags = remove_tags_under_threshold(tags_under_threshold, tags)

            body = question.get('body', '')

            # Use body_markdown if available, fall back to body_html or just body
            if 'body_markdown' in question:
                body = question['body_markdown']
            elif 'body_html' in question:
                body = question['body_html']

            # Decode HTML entities
            body = decode_html_entities(body)

            # --- IMAGE HANDLING FOR QUESTION BODY ---
            body = process_image_fields(body, local_image_folder, owner, name, repo, logger)

            header = format_header_data(question, MetaAction.ASKED)
            body = header + body

            # Sort comments by creation_date (chronological order)
            question_comments = question.get('comments', [])
            question_comments_sorted = sorted(question_comments, key=lambda c: c.get('creation_date', 0))

            # Check for existing discussion by title
            existing_node_id = find_discussion_by_title(github_graphql, owner, name, title, category)
            if existing_node_id:
                logger.info(f"Discussion already exists for title '{title}', applying labels only.")
                # logging for url mapping is also not done because it wouldn't map answer URLS
                # presumably this mapping was done in a previous run
                if tags:
                    label_node_ids = get_label_node_ids(github_graphql, owner, name, tags)
                    add_labels_to_discussion(github_graphql, existing_node_id, label_node_ids)
                continue

            # Create discussion
            discussion_number, discussion_url = create_discussion(github_graphql, owner, name, title, body, category_id, tags)
            
            # Links
            stackoverflow_urls = []
            stackoverflow_urls.append(question.get(SO_LINK))
            stackoverflow_urls.append(question.get(SO_SHARE_LINK))
            log_url_mapping(stackoverflow_urls, discussion_url)

            # Add question comments (chronological order)
            for comment in question_comments_sorted:
                comment_body = decode_html_entities(comment.get('body', ''))
                # --- IMAGE HANDLING FOR QUESTION COMMENT ---
                comment_body = process_image_fields(comment_body, local_image_folder, owner, name, repo, logger)
                comment_header = format_header_data(comment, MetaAction.COMMENTED)
                comment_body = comment_header + comment_body
                add_comment(github_graphql, owner, name, discussion_number, comment_body)

            # Add answers as comments (chronological order)
            accepted_answer_id = question.get('accepted_answer_id')
            answers = question.get('answers', [])
            answers_sorted = sorted(answers, key=lambda a: a.get('creation_date', 0))
            answer_id_to_comment_id = {}
            for answer in answers_sorted:
                answer_body = answer.get('body', '')

                # Use body_markdown if available, fall back to body_html
                if 'body_markdown' in answer:
                    answer_body = answer['body_markdown']
                elif 'body_html' in answer:
                    answer_body = answer['body_html']

                # Decode HTML entities
                answer_body = decode_html_entities(answer_body)

                # --- IMAGE HANDLING FOR ANSWER BODY ---
                answer_body = process_image_fields(answer_body, local_image_folder, owner, name, repo, logger)

               
                answer_header = format_header_data(answer, MetaAction.ANSWERED)

                # Remove accepted answer header from body (handled by API now)
                answer_body = answer_header + answer_body

                comment_id, comment_url = add_comment(github_graphql, owner, name, discussion_number, answer_body)
                if comment_id and 'answer_id' in answer:
                    answer_id_to_comment_id[answer['answer_id']] = comment_id

                answer_urls = []    
                answer_urls.append(answer.get(SO_LINK))
                answer_urls.append(answer.get(SO_SHARE_LINK))
                log_url_mapping(answer_urls, comment_url)

                # Also add any comments on the answer
                for comment in answer.get('comments', []):
                    comment_body = decode_html_entities(comment.get('body', ''))

                    # --- IMAGE HANDLING FOR ANSWER COMMENT ---
                    comment_body = process_image_fields(comment_body, local_image_folder, owner, name, repo, logger)

            
                    comment_header = format_header_data(comment, MetaAction.COMMENTED)
                    comment_body = comment_header + comment_body

                    add_comment(github_graphql, owner, name, discussion_number, comment_body, comment_id)

            # Mark accepted answer using API if available
            if accepted_answer_id and accepted_answer_id in answer_id_to_comment_id:
                mark_discussion_comment_as_answer(github_graphql, answer_id_to_comment_id[accepted_answer_id])
        except Exception as e:
            question_id = question['question_id'] if question else "Unknown ID"
            logger.error(f"Error processing question_id {question_id} question #{i+1}: {e}")
            continue



class TagsToIgnore:
    """Helper class to manage tags that should be ignored during migration."""

    def __init__(self, tags_to_ignore: list[str] = None):
        """Initialize tags to ignore.
        
        Args:
            tags_to_ignore: List of tags to ignore
        """
        self.tags_to_ignore = tags_to_ignore

        if self.tags_to_ignore:
            logger.info(f"Tags to ignore: {', '.join(self.tags_to_ignore)}")

    def should_ignore(self, tags: list[str]) -> bool:
        """Check if any of the given tags should be ignored.
        
        Args:
            tags: List of tags to check

        Returns:
            True if any tag should be ignored, False otherwise
        """

        return self.tags_to_ignore and any(t in self.tags_to_ignore for t in tags)

if __name__ == '__main__':
    main()
