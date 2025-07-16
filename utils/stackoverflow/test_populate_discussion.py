import unittest
from datetime import datetime, timezone
from populate_discussion import get_url_redir_str, get_readable_date, decode_html_entities


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


class TestGetReadableDate(unittest.TestCase):
    """Unit tests for the get_readable_date function."""

    def test_timestamp_conversion(self):
        """Test conversion of Unix timestamp to readable date."""
        # Test with a known timestamp: 2025-01-15 10:10:00 UTC
        timestamp = 1736935800
        expected = "2025-01-15 10:10:00 UTC"
        result = get_readable_date(timestamp)
        self.assertEqual(result, expected)

    def test_float_timestamp_conversion(self):
        """Test conversion of float timestamp to readable date."""
        # Test with a float timestamp
        timestamp = 1736935800.123
        expected = "2025-01-15 10:10:00 UTC"
        result = get_readable_date(timestamp)
        self.assertEqual(result, expected)

    def test_zero_timestamp(self):
        """Test with zero timestamp."""
        timestamp = 0
        result = get_readable_date(timestamp)
        self.assertEqual(result, "Unknown Date")

    def test_negative_timestamp(self):
        """Test with negative timestamp (before Unix epoch)."""
        timestamp = -86400  # One day before epoch
        expected = "1969-12-31 00:00:00 UTC"
        result = get_readable_date(timestamp)
        self.assertEqual(result, expected)

    def test_none_date(self):
        """Test with None input."""
        result = get_readable_date(None)
        self.assertEqual(result, "Unknown Date")

    def test_empty_string_date(self):
        """Test with empty string input."""
        result = get_readable_date("")
        self.assertEqual(result, "Unknown Date")

    def test_string_date_passthrough(self):
        """Test with string date that should pass through unchanged."""
        date_string = "2025-06-15 14:30:00"
        result = get_readable_date(date_string)
        self.assertEqual(result, date_string)

    def test_invalid_timestamp(self):
        """Test with invalid timestamp that causes exception."""
        # Test with a timestamp that's too large (year > 9999)
        invalid_timestamp = 999999999999999
        result = get_readable_date(invalid_timestamp)
        # Should return the original value when conversion fails
        self.assertEqual(result, invalid_timestamp)

    def test_string_number_conversion(self):
        """Test with string representation of a number."""
        # This should not be converted as it's a string, not int/float
        timestamp_string = "1736935800"
        result = get_readable_date(timestamp_string)
        self.assertEqual(result, timestamp_string)

    def test_boolean_false(self):
        """Test with boolean False."""
        result = get_readable_date(False)
        self.assertEqual(result, "Unknown Date")

    def test_boolean_true(self):
        """Test with boolean True (which equals 1 in numeric context)."""
        result = get_readable_date(True)
        expected = "1970-01-01 00:00:01 UTC"
        self.assertEqual(result, expected)


class TestDecodeHtmlEntities(unittest.TestCase):
    """Unit tests for the decode_html_entities function."""

    def test_decode_apostrophe(self):
        """Test decoding of HTML encoded apostrophe."""
        text = "I&#39;m connected to BC Gov&#39;s VPN"
        expected = "I'm connected to BC Gov's VPN"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_decode_quotes(self):
        """Test decoding of HTML encoded quotes."""
        text = "He said &quot;Hello world&quot;"
        expected = 'He said "Hello world"'
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_decode_ampersand(self):
        """Test decoding of HTML encoded ampersand."""
        text = "Coffee &amp; Tea"
        expected = "Coffee & Tea"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_decode_less_than_greater_than(self):
        """Test decoding of HTML encoded angle brackets."""
        text = "&lt;script&gt;alert()&lt;/script&gt;"
        expected = "<script>alert()</script>"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_multiple_entities(self):
        """Test decoding of multiple HTML entities in one string."""
        text = "It&#39;s a &quot;test&quot; &amp; it&#39;s &lt;important&gt;"
        expected = 'It\'s a "test" & it\'s <important>'
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_no_entities(self):
        """Test string with no HTML entities."""
        text = "This is a normal string"
        expected = "This is a normal string"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_empty_string(self):
        """Test with empty string."""
        text = ""
        expected = ""
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_none_input(self):
        """Test with None input."""
        result = decode_html_entities(None)
        self.assertIsNone(result)

    def test_numeric_entities(self):
        """Test decoding of numeric HTML entities."""
        text = "&#8364; symbol"  # Euro symbol
        expected = "€ symbol"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_mixed_entities(self):
        """Test decoding of mixed named and numeric entities."""
        text = "Price: &#8364;100 &amp; &#36;120"
        expected = "Price: €100 & $120"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_partial_entities(self):
        """Test with incomplete HTML entities."""
        text = "&amp incomplete &"
        expected = "& incomplete &"
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_complex_html_content(self):
        """Test with more complex HTML-like content."""
        text = "&lt;p&gt;The user said: &quot;I can&#39;t access the site&quot;&lt;/p&gt;"
        expected = '<p>The user said: "I can\'t access the site"</p>'
        result = decode_html_entities(text)
        self.assertEqual(result, expected)

    def test_whitespace_preservation(self):
        """Test that whitespace is preserved during decoding."""
        text = "  I&#39;m   testing   spaces  "
        expected = "  I'm   testing   spaces  "
        result = decode_html_entities(text)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
