#!/usr/bin/env python3
"""
Delete GitHub Discussions based on Stack Overflow question IDs.

This script reads a list of SO question IDs, finds the corresponding questions in the 
questions_answers_comments.json file, looks up the GitHub discussions by title,
and deletes them along with all associated comments.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from collections import namedtuple

from populate_discussion_helpers import RateLimiter, GitHubAuthManager, GraphQLHelper
from populate_discussion import (
    load_json, decode_html_entities, get_category_id, find_discussion_by_title, Category
)

# Setup logging
# Configure root logger only if no handlers are already set up
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_console_handler = logging.StreamHandler()
    logger_console_handler.setFormatter(formatter)
    root_logger.addHandler(logger_console_handler)

# Always add our own file handler for this script
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_file_handler = logging.FileHandler('delete_discussions.log')
logger_file_handler.setFormatter(formatter)
root_logger.addHandler(logger_file_handler)

# Get logger for this module
logger = logging.getLogger(__name__)


def load_question_ids_from_file(file_path: str) -> List[int]:
    """Load question IDs from a text file (one ID per line)."""
    question_ids = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    try:
                        question_id = int(line)
                        question_ids.append(question_id)
                    except ValueError:
                        logger.warning(f"Invalid question_id '{line}' on line {line_num}, skipping")
        logger.info(f"Loaded {len(question_ids)} question IDs from {file_path}")
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {e}")
        sys.exit(1)
    
    return question_ids

def find_questions_by_ids(questions_data: List[Dict[str, Any]], question_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Find questions in the JSON data by their question_id."""
    questions_map = {}
    target_ids = set(question_ids)
    
    for question in questions_data:
        question_id = question.get('question_id')
        if question_id in target_ids:
            questions_map[question_id] = question
    
    return questions_map

