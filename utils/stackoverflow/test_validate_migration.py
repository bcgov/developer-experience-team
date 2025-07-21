import unittest
from unittest.mock import Mock, patch
from validate_migration import MigrationValidator, extract_image_filenames, normalize_image_urls
from populate_discussion_helpers import GitHubAuthManager


class TestImageHandling(unittest.TestCase):
    """Unit tests for image handling functions."""

    def test_extract_image_filenames_markdown(self):
        """Test extracting image filenames from markdown syntax."""
        text = "Here's an image: ![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)"
        filenames = extract_image_filenames(text)
        self.assertEqual(filenames, {"3545-sdfkb-adf2.png"})

    def test_extract_image_filenames_html(self):
        """Test extracting image filenames from HTML syntax."""
        text = 'Check this: <img src="https://github.com/bcgov/repo/blob/main/discussion_images/test-image.jpg?raw=true" alt="test">'
        filenames = extract_image_filenames(text)
        self.assertEqual(filenames, {"test-image.jpg"})

    def test_extract_image_filenames_mixed(self):
        """Test extracting image filenames from mixed markdown and HTML."""
        text = '''
        ![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)
        <img src="https://github.com/bcgov/repo/blob/main/discussion_images/test-image.jpg?raw=true">
        '''
        filenames = extract_image_filenames(text)
        self.assertEqual(filenames, {"3545-sdfkb-adf2.png", "test-image.jpg"})

    def test_extract_image_filenames_empty(self):
        """Test extracting image filenames from text with no images."""
        text = "This text has no images in it."
        filenames = extract_image_filenames(text)
        self.assertEqual(filenames, set())

    def test_normalize_image_urls_markdown(self):
        """Test normalizing markdown image URLs."""
        text = "![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)"
        normalized = normalize_image_urls(text)
        self.assertEqual(normalized, "![screenshot](IMAGE:3545-sdfkb-adf2.png)")

    def test_normalize_image_urls_html(self):
        """Test normalizing HTML image URLs."""
        text = '<img src="https://github.com/bcgov/repo/blob/main/discussion_images/test-image.jpg?raw=true" alt="test">'
        normalized = normalize_image_urls(text)
        self.assertIn("IMAGE:test-image.jpg", normalized)
        self.assertIn('alt="test"', normalized)

    def test_normalize_image_urls_matching(self):
        """Test that different URLs with same filename normalize to same result."""
        so_text = "![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)"
        gh_text = "![screenshot](https://github.com/bcgov/repo/blob/main/discussion_images/3545-sdfkb-adf2.png?raw=true)"
        
        so_normalized = normalize_image_urls(so_text)
        gh_normalized = normalize_image_urls(gh_text)
        
        self.assertEqual(so_normalized, gh_normalized)


