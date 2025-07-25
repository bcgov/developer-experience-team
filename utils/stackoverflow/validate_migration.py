import json
import os
import logging
import argparse
import re
from typing import Dict, List
from populate_discussion_helpers import GitHubAuthManager, GraphQLHelper
from populate_discussion import (
    load_json, decode_html_entities, get_category_id
)

# Configure logging only if no handlers are already set up
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_image_filenames(text: str) -> set:
    """Extract image filenames from markdown/html image tags, ignoring the host/path."""
    if not text:
        return set()
    
    # Patterns for both markdown ![alt](url) and HTML <img src="url">
    md_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
    html_pattern = r'<img [^>]*src=["\']([^"\'>]+)["\']'
    
    image_urls = re.findall(md_pattern, text) + re.findall(html_pattern, text)
    
    # Extract just the filename from each URL
    filenames = set()
    for url in image_urls:
        # Extract filename from URL (everything after the last slash)
        filename = url.split('/')[-1]
        # Remove query parameters like ?raw=true
        filename = filename.split('?')[0]
        filenames.add(filename)
    
    return filenames

def normalize_image_urls(text: str) -> str:
    """Replace image URLs with normalized placeholders to allow content comparison."""
    if not text:
        return text
    
    # Replace markdown images ![alt](url) with ![alt](IMAGE_PLACEHOLDER)
    def replace_md_image(match):
        alt_text = match.group(1)
        url = match.group(2)
        filename = url.split('/')[-1].split('?')[0]  # Get filename without query params
        return f"![{alt_text}](IMAGE:{filename})"
    
    # Replace HTML images <img src="url"> with <img src="IMAGE_PLACEHOLDER">
    def replace_html_image(match):
        before_src = match.group(1)  # Everything before the URL in src attribute
        url = match.group(2)  # The actual URL
        after_src = match.group(3)  # Everything after the URL in src attribute
        filename = url.split('/')[-1].split('?')[0]  # Get filename without query params
        return f"<img {before_src}IMAGE:{filename}{after_src}"
    
    # Apply replacements
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_md_image, text)
    text = re.sub(r'<img ([^>]*src=["\'])([^"\'>]+)(["\'][^>]*>)', replace_html_image, text)
    
    return text