def delete_discussion_by_id(github_graphql: GraphQLHelper, discussion_node_id: str, title: str) -> bool:
    """Delete a GitHub discussion and all its comments by node ID."""
    try:
        # First, get all comments in the discussion to delete them
        query = """
        query($discussionId: ID!) {
          node(id: $discussionId) {
            ... on Discussion {
              id
              number
              title
              comments(first: 100) {
                nodes {
                  id
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
          }
        }
        """
        variables = {'discussionId': discussion_node_id}
        data = github_graphql.github_graphql_request(query, variables)
        
        discussion = data['node']
        if not discussion:
            logger.error(f"Discussion with ID {discussion_node_id} not found")
            return False
        
        discussion_number = discussion['number']
        logger.info(f"Deleting discussion #{discussion_number}: {title}")
        
        # Delete all comments first
        comments = discussion['comments']['nodes']
        for comment in comments:
            comment_id = comment['id']
            mutation = """
            mutation($id: ID!) {
              deleteDiscussionComment(input: {id: $id}) {
                clientMutationId
              }
            }
            """
            variables_del = {'id': comment_id}
            github_graphql.github_graphql_request(mutation, variables_del)
            logger.debug(f"Deleted comment {comment_id}")
        
        # Handle pagination if there are more than 100 comments
        has_next_page = discussion['comments']['pageInfo']['hasNextPage']
        end_cursor = discussion['comments']['pageInfo']['endCursor']
        
        while has_next_page:
            query = """
            query($discussionId: ID!, $after: String) {
              node(id: $discussionId) {
                ... on Discussion {
                  comments(first: 100, after: $after) {
                    nodes {
                      id
                    }
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                  }
                }
              }
            }
            """
            variables = {'discussionId': discussion_node_id, 'after': end_cursor}
            data = github_graphql.github_graphql_request(query, variables)
            
            comments = data['node']['comments']['nodes']
            for comment in comments:
                comment_id = comment['id']
                mutation = """
                mutation($id: ID!) {
                  deleteDiscussionComment(input: {id: $id}) {
                    clientMutationId
                  }
                }
                """
                variables_del = {'id': comment_id}
                github_graphql.github_graphql_request(mutation, variables_del)
                logger.debug(f"Deleted comment {comment_id}")
            
            has_next_page = data['node']['comments']['pageInfo']['hasNextPage']
            end_cursor = data['node']['comments']['pageInfo']['endCursor']
        
        # Now delete the discussion itself
        mutation = """
        mutation($id: ID!) {
          deleteDiscussion(input: {id: $id}) {
            clientMutationId
          }
        }
        """
        variables_del = {'id': discussion_node_id}
        github_graphql.github_graphql_request(mutation, variables_del)
        
        logger.info(f"Successfully deleted discussion #{discussion_number}: {title}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting discussion '{title}': {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Delete GitHub Discussions based on Stack Overflow question IDs',
        epilog='''
Examples:
  # Delete discussions for specific question IDs
  python delete_discussions.py --repo owner/repo --category "Q&A" --question-ids failed_questions.txt
  
  # Use custom input file
  python delete_discussions.py --repo owner/repo --category "Q&A" --question-ids failed_questions.txt --input custom_questions.json
  
  # Dry run to see what would be deleted
  python delete_discussions.py --repo owner/repo --category "Q&A" --question-ids failed_questions.txt --dry-run
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--repo', required=True, 
                       help='Repository in format owner/name')
    parser.add_argument('--category', required=True, 
                       help='Discussion category name to search in')
    parser.add_argument('--question-ids', required=True,
                       help='File containing question IDs to delete (one per line)')
    
    # Optional arguments
    parser.add_argument('--input', '-i', 
                       default='questions_answers_comments.json',
                       help='Input JSON file containing Stack Overflow data (default: questions_answers_comments.json)')
    parser.add_argument('--api-delay', type=float, default=1.0,
                       help='Minimum seconds between API calls (default: 1.0)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.input).exists():
        logger.error(f"Input file '{args.input}' does not exist")
        sys.exit(1)
    
    if not Path(args.question_ids).exists():
        logger.error(f"Question IDs file '{args.question_ids}' does not exist")
        sys.exit(1)
    
    # Parse repository
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        logger.error("Repository must be in format 'owner/name'")
        sys.exit(1)
    
    owner, name = repo_parts
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(min_interval=args.api_delay)
    logger.info(f"Using API delay of {args.api_delay} seconds between requests")
    
    # Initialize GitHub authentication
    try:
        github_auth_manager = GitHubAuthManager()
        github_auth_manager.initialize()
        github_graphql = GraphQLHelper(github_auth_manager, rate_limiter)
        logger.info("GitHub authentication initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GitHub authentication: {e}")
        sys.exit(1)
    
    # Get discussion category ID
    try:
        category_id = get_category_id(github_graphql, owner, name, args.category)
        category = Category(category_id, args.category)
        logger.info(f"Found category '{args.category}' with ID: {category_id}")
    except Exception as e:
        logger.error(f"Error getting category ID: {e}")
        sys.exit(1)
    
    # Load question IDs to delete
    question_ids = load_question_ids_from_file(args.question_ids)
    if not question_ids:
        logger.error("No valid question IDs found in file")
        sys.exit(1)
    
    # Load Stack Overflow data
    try:
        questions_data = load_json(args.input)
        logger.info(f"Loaded {len(questions_data)} questions from {args.input}")
    except Exception as e:
        logger.error(f"Error loading questions data: {e}")
        sys.exit(1)
    
    # Find questions by IDs
    questions_map = find_questions_by_ids(questions_data, question_ids)
    found_count = len(questions_map)
    missing_ids = set(question_ids) - set(questions_map.keys())
    
    logger.info(f"Found {found_count} questions out of {len(question_ids)} requested")
    if missing_ids:
        logger.warning(f"Missing question IDs: {sorted(missing_ids)}")
    
    if found_count == 0:
        logger.error("No matching questions found")
        sys.exit(1)
    
    # Process each question
    deleted_count = 0
    not_found_count = 0
    error_count = 0
    
    for question_id, question in questions_map.items():
        title = decode_html_entities(question.get('title') or "")
        logger.info(f"Processing question {question_id}: {title}")
        
        try:
            # Find the GitHub discussion by title
            discussion_node_id = find_discussion_by_title(github_graphql, owner, name, title, category)
            
            if discussion_node_id:
                if args.dry_run:
                    logger.info(f"[DRY RUN] Would delete discussion: {title}")
                    deleted_count += 1
                else:
                    if delete_discussion_by_id(github_graphql, discussion_node_id, title):
                        deleted_count += 1
                    else:
                        error_count += 1
            else:
                logger.warning(f"No GitHub discussion found for question {question_id}: {title}")
                not_found_count += 1
                
        except Exception as e:
            logger.error(f"Error processing question {question_id}: {e}")
            error_count += 1
    
    # Print summary
    action = "Would delete" if args.dry_run else "Deleted"
    logger.info(f"\nSummary:")
    logger.info(f"  {action}: {deleted_count} discussions")
    logger.info(f"  Not found: {not_found_count} discussions")
    logger.info(f"  Errors: {error_count} discussions")
    logger.info(f"  Total processed: {found_count} questions")
    
    if args.dry_run:
        logger.info("\nThis was a dry run. Use --dry-run=false to actually delete discussions.")

if __name__ == '__main__':
    main()
