import unittest
from unittest.mock import Mock, patch
from validate_migration import MigrationValidator, extract_image_filenames, normalize_image_urls
from populate_discussion_helpers import GitHubAuthManager
from populate_discussion import POPULAR_TAG_NAME

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

    def test_validate_question_content_has_low_usage_tag(self):
        """Test validation when a low usage tag is present."""
        so_question = {
            "title": "VPN Help",
            "body": "Need VPN help.",
            "tags": ["vpn", "networking", "troubleshooting"]
        }

        gh_discussion = {
            "title": "VPN Help",
            "body": "Need VPN help.",
            "labels": {"nodes": [{"name": "vpn"}, {"name": "troubleshooting"}]}
        }

        mock_low_usage_tags_data = ["networking", "help"]

        issues = self.validator.validate_question_content(so_question, gh_discussion, mock_low_usage_tags_data)
        self.assertEqual(len(issues), 0)

    def test_validate_question_content_missing_mixed_missing_and_low_usage_tag(self):
        """Test validation when a low usage tag is present."""
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

        mock_low_usage_tags_data = ["networking", "help"]

        issues = self.validator.validate_question_content(so_question, gh_discussion, mock_low_usage_tags_data)
        self.assertEqual(len(issues), 1)    
        self.assertIn("Missing tags:", issues[0])
        # Check that both missing tags are mentioned, regardless of order
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
        self.assertEqual(len(issues), 2)
        self.assertIn("Missing images:", issues[0])
        self.assertIn("3545-sdfkb-adf2.png", issues[0])
        self.assertIn("Body content not found", issues[1])

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
        """Test validation when comment counts match perfectly with reply structure."""
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
                    # Question comments (top-level)
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1 on 2024-01-15\n\nGreat question!",
                        "replyTo": None
                    },
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user2 on 2024-01-15\n\nI have the same issue.",
                        "replyTo": None
                    },
                    # Answer comments (with replies)
                    {
                        "body": "> [!NOTE]\n> Originally answered by user3 on 2024-01-15\n\nFirst answer content",
                        "replies": {
                            "nodes": [
                                {"body": "This worked for me!"},
                                {"body": "Thanks for the solution."}
                            ]
                        }
                    },
                    {
                        "body": "> [!NOTE]\n> Originally answered by user4 on 2024-01-15\n\nSecond answer content",
                        "replies": {
                            "nodes": [
                                {"body": "Alternative approach."}
                            ]
                        }
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_count_mismatch(self):
        """Test validation when comment counts don't match with reply structure."""
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
                    # Question comments (correct)
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nComment 1",
                        "replyTo": None
                    },
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user2\n\nComment 2",
                        "replyTo": None
                    },
                    # Answer with missing reply
                    {
                        "body": "> [!NOTE]\n> Originally answered by user3\n\nAnswer content",
                        "replies": {
                            "nodes": []  # Missing the answer comment
                        }
                    }
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
        """Test validation when GH has mixed content (answers and comments) with reply structure."""
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
                    # Question comment (top-level)
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nQuestion comment",
                        "replyTo": None
                    },
                    # Answer with reply
                    {
                        "body": "> [!NOTE]\n> Originally answered by user2\n\nThis is an answer, not a comment",
                        "replies": {
                            "nodes": [
                                {"body": "Answer comment"}
                            ]
                        }
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_missing_answer_structure(self):
        """Test validation when there are no answers with reply structure."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Only question comment"}
            ]
            # Missing "answers" key
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nOnly question comment",
                        "replyTo": None
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_with_reply_structure(self):
        """Test validation specifically for the reply-to structure."""
        so_question = {
            "comments": [],  # No question comments
            "answers": [
                {
                    "answer_id": 1,
                    "comments": [
                        {"comment_id": 1, "body": "Reply 1 to answer"},
                        {"comment_id": 2, "body": "Reply 2 to answer"}
                    ]
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1\n\nAnswer content here",
                        "replies": {
                            "nodes": [
                                {"body": "Reply 1 to answer"},
                                {"body": "Reply 2 to answer"}
                            ]
                        }
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)

    def test_validate_comments_missing_replies_structure(self):
        """Test validation when GitHub discussion is missing replies structure."""
        so_question = {
            "comments": [],
            "answers": [
                {
                    "answer_id": 1,
                    "comments": [
                        {"comment_id": 1, "body": "Answer comment"}
                    ]
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1\n\nAnswer content",
                        # Missing "replies" key entirely
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        self.assertIn("Comment count mismatch: SO=1 vs GH=0", issues[0])

    def test_validate_comments_question_vs_answer_breakdown(self):
        """Test that the error message includes detailed breakdown of question vs answer comments."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Question comment 1"},
                {"comment_id": 2, "body": "Question comment 2"}
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
        
        # GitHub is missing one question comment
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nQuestion comment 1",
                        "replyTo": None
                    },
                    # Missing second question comment
                    {
                        "body": "> [!NOTE]\n> Originally answered by user2\n\nAnswer content",
                        "replies": {
                            "nodes": [
                                {"body": "Answer comment 1"}
                            ]
                        }
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 1)
        # Should include detailed breakdown
        self.assertIn("Question comments: SO=2 vs GH=1", issues[0])
        self.assertIn("Answer comments: SO=1 vs GH=1", issues[0])

    def test_validate_comments_with_replyTo_field(self):
        """Test validation when GitHub comments have replyTo field set."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Question comment"}
            ],
            "answers": []
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nQuestion comment",
                        "replyTo": None  # Top-level question comment
                    },
                    {
                        "body": "This should not be counted as it has replyTo",
                        "replyTo": {"id": "some_id"}  # This is a reply, not a top-level comment
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)  # Should match: 1 SO question comment = 1 GH top-level comment

    def test_validate_comments_complex_structure(self):
        """Test validation with a complex mix of question comments, answers, and replies."""
        so_question = {
            "comments": [
                {"comment_id": 1, "body": "Question comment 1"},
                {"comment_id": 2, "body": "Question comment 2"}
            ],
            "answers": [
                {
                    "answer_id": 1,
                    "comments": [
                        {"comment_id": 3, "body": "Answer 1 comment 1"},
                        {"comment_id": 4, "body": "Answer 1 comment 2"}
                    ]
                },
                {
                    "answer_id": 2,
                    "comments": []  # Answer with no comments
                }
            ]
        }
        
        gh_discussion = {
            "comments": {
                "nodes": [
                    # Question comments
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user1\n\nQuestion comment 1",
                        "replyTo": None
                    },
                    {
                        "body": "> [!NOTE]\n> Originally commented on by user2\n\nQuestion comment 2",
                        "replyTo": None
                    },
                    # First answer with replies
                    {
                        "body": "> [!NOTE]\n> Originally answered by user3\n\nFirst answer content",
                        "replies": {
                            "nodes": [
                                {"body": "Answer 1 comment 1"},
                                {"body": "Answer 1 comment 2"}
                            ]
                        }
                    },
                    # Second answer with no replies
                    {
                        "body": "> [!NOTE]\n> Originally answered by user4\n\nSecond answer content",
                        "replies": {
                            "nodes": []
                        }
                    }
                ]
            }
        }
        
        issues = self.validator.validate_comments(so_question, gh_discussion)
        self.assertEqual(len(issues), 0)  # 2 question + 2 answer comments = 4 total


class TestIgnoredTagsFunctionality(unittest.TestCase):
    """Unit tests for the ignored tags functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_auth_manager = Mock(spec=GitHubAuthManager)
        self.mock_auth_manager.get_token.return_value = "test_token"
        self.mock_auth_manager.is_initialized = True

    def test_process_question_with_ignored_tag_single(self):
        """Test that questions with a single ignored tag are categorized correctly."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated"]
        )
        
        so_question = {
            "question_id": 123,
            "title": "Old deprecated feature help",
            "tags": ["deprecated", "old-feature"]
        }
        
        gh_discussions_by_title = {}  # Question not migrated
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Check that question is in ignored list, not missing list
        self.assertEqual(len(validator.validation_results['ignored_questions']), 1)
        self.assertEqual(len(validator.validation_results['missing_questions']), 0)
        self.assertIn("123 - Old deprecated feature help", validator.validation_results['ignored_questions'][0])
        self.assertIn("deprecated", validator.validation_results['ignored_questions'][0])

    def test_process_question_with_ignored_tag_multiple(self):
        """Test that questions with multiple ignored tags are categorized correctly."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated", "obsolete", "archived"]
        )
        
        so_question = {
            "question_id": 456,
            "title": "Help with archived system",
            "tags": ["archived", "legacy", "systems"]
        }
        
        gh_discussions_by_title = {}  # Question not migrated
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        self.assertEqual(len(validator.validation_results['ignored_questions']), 1)
        self.assertEqual(len(validator.validation_results['missing_questions']), 0)
        self.assertIn("456 - Help with archived system", validator.validation_results['ignored_questions'][0])

    def test_process_question_without_ignored_tags(self):
        """Test that questions without ignored tags go to missing list when not found."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated"]
        )
        
        so_question = {
            "question_id": 789,
            "title": "Current feature help",
            "tags": ["current", "active-feature"]
        }
        
        gh_discussions_by_title = {}  # Question not migrated
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Check that question is in missing list, not ignored list
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 1)
        self.assertIn("789 - Current feature help", validator.validation_results['missing_questions'][0])

    def test_process_question_no_ignored_tags_configured(self):
        """Test behavior when no ignored tags are configured."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=None  # No ignored tags
        )
        
        so_question = {
            "question_id": 111,
            "title": "Any question",
            "tags": ["any", "tags"]
        }
        
        gh_discussions_by_title = {}
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Should go to missing since no ignored tags configured
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 1)

    def test_process_question_empty_ignored_tags_list(self):
        """Test behavior when ignored tags list is empty."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=[]  # Empty list
        )
        
        so_question = {
            "question_id": 222,
            "title": "Another question",
            "tags": ["some", "tags"]
        }
        
        gh_discussions_by_title = {}
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Should go to missing since ignored tags list is empty
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 1)

    def test_process_question_found_in_discussions_ignores_tags(self):
        """Test that found questions are processed normally regardless of ignored tags."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["legacy"]
        )
        
        so_question = {
            "question_id": 333,
            "title": "Found question with legacy tag",
            "body": "This question was migrated",
            "tags": ["legacy", "migrated"]
        }

        gh_discussion = {
            "title": "Found question with legacy tag",
            "body": "This question was migrated",
            "labels": {"nodes": [{"name": "legacy"}, {"name": "migrated"}]},
            "comments": {
                "nodes": [
                    {
                        "body": "> [!NOTE]\n> Originally answered by user1 on 2024-01-15\n\nTry this solution",
                        "isAnswer": True
                    }
                ]
            }
        }
        
        gh_discussions_by_title = {"Found question with legacy tag": gh_discussion}
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Should be processed as migrated, not ignored
        self.assertEqual(validator.validation_results['migrated_questions'], 1)
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 0)

    @patch('validate_migration.load_json')
    def test_validate_migration_with_ignored_tags_integration(self, mock_load_json):
        """Integration test for the full validate_migration method with ignored tags."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated", "legacy"]
        )

        validator.get_popular_so_questions_sql = Mock(return_value=[])
        
        # Mock the SO questions data
        mock_so_questions = [
            {
                "question_id": 1,
                "title": "Current Question",
                "tags": ["current", "active"]
            },
            {
                "question_id": 2,
                "title": "Legacy Question",
                "tags": ["legacy", "old"]
            },
            {
                "question_id": 3,
                "title": "Deprecated Feature",
                "tags": ["deprecated"]
            },
            {
                "question_id": 4,
                "title": "Mixed Tags Question",
                "tags": ["current", "deprecated"]
            }
        ]
        
        # Mock the tags data (second file parameter)
        mock_tags_data = [
            {
                "count": 145,
                "name": "openshift"
            },
            {
                "count": 32,
                "name": "keycloak"
            },
            {
                "count": 26,
                "name": "security"
            },
            {
                "count": 15,
                "name": "deprecated"
            },
            {
                "count": 10,
                "name": "legacy"
            }
        ]
        
        # Configure mock to return different data based on which file is being loaded
        def mock_load_json_side_effect(file_path):
            if "mock_tag_file.json" in file_path:
                return mock_tags_data
            else:
                return mock_so_questions
        
        mock_load_json.side_effect = mock_load_json_side_effect
        
        # Mock get_github_discussions to return empty (none migrated)
        validator.get_github_discussions = Mock(return_value=[])
        
        results = validator.validate_migration("mock_so_file.json", "mock_tag_file.json")
        
        # Check results
        self.assertEqual(results['total_questions'], 4)
        self.assertEqual(results['migrated_questions'], 0)
        self.assertEqual(len(results['missing_questions']), 1)  # Only "Current Question"
        self.assertEqual(len(results['ignored_questions']), 3)  # Legacy, Deprecated, and Mixed
        
        # Verify specific questions
        self.assertIn("1 - Current Question", results['missing_questions'][0])
        
        ignored_ids = [entry.split(' - ')[0] for entry in results['ignored_questions']]
        self.assertIn("2", ignored_ids)  # Legacy Question
        self.assertIn("3", ignored_ids)  # Deprecated Feature  
        self.assertIn("4", ignored_ids)  # Mixed Tags Question

    def test_process_question_question_without_tags(self):
        """Test behavior when SO question has no tags."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated"]
        )
        
        so_question = {
            "question_id": 444,
            "title": "Question without tags"
            # No tags field
        }
        
        gh_discussions_by_title = {}
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Should go to missing since no tags to check against ignored list
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 1)

    def test_process_question_empty_tags_list(self):
        """Test behavior when SO question has empty tags list."""
        validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            ignored_tags=["deprecated"]
        )
        
        so_question = {
            "question_id": 555,
            "title": "Question with empty tags",
            "tags": []  # Empty tags list
        }
        
        gh_discussions_by_title = {}
        
        validator.process_question(so_question, gh_discussions_by_title)
        
        # Should go to missing since no tags to match
        self.assertEqual(len(validator.validation_results['ignored_questions']), 0)
        self.assertEqual(len(validator.validation_results['missing_questions']), 1)

