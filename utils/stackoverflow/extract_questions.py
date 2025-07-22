#!/usr/bin/env python3
"""
Extract specific questions from questions_answers_comments.json by question_id.
Useful for re-processing questions that failed during populate_discussion.py runs.
"""

import json
import argparse
import sys
from typing import List, Dict, Any, Set
from pathlib import Path

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
                        print(f"Warning: Invalid question_id '{line}' on line {line_num}, skipping")
        print(f"Loaded {len(question_ids)} question IDs from {file_path}")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)
    
    return question_ids

def extract_questions_by_ids(input_file: str, output_file: str, question_ids: List[int]) -> None:
    """Extract specific questions by their question_id values."""
    
    if not question_ids:
        print("Error: No question IDs provided")
        sys.exit(1)
    
    print(f"Looking for {len(question_ids)} question IDs...")
    
    # Load the data
    try:
        with open(input_file, 'r') as f:
            all_questions = json.load(f)
        print(f"Loaded {len(all_questions)} total questions from {input_file}")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{input_file}': {e}")
        sys.exit(1)
    
    # Create a set for faster lookup
    target_ids = set(question_ids)
    
    # Extract matching questions (preserve original order)
    extracted_questions = []
    found_ids = set()
    
    for question in all_questions:
        question_id = question.get('question_id')
        if question_id in target_ids:
            extracted_questions.append(question)
            found_ids.add(question_id)
            print(f"Found question {question_id}: {question.get('title', 'No title')[:60]}...")
    
    # Report results
    missing_ids = target_ids - found_ids
    if missing_ids:
        print(f"\nWarning: {len(missing_ids)} question IDs not found:")
        for missing_id in sorted(missing_ids):
            print(f"  - {missing_id}")
    
    if not extracted_questions:
        print("No matching questions found!")
        sys.exit(1)
    
    # Save to new file
    try:
        with open(output_file, 'w') as f:
            json.dump(extracted_questions, f, indent=2)
        print(f"\nSuccessfully extracted {len(extracted_questions)} questions to '{output_file}'")
        
        # Print summary statistics
        total_answers = sum(len(q.get('answers', [])) for q in extracted_questions)
        total_comments = sum(len(q.get('comments', [])) for q in extracted_questions)
        for q in extracted_questions:
            for answer in q.get('answers', []):
                total_comments += len(answer.get('comments', []))
        
        print(f"Summary:")
        print(f"  - Questions: {len(extracted_questions)}")
        print(f"  - Answers: {total_answers}")
        print(f"  - Comments: {total_comments}")
        
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Extract specific questions from questions_answers_comments.json by question_id',
        epilog='''
Examples:
  # Extract specific question IDs from command line
  python extract_questions.py --ids 1354 1320 1321 --output failed_questions.json
  
  # Extract question IDs from a file
  python extract_questions.py --file failed_ids.txt --output retry_questions.json
  
  # Use different input file
  python extract_questions.py --input backup_questions.json --ids 1354 --output single_question.json
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input/output files
    parser.add_argument('--input', '-i', 
                       default='questions_answers_comments.json',
                       help='Input JSON file (default: questions_answers_comments.json)')
    parser.add_argument('--output', '-o', 
                       required=True,
                       help='Output JSON file for extracted questions')
    
    # Question ID sources (mutually exclusive)
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument('--ids', 
                         type=int, 
                         nargs='+',
                         help='Question IDs to extract (space-separated)')
    id_group.add_argument('--file', '-f',
                         help='File containing question IDs (one per line)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    # Get question IDs from appropriate source
    if args.ids:
        question_ids = args.ids
        print(f"Using {len(question_ids)} question IDs from command line")
    else:
        question_ids = load_question_ids_from_file(args.file)
    
    # Remove duplicates while preserving order
    unique_ids = []
    seen = set()
    for qid in question_ids:
        if qid not in seen:
            unique_ids.append(qid)
            seen.add(qid)
    
    if len(unique_ids) != len(question_ids):
        print(f"Removed {len(question_ids) - len(unique_ids)} duplicate IDs")
    
    # Extract questions
    extract_questions_by_ids(args.input, args.output, unique_ids)

if __name__ == '__main__':
    main()
