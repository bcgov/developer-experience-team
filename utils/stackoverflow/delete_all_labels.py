import logging
import argparse
from github.GithubException import GithubException
from populate_discussion_helpers import RateLimiter, GitHubAuthManager, GraphQLHelper
from typing import Dict, List, Any


# Get logger for this module
logger = logging.getLogger(__name__)


def setup_logging():
    root_logger = logging.getLogger()
    
    # Avoid adding duplicate handlers
    if root_logger.hasHandlers():
        return
        
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_file_handler = logging.FileHandler('delete_labels.log')
    logger_file_handler.setFormatter(formatter)
    logger_console_handler = logging.StreamHandler()
    logger_console_handler.setFormatter(formatter)
    root_logger.addHandler(logger_file_handler)
    root_logger.addHandler(logger_console_handler)

def delete_labels(github_graphql: GraphQLHelper, labels_to_delete: List[Dict[str, Any]], dry_run: bool):
    if not labels_to_delete:
        logger.info("No labels found to delete")
        return
        
    successful_deletions = 0
    failed_deletions = 0
    
    for label in labels_to_delete:
        mutation = """
        mutation($labelId: ID!) {
          deleteLabel(input: {id: $labelId}) {
            clientMutationId
          }
        }
        """
        variables = {
            'labelId': label['id']
        }
        if dry_run:
            logger.info(f"Dry run: Would delete label: '{label['name']}' (ID: {label['id']})")
            successful_deletions += 1
        else:
            try:
                github_graphql.github_graphql_request(mutation, variables)
                logger.info(f"Deleted label: '{label['name']}'")
                successful_deletions += 1
            except Exception as e:
                logger.error(f"Failed to delete label '{label['name']}': {e}")
                failed_deletions += 1
    
    action = "Would delete" if dry_run else "Deleted"
    logger.info(f"Summary: {action} {successful_deletions} labels successfully")
    if failed_deletions > 0:
        logger.warning(f"Failed to delete {failed_deletions} labels")   

def get_all_labels(github_graphql: GraphQLHelper, owner: str, name: str) -> List[Dict[str, Any]]:
    """Retrieve all labels from the specified GitHub repository."""
    all_labels = []
    has_next_page = True
    end_cursor = None
    
    logger.info(f"Fetching labels from repository {owner}/{name}...")
    
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
        
        try:
            data = github_graphql.github_graphql_request(query, variables)
            label_data = data['repository']['labels']
            all_labels.extend(label_data['nodes'])
            has_next_page = label_data['pageInfo']['hasNextPage']
            end_cursor = label_data['pageInfo']['endCursor']
        except Exception as e:
            logger.error(f"Failed to fetch labels: {e}")
            raise
    
    logger.info(f"Found {len(all_labels)} labels")
    return all_labels
  

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description='Delete labels for given GitHub Discussions repo')
    parser.add_argument('--repo', required=True, help='Repository in format owner/name')
    parser.add_argument('--api-delay', type=float, default=1.0, help='Minimum seconds between API calls (default: 1.0)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()


    if args.api_delay < 0:
        logger.warning("Negative API delay specified, defaulting to 1.0 seconds")
        args.api_delay = 1.0

    # Set the global API delay based on user preference
    rate_limiter = RateLimiter(min_interval=args.api_delay)
    logger.info(f"Using API delay of {args.api_delay} seconds between requests")

    # Initialize GitHub authentication
    github_auth_manager = GitHubAuthManager()
    github_auth_manager.initialize()

    github_graphql = GraphQLHelper(github_auth_manager, rate_limiter)
    
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        raise ValueError("Repository must be in format 'owner/name'")

    owner, name = repo_parts
    repo = github_auth_manager.get_client().get_repo(f"{owner}/{name}")

    logger.info(f"Deleting labels in repo '{repo.full_name}'")
    logger.info(f"Dry run mode: {args.dry_run}")
    
    # Get all labels from the repository
    labels_to_delete = get_all_labels(github_graphql, owner, name)
    
    if not labels_to_delete:
        logger.info("No labels found in repository")
        return
    
    # Ask for confirmation unless it's a dry run or force flag is used
    if not args.dry_run and not args.force:
        print(f"\nWARNING: This will permanently delete {len(labels_to_delete)} labels from {repo.full_name}")
        print("Labels to be deleted:")
        for label in labels_to_delete[:10]:  # Show first 10
            print(f"  - {label['name']}")
        if len(labels_to_delete) > 10:
            print(f"  ... and {len(labels_to_delete) - 10} more")
        
        response = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            logger.info("Operation cancelled by user")
            return
    
    # Delete all labels from the repository
    delete_labels(github_graphql, labels_to_delete, args.dry_run)
    logger.info("Label deletion process completed")


if __name__ == '__main__':
    main()