class TestPopularTagFunctionality(unittest.TestCase):
    """Unit tests for the popular tag functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_auth_manager = Mock(spec=GitHubAuthManager)
        self.mock_auth_manager.get_token.return_value = "test_token"
        self.mock_auth_manager.is_initialized = True
        
        self.validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            popular_tag_min_threshold=300
        )

    def test_get_popular_so_questions_basic(self):
        """Test getting popular SO questions with basic functionality."""
        # Mock the SQL method to return a list of titles
        self.validator.get_popular_so_questions_sql = Mock(return_value=[
            "How to configure VPN?",
            "OpenShift setup guide", 
            "Database connection issues"
        ])
        
        result = self.validator.get_popular_so_questions("test_file.json")
        
        expected = {
            "How to configure VPN?",
            "OpenShift setup guide", 
            "Database connection issues"
        }
        self.assertEqual(result, expected)
        
        # Verify SQL method was called with correct file
        self.validator.get_popular_so_questions_sql.assert_called_once_with("test_file.json")

    def test_get_popular_so_questions_with_html_entities(self):
        """Test getting popular SO questions with HTML entity decoding."""
        # Mock the SQL method to return titles with HTML entities
        self.validator.get_popular_so_questions_sql = Mock(return_value=[
            "How to use &quot;quotes&quot; in config?",
            "Setup &amp; configuration guide"
        ])
        
        result = self.validator.get_popular_so_questions("test_file.json")
        
        expected = {
            'How to use "quotes" in config?',
            "Setup & configuration guide"
        }
        self.assertEqual(result, expected)

    def test_get_popular_so_questions_empty_result(self):
        """Test getting popular SO questions when no questions meet threshold."""
        # Mock the SQL method to return empty list
        self.validator.get_popular_so_questions_sql = Mock(return_value=[])
        
        result = self.validator.get_popular_so_questions("test_file.json")
        
        self.assertEqual(result, set())


    def test_validate_popular_tags_perfect_match(self):
        """Test validation when popular tags match perfectly between SO and GH."""
        # Set up SO popular questions
        self.validator.get_popular_so_questions = Mock(return_value={
            "Popular Question 1",
            "Popular Question 2",
            "Popular Question 3"
        })
        
        # Set up GH popular questions (questions with popular tag)
        self.validator.popular_gh_questions = {
            "Popular Question 1",
            "Popular Question 2", 
            "Popular Question 3"
        }
        
        self.validator.validate_popular_tags("test_file.json")
        
        # Should have no issues when they match perfectly
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['missing_popular_tag'], 
            []
        )
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['tagged_as_popular_but_are_not'], 
            []
        )

    def test_validate_popular_tags_missing_popular_tag(self):
        """Test validation when SO questions should be popular but aren't tagged in GH."""
        # SO has popular questions
        self.validator.get_popular_so_questions = Mock(return_value={
            "Should be popular 1",
            "Should be popular 2",
            "Already tagged popular"
        })
        
        # GH only has one of them tagged as popular
        self.validator.popular_gh_questions = {
            "Already tagged popular"
        }
        
        self.validator.validate_popular_tags("test_file.json")
        
        # Should identify missing popular tags
        missing = self.validator.validation_results['popular_question_issues']['missing_popular_tag']
        self.assertEqual(missing, {"Should be popular 1", "Should be popular 2"})
        
        # Should have no false positives
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['tagged_as_popular_but_are_not'], 
            []
        )

    def test_validate_popular_tags_tagged_as_popular_but_are_not(self):
        """Test validation when GH questions are tagged popular but don't meet SO threshold."""
        # SO has no popular questions (or different ones)
        self.validator.get_popular_so_questions = Mock(return_value={
            "Actually popular question"
        })
        
        # GH has questions incorrectly tagged as popular
        self.validator.popular_gh_questions = {
            "Actually popular question",
            "Incorrectly tagged as popular 1",
            "Incorrectly tagged as popular 2"
        }
        
        self.validator.validate_popular_tags("test_file.json")
        
        # Should have no missing popular tags
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['missing_popular_tag'], 
            []
        )
        
        # Should identify incorrectly tagged questions
        incorrect = self.validator.validation_results['popular_question_issues']['tagged_as_popular_but_are_not']
        self.assertEqual(incorrect, {"Incorrectly tagged as popular 1", "Incorrectly tagged as popular 2"})

    def test_validate_popular_tags_mixed_issues(self):
        """Test validation when there are both missing and incorrectly tagged questions."""
        # SO popular questions
        self.validator.get_popular_so_questions = Mock(return_value={
            "Should be popular but isn't tagged",
            "Correctly tagged popular",
            "Another missing popular"
        })
        
        # GH popular questions (mix of correct and incorrect)
        self.validator.popular_gh_questions = {
            "Correctly tagged popular",
            "Incorrectly tagged as popular",
            "Another incorrect popular"
        }
        
        self.validator.validate_popular_tags("test_file.json")
        
        # Should identify missing popular tags
        missing = self.validator.validation_results['popular_question_issues']['missing_popular_tag']
        self.assertEqual(missing, {"Should be popular but isn't tagged", "Another missing popular"})
        
        # Should identify incorrectly tagged questions
        incorrect = self.validator.validation_results['popular_question_issues']['tagged_as_popular_but_are_not']
        self.assertEqual(incorrect, {"Incorrectly tagged as popular", "Another incorrect popular"})

    def test_validate_popular_tags_no_popular_questions(self):
        """Test validation when there are no popular questions in either system."""
        # No popular questions in SO
        self.validator.get_popular_so_questions = Mock(return_value=set())
        
        # No popular questions in GH
        self.validator.popular_gh_questions = set()
        
        self.validator.validate_popular_tags("test_file.json")
        
        # Should have no issues
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['missing_popular_tag'], 
            []
        )
        self.assertEqual(
            self.validator.validation_results['popular_question_issues']['tagged_as_popular_but_are_not'], 
            []
        )

    def test_popular_gh_questions_tracking(self):
        """Test that popular_gh_questions set is populated during question validation."""
        so_question = {
            "title": "Test Question",
            "body": "Test body",
            "tags": ["test"]
        }
        
        # GH discussion with popular tag
        gh_discussion = {
            "title": "Test Question",
            "body": "Test body",
            "labels": {
                "nodes": [
                    {"name": "test"},
                    {"name": POPULAR_TAG_NAME}  # This should be tracked
                ]
            }
        }
        
        # Initially empty
        self.assertEqual(len(self.validator.popular_gh_questions), 0)
        
        # Validate question content (this should populate popular_gh_questions)
        self.validator.validate_question_content(so_question, gh_discussion)
        
        # Should now contain the question title
        self.assertEqual(self.validator.popular_gh_questions, {"Test Question"})

    def test_popular_gh_questions_not_tracked_without_tag(self):
        """Test that questions without popular tag are not tracked."""
        so_question = {
            "title": "Regular Question",
            "body": "Test body", 
            "tags": ["test"]
        }
        
        # GH discussion without popular tag
        gh_discussion = {
            "title": "Regular Question",
            "body": "Test body",
            "labels": {
                "nodes": [
                    {"name": "test"}
                    # No popular tag
                ]
            }
        }
        
        # Validate question content
        self.validator.validate_question_content(so_question, gh_discussion)
        
        # Should remain empty since no popular tag
        self.assertEqual(len(self.validator.popular_gh_questions), 0)

   

    def test_popular_tag_min_threshold_initialization(self):
        """Test that popular_tag_min_threshold is properly initialized."""
        # Test default value
        default_validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A"
        )
        self.assertEqual(default_validator.popular_tag_min_threshold, 200)
        
        # Test custom value
        custom_validator = MigrationValidator(
            auth_manager=self.mock_auth_manager,
            owner="test_owner", 
            name="test_repo",
            category_name="Q&A",
            popular_tag_min_threshold=500
        )
        self.assertEqual(custom_validator.popular_tag_min_threshold, 500)

    

if __name__ == '__main__':
    unittest.main()
