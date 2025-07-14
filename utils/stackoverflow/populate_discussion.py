import json
import os
import logging
import argparse
from github import Github, Auth
from github.GithubException import GithubException
from typing import Dict, List, Any
import requests
import re
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def github_graphql_request(token, query, variables=None):
    """Helper to make a GitHub GraphQL API request and handle errors."""
    headers = {
        'Authorization': f'bearer {token}',
        'Accept': 'application/vnd.github+json'
    }
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables or {}},
        headers=headers
    )
    try:
        result = response.json()
    except Exception as e:
        logger.error(f"Failed to parse GraphQL response: {e}")
        raise
    if 'errors' in result:
        logger.error(f"GraphQL errors: {result['errors']}")
        raise Exception(f"GraphQL errors: {result['errors']}")
    if 'data' not in result:
        logger.error(f"No data in GraphQL response: {result}")
        raise Exception(f"No data in GraphQL response: {result}")
    return result['data']

def get_category_id(token, owner: str, name: str, category_name: str):
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
    data = github_graphql_request(token, query, variables)
    categories = data['repository']['discussionCategories']['nodes']
    for category in categories:
        if category['name'] == category_name:
            return category['id']
    raise ValueError(f'Category {category_name} not found')

def get_repo_node_id(token, owner: str, name: str):
    """Fetch the repository node_id using a GraphQL query."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
      }
    }
    """
    variables = {'owner': owner, 'name': name}
    data = github_graphql_request(token, query, variables)
    return data['repository']['id']

def get_label_node_ids(token, owner: str, name: str, label_names: List[str]) -> List[str]:
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
        data = github_graphql_request(token, query, variables)
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

def add_labels_to_discussion(token, discussion_node_id: str, label_node_ids: List[str]):
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
    github_graphql_request(token, mutation, variables)

def create_discussion(token, g, repo, owner, name, title: str, body: str, category_id: str, labels_list: List[str]):
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
        }
      }
    }
    """
    repo_node_id = get_repo_node_id(token, owner, name)
    variables = {
        'repositoryId': repo_node_id,
        'categoryId': category_id,
        'title': title,
        'body': body
    }
    data = github_graphql_request(token, mutation, variables)
    discussion = data['createDiscussion']['discussion']
    discussion_number = discussion['number']
    discussion_node_id = discussion['id']
    logger.info(f"Created discussion #{discussion_number}: {title}")
    if labels_list:
        label_node_ids = get_label_node_ids(token, owner, name, labels_list)
        add_labels_to_discussion(token, discussion_node_id, label_node_ids)
    return discussion_number

def add_comment(token, owner: str, name: str, discussion_number: int, body: str):
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
    data = github_graphql_request(token, query, variables)
    discussion_id = data['repository']['discussion']['id']
    mutation = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {
        discussionId: $discussionId,
        body: $body
      }) {
        comment {
          id
        }
      }
    }
    """
    variables = {
        'discussionId': discussion_id,
        'body': body
    }
    data = github_graphql_request(token, mutation, variables)
    logger.info(f"Added comment to discussion #{discussion_number}")
    return data['addDiscussionComment']['comment']['id']

def find_discussion_by_title(token, owner: str, name: str, title: str):
    """Return (discussion_number, discussion_node_id) if a discussion with the given title exists, else None."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussions(first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            id
            number
            title
          }
        }
      }
    }
    """
    variables = {'owner': owner, 'name': name}
    data = github_graphql_request(token, query, variables)
    discussions = data['repository']['discussions']['nodes']
    for d in discussions:
        if d['title'].strip() == title.strip():
            return d['number'], d['id']
    return None, None

def clean_repo_discussions(token, owner: str, name: str, category_name: str = None):
    """Delete all discussions, their comments, and remove all labels from the repo. Optionally filter by category."""

    category_id = get_category_id(token, owner, name, category_name) if category_name else None

    if not category_id:
      logger.warning("Cleaning all discussions, comments, and labels from the repository!")
    else:
      logger.warning(f"Cleaning discussions in category '{category_name}', comments, and labels from the repository!")
      

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
        variables = {'owner': owner, 'name': name, 'after': end_cursor, 'categoryId': category_id}
        data = github_graphql_request(token, query, variables)
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
                github_graphql_request(token, mutation, variables_rm)
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
                github_graphql_request(token, mutation, variables_del)
            mutation = """
            mutation($id: ID!) {
              deleteDiscussion(input: {id: $id}) {
                clientMutationId
              }
            }
            """
            variables_del = {'id': discussion_id}
            github_graphql_request(token, mutation, variables_del)
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

def process_image_fields(text, local_image_folder, owner, name, repo, logger):
    """Extract image URLs, upload local images to GitHub, and replace URLs in the text."""
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