class TestMigrationValidator(unittest.TestCase):
    """Unit tests for the MigrationValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock auth manager
        self.mock_auth_manager = Mock(spec=GitHubAuthManager)
        self.mock_auth_manager.get_token.return_value = "test_token"
        self.mock_auth_manager.is_initialized = True
        
        self.validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A"
        )

    def test_validate_question_content_perfect_match(self):
        """Test validation when SO question and GH discussion match perfectly."""
        so_question = {
            "title": "How do I connect to VPN?",
            "body": "I need help connecting to the BC Gov VPN.",
            "body_markdown": "I need help connecting to the BC Gov VPN.",
            "tags": ["vpn", "networking", "help"]
        }
        
        gh_discussion = {
            "title": "How do I connect to VPN?",
            "body": "> [!NOTE]\n> Originally asked by user123 on 2024-01-15\n\nI need help connecting to the BC Gov VPN.",
            "labels": {
                "nodes": [
                    {"name": "vpn"},
                    {"name": "networking"},
                    {"name": "help"}
                ]
            }
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_question_content_title_mismatch(self):
        """Test validation when titles don't match."""
        so_question = {
            "title": "How do I connect to VPN?",
            "body": "I need help connecting to the BC Gov VPN.",
            "tags": ["vpn"]
        }
        
        gh_discussion = {
            "title": "How to connect to VPN?",
            "body": "I need help connecting to the BC Gov VPN.",
            "labels": {"nodes": [{"name": "vpn"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Title mismatch", issues[0])

    def test_validate_question_content_html_entities(self):
        """Test validation with HTML entities in SO title."""
        so_question = {
            "title": "How can I check if I&#39;m connected to VPN?",
            "body": "I need to check my VPN connection.",
            "tags": ["vpn"]
        }
        
        gh_discussion = {
            "title": "How can I check if I'm connected to VPN?",
            "body": "I need to check my VPN connection.",
            "labels": {"nodes": [{"name": "vpn"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_question_content_different_body(self):
        """Test validation when body content is different."""
        so_question = {
            "title": "VPN Connection Help",
            "body": "I need help with VPN connection troubleshooting.",
            "tags": ["vpn"]
        }
        
        gh_discussion = {
            "title": "VPN Connection Help",
            "body": "This is completely different content.",
            "labels": {"nodes": [{"name": "vpn"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Body content not found", issues[0])

    def test_validate_question_content_missing_tags(self):
        """Test validation when tags are missing."""
        so_question = {
            "title": "VPN Help",
            "body": "Need VPN help.",
            "tags": ["vpn", "networking", "troubleshooting"]
        }
        
        gh_discussion = {
            "title": "VPN Help",
            "body": "Need VPN help.",
            "labels": {"nodes": [{"name": "vpn"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing tags:", issues[0])
        # Check that both missing tags are mentioned, regardless of order
        self.assertIn("networking", issues[0])
        self.assertIn("troubleshooting", issues[0])

    def test_validate_question_content_with_images_matching(self):
        """Test validation when images are present and match between SO and GH."""
        so_question = {
            "title": "How to configure OpenShift?",
            "body": "Here's my setup: ![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)",
            "tags": ["openshift"]
        }
        
        gh_discussion = {
            "title": "How to configure OpenShift?",
            "body": "> [!NOTE]\n> Originally asked by user123 on 2024-01-15\n\nHere's my setup: ![screenshot](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/3545-sdfkb-adf2.png?raw=true)",
            "labels": {"nodes": [{"name": "openshift"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_question_content_with_images_missing(self):
        """Test validation when images are missing in GitHub discussion."""
        so_question = {
            "title": "How to configure OpenShift?",
            "body": "Here's my setup: ![screenshot](https://stackoverflow.developer.gov.bc.ca/images/a/3545-sdfkb-adf2.png)",
            "tags": ["openshift"]
        }
        
        gh_discussion = {
            "title": "How to configure OpenShift?",
            "body": "> [!NOTE]\n> Originally asked by user123 on 2024-01-15\n\nHere's my setup: (image missing)",
            "labels": {"nodes": [{"name": "openshift"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing images:", issues[0])
        self.assertIn("3545-sdfkb-adf2.png", issues[0])

    def test_validate_question_content_with_multiple_images(self):
        """Test validation with multiple images in question body."""
        so_question = {
            "title": "Multiple screenshots",
            "body": '''Here are two images:
            ![first](https://stackoverflow.developer.gov.bc.ca/images/a/image1.png)
            <img src="https://stackoverflow.developer.gov.bc.ca/images/b/image2.jpg" alt="second">''',
            "tags": ["help"]
        }
        
        gh_discussion = {
            "title": "Multiple screenshots", 
            "body": '''> [!NOTE]\n> Originally asked by user123 on 2024-01-15\n\nHere are two images:
            ![first](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/image1.png?raw=true)
            <img src="https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/image2.jpg?raw=true" alt="second">''',
            "labels": {"nodes": [{"name": "help"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_question_content_with_different_image_urls_same_content(self):
        """Test that different image URLs don't cause false positive content mismatches."""
        so_question = {
            "title": "Image URL Test",
            "body": "Check this image: ![test](https://stackoverflow.developer.gov.bc.ca/images/a/test.png) and this text after.",
            "tags": ["test"]
        }
        
        gh_discussion = {
            "title": "Image URL Test",
            "body": "> [!NOTE]\n> Originally asked by user123 on 2024-01-15\n\nCheck this image: ![test](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/test.png?raw=true) and this text after.",
            "labels": {"nodes": [{"name": "test"}]}
        }
        
        issues = self.validator.validate_question_content(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_answers_perfect_match(self):
        """Test validation when answer counts match perfectly."""
        so_question = {
            "answers": [
                {
                    "answer_id": 1,
                    "body": "Try connecting to vpn.gov.bc.ca",
                    "is_accepted": True
                },
                {
                    "answer_id": 2,
                    "body": "You can also use vpn2.gov.bc.ca",
                    "is_accepted": False
                }
            ],
            "accepted_answer_id": 1
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nTry connecting to vpn.gov.bc.ca",
                        "isAnswer": True
                    },
                    {
                        "body": "> [!NOTE]\n> Originally answered by user2 on 2024-01-15\n\nYou can also use vpn2.gov.bc.ca",
                        "isAnswer": False
                    }
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_answers_count_mismatch(self):
        """Test validation when answer counts don't match."""
        so_question = {
            "answers": [
                {"answer_id": 1, "body": "Answer 1"},
                {"answer_id": 2, "body": "Answer 2"},
                {"answer_id": 3, "body": "Answer 3"}
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Originally answered by user1\n\nAnswer 1", "isAnswer": False},
                    {"body": "> [!NOTE]\n> Originally answered by user2\n\nAnswer 2", "isAnswer": False}
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Answer count mismatch: SO=3 vs GH=2", issues[0])

    def test_validate_answers_accepted_answer_missing(self):
        """Test validation when accepted answer is not marked in GitHub."""
        so_question = {
            "answers": [
                {"answer_id": 1, "body": "Answer 1", "is_accepted": True}
            ],
            "accepted_answer_id": 1
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Originally answered by user1\n\nAnswer 1", "isAnswer": False}
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Accepted answer not properly marked", issues[0])

    def test_validate_answers_false_accepted_answer(self):
        """Test validation when GitHub has accepted answer but SO doesn't."""
        so_question = {
            "answers": [
                {"answer_id": 1, "body": "Answer 1", "is_accepted": False}
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Originally answered by user1\n\nAnswer 1", "isAnswer": True}
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("GitHub has accepted answer but SO doesn't", issues[0])

    def test_validate_answers_no_answers(self):
        """Test validation when there are no answers."""
        so_question = {
            "answers": []
        }
        
        gh_discussion = {
            "comments": {
                "nodes": []
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_answers_with_images_matching(self):
        """Test validation when answer images match between SO and GH."""
        so_question = {
            "answers": [
                {
                    "answer_id": 1,
                    "body": "Try this solution: ![solution](https://stackoverflow.developer.gov.bc.ca/images/a/solution.png)",
                    "is_accepted": True
                }
            ],
            "accepted_answer_id": 1
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nTry this solution: ![solution](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/solution.png?raw=true)",
                        "isAnswer": True
                    }
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_answers_with_images_missing(self):
        """Test validation when answer images are missing in GitHub."""
        so_question = {
            "answers": [
                {
                    "answer_id": 1,
                    "body": "Check this diagram: ![diagram](https://stackoverflow.developer.gov.bc.ca/images/a/diagram.png)",
                    "is_accepted": False
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nCheck this diagram: (diagram missing)",
                        "isAnswer": False
                    }
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing images in answer:", issues[0])
        self.assertIn("diagram.png", issues[0])

    def test_validate_answers_with_multiple_images_in_answer(self):
        """Test validation with multiple images in a single answer."""
        so_question = {
            "answers": [
                {
                    "answer_id": 1,
                    "body": '''Here's the complete solution:
                    ![step1](https://stackoverflow.developer.gov.bc.ca/images/a/step1.png)
                    <img src="https://stackoverflow.developer.gov.bc.ca/images/b/step2.jpg" alt="step2">
                    Follow these steps.''',
                    "is_accepted": True
                }
            ],
            "accepted_answer_id": 1
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nHere's the complete solution:\n![step1](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/step1.png?raw=true)\n<img src=\"https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/step2.jpg?raw=true\" alt=\"step2\">\nFollow these steps.",
                        "isAnswer": True
                    }
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_answers_with_partial_missing_images(self):
        """Test validation when some but not all images are missing from answers."""
        so_question = {
            "answers": [
                {
                    "answer_id": 1,
                    "body": '''Solution with images:
                    ![present](https://stackoverflow.developer.gov.bc.ca/images/a/present.png)
                    ![missing](https://stackoverflow.developer.gov.bc.ca/images/a/missing.png)''',
                    "is_accepted": False
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nSolution with images:\n![present](https://github.com/bcgov/gh-discussions-lab/blob/main/discussion_images/present.png?raw=true)\n(second image missing)",
                        "isAnswer": False
                    }
                ]
            }
        }
        
        issues = self.validator.validate_answers(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Missing images in answer:", issues[0])
        self.assertIn("missing.png", issues[0])
        self.assertNotIn("present.png", issues[0])

    def test_validate_comments_perfect_match(self):
        """Test validation when comment counts match perfectly."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Great question!"},
                {"comment_id": 2, "body": "I have the same issue."}
            ],
            "answers": [
                {
                    "answer_id": 1,
                    "comments": [
                        {"comment_id": 3, "body": "This worked for me!"},
                        {"comment_id": 4, "body": "Thanks for the solution."}
                    ]
                },
                {
                    "answer_id": 2,
                    "comments": [
                        {"comment_id": 5, "body": "Alternative approach."}
                    ]
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Comment by user1 on 2024-01-15\n\nGreat question!"},
                    {"body": "> [!NOTE]\n> Comment by user2 on 2024-01-15\n\nI have the same issue."},
                    {"body": "> [!NOTE]\n> Comment by user3 on 2024-01-15\n\nThis worked for me!"},
                    {"body": "> [!NOTE]\n> Comment by user4 on 2024-01-15\n\nThanks for the solution."},
                    {"body": "> [!NOTE]\n> Comment by user5 on 2024-01-15\n\nAlternative approach."}
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_count_mismatch(self):
        """Test validation when comment counts don't match."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Comment 1"},
                {"comment_id": 2, "body": "Comment 2"}
            ],
            "answers": [
                {
                    "answer_id": 1,
                    "comments": [
                        {"comment_id": 3, "body": "Answer comment 1"}
                    ]
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Comment by user1\n\nComment 1"},
                    {"body": "> [!NOTE]\n> Comment by user2\n\nComment 2"}
                    # Missing the answer comment
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Comment count mismatch: SO=3 vs GH=2", issues[0])

    def test_validate_comments_no_comments(self):
        """Test validation when there are no comments."""
        so_question = {
            "comments": [],
            "answers": [
                {
                    "answer_id": 1,
                    "comments": []
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": []
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_mixed_content(self):
        """Test validation when GH has mixed content (answers and comments)."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Question comment"}
            ],
            "answers": [
                {
                    "answer_id": 1,
                    "body": "This is an answer, not a comment",
                    "comments": [
                        {"comment_id": 2, "body": "Answer comment"}
                    ]
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Comment by user1\n\nQuestion comment"},
                    {"body": "> [!NOTE]\n> Originally answered by user2\n\nThis is an answer, not a comment"},
                    {"body": "> [!NOTE]\n> Comment by user3\n\nAnswer comment"}
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_missing_answer_structure(self):
        """Test validation when there are no answers."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Only question comment"}
            ]
            # Missing "answers" key
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {"body": "> [!NOTE]\n> Comment by user1\n\nOnly question comment"}
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)


if __name__ == '__main__':
    unittest.main()