class MigrationValidator:
    def __init__(self, auth_manager: GitHubAuthManager, owner: str, name: str, category_name: str):
        self.owner = owner
        self.name = name
        self.category_name = category_name
        self.github_graphql = GraphQLHelper(auth_manager)
        self.validation_results = {
            'total_questions': 0,
            'migrated_questions': 0,
            'missing_questions': [],
            'answer_mismatches': [],
            'comment_mismatches': [],
            'content_issues': []
        }

    def get_github_discussions(self) -> List[Dict]:
        """Fetch all discussions from the specified category."""
        discussions = []
        has_next_page = True
        end_cursor = None
        
        categoryId = get_category_id(self.github_graphql, self.owner, self.name, self.category_name)
        while has_next_page:
            query = """
           query($owner: String!, $name: String!, $categoryId: ID, $after: String) {
            repository(owner: $owner, name: $name) {
              discussions(first: 50, categoryId: $categoryId, after: $after) {
                  nodes {
                    id
                    number
                    title
                    body
                    createdAt
                    author {
                      login
                    }
                    labels(first: 20) {
                      nodes {
                        name
                      }
                    }
                    comments(first: 100) {
                      nodes {
                        id
                        body
                        createdAt
                        author {
                          login
                        }
                        isAnswer
                        replyTo {
                          id
                        }
                        replies(first: 50) {
                          nodes {
                            id
                            body
                            createdAt
                            author {
                              login
                            }
                          }
                        }
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
            variables = {'owner': self.owner, 'name': self.name, 'after': end_cursor, 'categoryId': categoryId}
            data = self.github_graphql.github_graphql_request(query, variables)
            
            for discussion in data['repository']['discussions']['nodes']:
              discussions.append(discussion)
            
            has_next_page = data['repository']['discussions']['pageInfo']['hasNextPage']
            end_cursor = data['repository']['discussions']['pageInfo']['endCursor']
        
        return discussions

    def validate_question_content(self, so_question: Dict, gh_discussion: Dict) -> List[str]:
        """Validate that question content was transferred correctly."""
        issues = []
        
        # Check title
        so_title = decode_html_entities(so_question.get('title', ''))
        gh_title = gh_discussion['title']
        if so_title != gh_title:
            issues.append(f"Title mismatch: SO='{so_title}' vs GH='{gh_title}'")
        
        # Check if original body content is present (allowing for added headers)
        so_body = decode_html_entities(so_question.get('body_markdown', so_question.get('body', '')))
        gh_body = gh_discussion['body']
        
        # Check images first - this affects content validation
        so_images = extract_image_filenames(so_body)
        gh_images = extract_image_filenames(gh_body)
        missing_images = so_images - gh_images
        if missing_images:
            issues.append(f"Missing images: {missing_images}")
        
        # Normalize image URLs for comparison
        so_body_normalized = normalize_image_urls(so_body)
        gh_body_normalized = normalize_image_urls(gh_body)
        
        # Check content - if images are missing, also try text-only comparison
        content_found = so_body_normalized in gh_body_normalized
        
        if not content_found and missing_images:
            # Try comparing without image syntax
            so_text_only = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', so_body)
            so_text_only = re.sub(r'<img [^>]*>', '', so_text_only)
            so_text_only = ' '.join(so_text_only.split())  # Normalize whitespace
            
            gh_text_only = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', gh_body)
            gh_text_only = re.sub(r'<img [^>]*>', '', gh_text_only)
            gh_text_only = ' '.join(gh_text_only.split())  # Normalize whitespace
            
            if so_text_only.strip() and so_text_only in gh_text_only:
                content_found = True
        
        if so_body_normalized and not content_found:
            issues.append(f"Body content not found in GitHub discussion")
        
        # Check tags/labels
        so_tags = set(so_question.get('tags', []))
        gh_labels = set(label['name'] for label in gh_discussion['labels']['nodes'])
        missing_tags = so_tags - gh_labels
        if missing_tags:
            issues.append(f"Missing tags: {missing_tags}")
        
        return issues

    def validate_answers(self, so_question: Dict, gh_discussion: Dict) -> List[str]:
        """Validate that answers were transferred correctly."""
        issues = []
        
        so_answers = so_question.get('answers', [])
        gh_comments = [c for c in gh_discussion['comments']['nodes'] 
                      if 'Originally answered by' in c['body']]
        
        if len(so_answers) != len(gh_comments):
            issues.append(f"Answer count mismatch: SO={len(so_answers)} vs GH={len(gh_comments)}")
        
        # Check if accepted answer is marked correctly
        accepted_answer_id = so_question.get('accepted_answer_id')
        gh_accepted_answers = [c for c in gh_discussion['comments']['nodes'] if c['isAnswer']]
        
        if accepted_answer_id and len(gh_accepted_answers) != 1:
            issues.append(f"Accepted answer not properly marked in GitHub")
        elif not accepted_answer_id and len(gh_accepted_answers) > 0:
            issues.append(f"GitHub has accepted answer but SO doesn't")
        
        # Check answer content and images
        for so_answer in so_answers:
            so_answer_body = decode_html_entities(so_answer.get('body_markdown', so_answer.get('body', '')))
            so_answer_normalized = normalize_image_urls(so_answer_body)
            so_answer_images = extract_image_filenames(so_answer_body)
            
            # Find matching GitHub comment using a more flexible approach
            matching_gh_comment = None
            
            # First, try to find exact normalized match (with whitespace normalization)
            for gh_comment in gh_comments:
                gh_comment_normalized = normalize_image_urls(gh_comment['body'])
                
                # Normalize whitespace for comparison
                so_normalized_clean = ' '.join(so_answer_normalized.split())
                gh_normalized_clean = ' '.join(gh_comment_normalized.split())
                
                if so_normalized_clean in gh_normalized_clean:
                    matching_gh_comment = gh_comment
                    break
            
            # If no exact match, try to find best match by text content (excluding images)
            if not matching_gh_comment:
                # Remove image syntax from both texts for comparison
                so_text_only = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', so_answer_body)
                so_text_only = re.sub(r'<img [^>]*>', '', so_text_only)
                so_text_only = so_text_only.strip()
                
                best_match_score = 0
                for gh_comment in gh_comments:
                    # Extract just the text content from GitHub comment (after header)
                    gh_body = gh_comment['body']
                    # Remove the "Originally answered by" header
                    if "> [!NOTE]" in gh_body:
                        lines = gh_body.split('\n')
                        content_lines = []
                        skip_header = True
                        for line in lines:
                            if skip_header and (line.startswith('>') or line.strip() == ''):
                                continue
                            skip_header = False
                            content_lines.append(line)
                        gh_text_content = '\n'.join(content_lines)
                    else:
                        gh_text_content = gh_body
                    
                    # Remove image syntax from GitHub text
                    gh_text_only = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', gh_text_content)
                    gh_text_only = re.sub(r'<img [^>]*>', '', gh_text_only)
                    gh_text_only = gh_text_only.strip()
                    
                    # Simple text similarity check
                    if so_text_only and gh_text_only and so_text_only in gh_text_only:
                        matching_gh_comment = gh_comment
                        break
            
            if matching_gh_comment:
                # Check if all images are present
                gh_comment_images = extract_image_filenames(matching_gh_comment['body'])
                missing_images = so_answer_images - gh_comment_images
                if missing_images:
                    issues.append(f"Missing images in answer: {missing_images}")
            else:
                # If we can't find any matching comment, this is a bigger issue
                if so_answer_images:
                    issues.append(f"Could not find matching answer comment to validate images: {so_answer_images}")
        
        return issues

    def validate_comments(self, so_question: Dict, gh_discussion: Dict) -> List[str]:
        """Validate that comments were transferred correctly.
        
        Comments are structured differently in GitHub Discussions:
        - Stack Overflow question comments → GitHub top-level comments with 'Comment by' prefix
        - Stack Overflow answer comments → GitHub replies to answer comments
        """
        issues = []
        
        # Count SO comments (question + answer comments)
        so_question_comments = len(so_question.get('comments', []))
        so_answer_comments = sum(len(answer.get('comments', [])) for answer in so_question.get('answers', []))
        total_so_comments = so_question_comments + so_answer_comments
        
        # Count GH comments and replies
        # Question comments become top-level comments with 'Comment by' in body
        gh_question_comments = [c for c in gh_discussion['comments']['nodes'] 
                               if 'Comment by' in c['body'] and not c.get('replyTo')]
        
        # Answer comments become replies to answer comments (with 'Originally answered by')
        gh_answer_replies = []
        for comment in gh_discussion['comments']['nodes']:
            if 'Originally answered by' in comment['body']:
                # This is an answer comment, check its replies
                replies = comment.get('replies', {}).get('nodes', [])
                gh_answer_replies.extend(replies)
        
        total_gh_comments = len(gh_question_comments) + len(gh_answer_replies)
        
        if total_so_comments != total_gh_comments:
            issues.append(f"Comment count mismatch: SO={total_so_comments} vs GH={total_gh_comments} (Question comments: SO={so_question_comments} vs GH={len(gh_question_comments)}, Answer comments: SO={so_answer_comments} vs GH={len(gh_answer_replies)})")
        
        return issues

    def validate_migration(self, questions_file: str) -> Dict:
        """Main validation method."""
        logger.info("Starting migration validation...")
        
        # Load Stack Overflow data
        so_questions = load_json(questions_file)
        self.validation_results['total_questions'] = len(so_questions)
        
        # Get GitHub discussions
        gh_discussions = self.get_github_discussions()
        gh_discussions_by_title = {d['title']: d for d in gh_discussions}
        
        logger.info(f"Found {len(so_questions)} SO questions and {len(gh_discussions)} GH discussions")
        
        for i, so_question in enumerate(so_questions):
            so_title = decode_html_entities(so_question.get('title', f"Question #{i+1}"))
            
            if so_title in gh_discussions_by_title:
                self.validation_results['migrated_questions'] += 1
                gh_discussion = gh_discussions_by_title[so_title]
                
                # Validate content
                content_issues = self.validate_question_content(so_question, gh_discussion)
                if content_issues:
                    self.validation_results['content_issues'].append({
                        'id': so_question['question_id'],
                        'title': so_title,
                        'issues': content_issues
                    })
                
                # Validate answers
                answer_issues = self.validate_answers(so_question, gh_discussion)
                if answer_issues:
                    self.validation_results['answer_mismatches'].append({
                        'id': so_question['question_id'],
                        'title': so_title,
                        'issues': answer_issues
                    })
                
                # Validate comments
                comment_issues = self.validate_comments(so_question, gh_discussion)
                if comment_issues:
                    self.validation_results['comment_mismatches'].append({
                        'id': so_question['question_id'],
                        'title': so_title,
                        'issues': comment_issues
                    })
            else:
                self.validation_results['missing_questions'].append(f"{so_question['question_id']} - {so_title}")
        
        return self.validation_results

    def generate_report(self) -> str:
        """Generate a validation report."""
        results = self.validation_results
        success_rate = (results['migrated_questions'] / results['total_questions']) * 100 if results['total_questions'] > 0 else 0
        
        report = f"""