def main():
    parser = argparse.ArgumentParser(description='Populate GitHub Discussions from Q&A data')
    parser.add_argument('--repo', required=True, help='Repository in format owner/name')
    parser.add_argument('--category', required=True, help='Discussion category name')
    parser.add_argument('--questions-file', default='questions_answers_comments.json',
                        help='Path to questions JSON file')
    parser.add_argument('--tags-file', default='tags.json', help='Path to tags JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of questions to process')
    parser.add_argument('--image-folder', default='discussion_images_temp', help='Path to local folder containing images')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--clean', action='store_true', help='Delete all discussions, comments, and labels in the repo before import')
    group.add_argument('--clean-only', action='store_true', help='Delete all discussions, comments, and labels, in the repo then exit')
    parser.add_argument('--clean-category', action='store_true', help='Used with --category and --clean or --clean-only to delete all discussions, comments, and labels in the specified category')
    args = parser.parse_args()

  
    installation_id = os.environ.get("GHD_INSTALLATION_ID")
    app_id = os.environ.get("GHD_APP_ID")
    # This should be the path to the private key file
    private_key = os.environ.get("GHD_PRIVATE_KEY")

    if not installation_id or not app_id or not private_key:
        raise ValueError("INSTALLATION_ID, APP_ID, and PRIVATE_KEY environment variables must be set")
    
    if not installation_id.isdigit() or not app_id.isdigit():
        raise ValueError("INSTALLATION_ID and APP_ID must be numeric")
    
    if args.clean_category and (not args.category or not (args.clean or args.clean_only)):
        raise ValueError("When using --clean-category, you must also specify --category and either --clean or --clean-only")

    with open(private_key, "r") as key_file:
        private_key = key_file.read()

    auth = Auth.AppAuth(int(app_id), private_key).get_installation_auth(int(installation_id))

    # Initialize PyGithub client
    g = Github(auth=auth)
    
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        raise ValueError("Repository must be in format 'owner/name'")

    owner, name = repo_parts
    repo = g.get_repo(f"{owner}/{name}")

    logger.info(f"Using repo'{repo.full_name}'")

    token = auth.token

    # Clean repository discussions, comments, and labels if --clean or --clean-only flag is set
    if args.clean or args.clean_only:
        clean_repo_discussions(token, owner, name, args.category if args.clean_category else None)
        if args.clean_only:
            logger.info('Cleanup complete. Exiting due to --clean-only flag.')
            return

    # Load data
    questions = load_json(args.questions_file)
    tags_data = load_json(args.tags_file)

    # Get or create tags as labels
    existing_labels = get_labels(repo)
    tag_to_description = {tag['name']: tag.get('description', '') for tag in tags_data}

    for tag_name, description in tag_to_description.items():
        if tag_name not in existing_labels:
            create_label(repo, tag_name, description)

    # Get discussion category ID
    category_id = get_category_id(token, owner, name, args.category)

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
            title = question.get('title', f"Question #{i+1}")
            body = question.get('body', '')

            # Use body_markdown if available, fall back to body_html or just body
            if 'body_markdown' in question:
                body = question['body_markdown']
            elif 'body_html' in question:
                body = question['body_html']

            # --- IMAGE HANDLING FOR QUESTION BODY ---
            body = process_image_fields(body, local_image_folder, owner, name, repo, logger)

            # Extract author info and creation date
            author_name = None
            if 'owner' in question and question['owner']:
                display_name = question['owner'].get('display_name')
                if display_name:
                    author_name = display_name
                else:
                    # Try first/last name if available
                    first = question['owner'].get('first_name', '')
                    last = question['owner'].get('last_name', '')
                    author_name = f"{first} {last}".strip() or None
            if not author_name:
                author_name = "Unknown User"
            creation_date = question.get('creation_date')
            if creation_date:
                # If it's a timestamp, convert to readable date
                try:
                    import datetime
                    if isinstance(creation_date, (int, float)):
                        creation_date = datetime.datetime.utcfromtimestamp(creation_date).strftime('%Y-%m-%d %H:%M:%S UTC')
                except Exception:
                    pass
            else:
                creation_date = "Unknown Date"
            # Format author and date as a markdown NOTE block
            header = f"> [!NOTE]\n> Originally asked in BC Gov Stack Overflow by {author_name} on {creation_date}\n\n"
            body = header + body

            # Extract tags
            tags = question.get('tags', [])

            # Sort comments by creation_date (chronological order)
            question_comments = question.get('comments', [])
            question_comments_sorted = sorted(question_comments, key=lambda c: c.get('creation_date', 0))

            # Check for existing discussion by title
            existing_number, existing_node_id = find_discussion_by_title(token, owner, name, title)
            if existing_node_id:
                logger.info(f"Discussion already exists for title '{title}', applying labels only.")
                if tags:
                    label_node_ids = get_label_node_ids(token, owner, name, tags)
                    add_labels_to_discussion(token, existing_node_id, label_node_ids)
                continue

            # Create discussion
            discussion_number = create_discussion(token, g, repo, owner, name, title, body, category_id, tags)

            # Add question comments (chronological order)
            for comment in question_comments_sorted:
                comment_body = comment.get('body', '')
                # --- IMAGE HANDLING FOR QUESTION COMMENT ---
                comment_body = process_image_fields(comment_body, local_image_folder, owner, name, repo, logger)
                # Add commenter info and creation date if available
                comment_author = None
                if 'owner' in comment and comment['owner']:
                    display_name = comment['owner'].get('display_name')
                    if display_name:
                        comment_author = display_name
                    else:
                        first = comment['owner'].get('first_name', '')
                        last = comment['owner'].get('last_name', '')
                        comment_author = f"{first} {last}".strip() or None
                if not comment_author:
                    comment_author = "Unknown User"
                comment_date = comment.get('creation_date')
                if comment_date:
                    try:
                        import datetime
                        if isinstance(comment_date, (int, float)):
                            comment_date = datetime.datetime.utcfromtimestamp(comment_date).strftime('%Y-%m-%d %H:%M:%S UTC')
                    except Exception:
                        pass
                else:
                    comment_date = "Unknown Date"
                comment_header = f"> [!NOTE]\n> Comment by {comment_author} on {comment_date}\n\n"
                comment_body = comment_header + comment_body
                add_comment(token, owner, name, discussion_number, comment_body)

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

                # --- IMAGE HANDLING FOR ANSWER BODY ---
                answer_body = process_image_fields(answer_body, local_image_folder, owner, name, repo, logger)

                # Add owner info and creation date if available
                answer_author = None
                if 'owner' in answer and answer['owner']:
                    display_name = answer['owner'].get('display_name')
                    if display_name:
                        answer_author = display_name
                    else:
                        first = answer['owner'].get('first_name', '')
                        last = answer['owner'].get('last_name', '')
                        answer_author = f"{first} {last}".strip() or None
                if not answer_author:
                    answer_author = "Unknown User"
                answer_date = answer.get('creation_date')
                if answer_date:
                    try:
                        import datetime
                        if isinstance(answer_date, (int, float)):
                            answer_date = datetime.datetime.utcfromtimestamp(answer_date).strftime('%Y-%m-%d %H:%M:%S UTC')
                    except Exception:
                        pass
                else:
                    answer_date = "Unknown Date"
                answer_header = f"> [!NOTE]\n> Originally answered by {answer_author} on {answer_date}\n\n"

                # Remove accepted answer header from body (handled by API now)
                answer_body = answer_header + answer_body

                comment_id = add_comment(token, owner, name, discussion_number, answer_body)
                if comment_id and 'answer_id' in answer:
                    answer_id_to_comment_id[answer['answer_id']] = comment_id

                # Also add any comments on the answer
                for comment in answer.get('comments', []):
                    comment_body = comment.get('body', '')

                    # --- IMAGE HANDLING FOR ANSWER COMMENT ---
                    comment_body = process_image_fields(comment_body, local_image_folder, owner, name, repo, logger)

                    # Add commenter info and creation date if available
                    comment_author = None
                    if 'owner' in comment and comment['owner']:
                        display_name = comment['owner'].get('display_name')
                        if display_name:
                            comment_author = display_name
                        else:
                            first = comment['owner'].get('first_name', '')
                            last = comment['owner'].get('last_name', '')
                            comment_author = f"{first} {last}".strip() or None
                    if not comment_author:
                        comment_author = "Unknown User"
                    comment_date = comment.get('creation_date')
                    if comment_date:
                        try:
                            import datetime
                            if isinstance(comment_date, (int, float)):
                                comment_date = datetime.datetime.utcfromtimestamp(comment_date).strftime('%Y-%m-%d %H:%M:%S UTC')
                        except Exception:
                            pass
                    else:
                        comment_date = "Unknown Date"
                    comment_header = f"> [!NOTE]\n> Comment by {comment_author} on {comment_date}\n\n"
                    comment_body = comment_header + comment_body

                    add_comment(token, owner, name, discussion_number, comment_body)

            # Mark accepted answer using API if available
            if accepted_answer_id and accepted_answer_id in answer_id_to_comment_id:
                mark_discussion_comment_as_answer(token, answer_id_to_comment_id[accepted_answer_id])
        except Exception as e:
            logger.error(f"Error processing question #{i+1}: {e}")
            continue

def mark_discussion_comment_as_answer(token, comment_node_id):
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
    data = github_graphql_request(token, mutation, variables)
    logger.info(f"Marked comment {comment_node_id} as accepted answer.")
    return True

if __name__ == '__main__':
    main()
