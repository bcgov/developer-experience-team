import unittest
from populate_discussion import get_url_redir_str


class TestGetUrlRedirStr(unittest.TestCase):
    """Unit tests for the get_url_redir_str function."""

    def test_basic_stackoverflow_url(self):
        """Test with a basic Stack Overflow question URL."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/questions/123"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456"
        expected = "redir /questions/123 https://github.com/bcgov/developer-experience-team/discussions/456 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)

    def test_stackoverflow_answer_url(self):
        """Test with a Stack Overflow answer URL."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/questions/123/155#155"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345"
        expected = "redir /questions/123/155#155 https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)

    def test_stackoverflow_share_url(self):
        """Test with a Stack Overflow share URL format."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/q/123/456"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456"
        expected = "redir /q/123/456 https://github.com/bcgov/developer-experience-team/discussions/456 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)

    def test_stackoverflow_answer_share_url(self):
        """Test with a Stack Overflow answer share URL format."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/a/789/529"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345"
        expected = "redir /a/789/529 https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)

    def test_stackoverflow_url_fragment(self):
        """Test with a Stack Overflow URL that has a hash."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/questions/1297/1299#1299"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345"
        expected = "redir /questions/1297/1299#1299 https://github.com/bcgov/developer-experience-team/discussions/456#discussioncomment-12345 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)


    def test_url_with_query_parameters(self):
        """Test with URL containing query parameters."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/questions/123?utm_source=test"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456"
        expected = "redir /questions/123 https://github.com/bcgov/developer-experience-team/discussions/456 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)


    def test_root_path(self):
        """Test with root path URL."""
        stackoverflow_url = "https://stackoverflow.developer.gov.bc.ca/"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions"
        expected = "redir / https://github.com/bcgov/developer-experience-team/discussions permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)


    def test_different_domain(self):
        """Test with different Stack Overflow domain."""
        stackoverflow_url = "https://stackoverflowteams.com/c/myteam/questions/123/my-question"
        github_url = "https://github.com/bcgov/developer-experience-team/discussions/456"
        expected = "redir /c/myteam/questions/123/my-question https://github.com/bcgov/developer-experience-team/discussions/456 permanent"
        result = get_url_redir_str(stackoverflow_url, github_url)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