# Migration Validation Report

## Summary
- Total SO Questions: {results['total_questions']}
- Successfully Migrated: {results['migrated_questions']}
- Success Rate: {success_rate:.1f}%
- Missing Questions: {len(results['missing_questions'])}
- Content Issues: {len(results['content_issues'])}
- Answer Mismatches: {len(results['answer_mismatches'])}
- Comment Mismatches: {len(results['comment_mismatches'])}

## Missing Questions
"""
        for title in results['missing_questions']:
            report += f"- {title}\n"

        if results['content_issues']:
            report += "\n## Content Issues\n"
            for issue in results['content_issues']:
                report += f"### {issue['id']} - {issue['title']}\n"
                for problem in issue['issues']:
                    report += f"- {problem}\n"

        if results['answer_mismatches']:
            report += "\n## Answer Issues\n"
            for issue in results['answer_mismatches']:
                report += f"### {issue['id']} - {issue['title']}\n"
                for problem in issue['issues']:
                    report += f"- {problem}\n"

        if results['comment_mismatches']:
            report += "\n## Comment Issues\n"
            for issue in results['comment_mismatches']:
                report += f"### {issue['id']} - {issue['title']}\n"
                for problem in issue['issues']:
                    report += f"- {problem}\n"

        # Add section for unique IDs with issues
        unique_ids = set()
        for issue in results['answer_mismatches']:
            unique_ids.add(issue['id'])
        for issue in results['comment_mismatches']:
            unique_ids.add(issue['id'])
        
        if unique_ids:
            report += "\n## Question IDs with Answer or Comment Issues\n"
            report += "The following question IDs have answer or comment mismatches. These are the question_ids listed in the above sections:\n\n"
            for question_id in sorted(unique_ids):
                report += f"- {question_id}\n"

        return report

def main():
    parser = argparse.ArgumentParser(description='Validate Stack Overflow to GitHub Discussions migration')
    parser.add_argument('--repo', required=True, help='Repository in format owner/name')
    parser.add_argument('--category', required=True, help='Discussion category name')
    parser.add_argument('--questions-file', default='questions_answers_comments.json',
                        help='Path to questions JSON file')
    parser.add_argument('--output', default='validation_report.md',
                        help='Output file for validation report')
    
    args = parser.parse_args()
    
    # Parse repository
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        raise ValueError("Repository must be in format 'owner/name'")
    owner, name = repo_parts
    
    # Initialize GitHub authentication
    github_auth_manager = GitHubAuthManager()
    github_auth_manager.initialize()
    
    # Create validator
    validator = MigrationValidator(github_auth_manager, owner, name, args.category)
    
    # Run validation
    results = validator.validate_migration(args.questions_file)
    
    # Generate and save report
    report = validator.generate_report()
    with open(args.output, 'w') as f:
        f.write(report)
    
    logger.info(f"Validation complete. Report saved to {args.output}")
    logger.info(f"Success rate: {(results['migrated_questions'] / results['total_questions'] * 100):.1f}%")

if __name__ == '__main__':
    main()