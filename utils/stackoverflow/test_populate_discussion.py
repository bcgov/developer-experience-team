import unittest
from datetime import datetime, timezone
from populate_discussion import get_url_redir_str, get_readable_date, decode_html_entities, TagsToIgnore


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


class TestTagsToIgnore(unittest.TestCase):
    """Unit tests for the TagsToIgnore class."""

    def test_init_with_none(self):
        """Test initialization with None."""
        tags_helper = TagsToIgnore(None)
        self.assertIsNone(tags_helper.tags_to_ignore)

    def test_init_with_empty_list(self):
        """Test initialization with an empty list."""
        tags_helper = TagsToIgnore([])
        self.assertEqual(tags_helper.tags_to_ignore, [])

    def test_init_with_one_tag(self):
        """Test initialization with a list containing one tag."""
        tags_to_ignore = ["test-tag"]
        tags_helper = TagsToIgnore(tags_to_ignore)
        self.assertEqual(tags_helper.tags_to_ignore, ["test-tag"])

    def test_init_with_two_tags(self):
        """Test initialization with a list containing two tags."""
        tags_to_ignore = ["tag1", "tag2"]
        tags_helper = TagsToIgnore(tags_to_ignore)
        self.assertEqual(tags_helper.tags_to_ignore, ["tag1", "tag2"])

    def test_init_with_five_tags(self):
        """Test initialization with a list containing five tags."""
        tags_to_ignore = ["tag1", "tag2", "tag3", "tag4", "tag5"]
        tags_helper = TagsToIgnore(tags_to_ignore)
        self.assertEqual(tags_helper.tags_to_ignore, ["tag1", "tag2", "tag3", "tag4", "tag5"])

    def test_should_ignore_with_none_tags_to_ignore(self):
        """Test should_ignore when tags_to_ignore is None."""
        tags_helper = TagsToIgnore(None)
        result = tags_helper.should_ignore(["any-tag"])
        self.assertFalse(result)

    def test_should_ignore_with_empty_tags_to_ignore(self):
        """Test should_ignore when tags_to_ignore is empty list."""
        tags_helper = TagsToIgnore([])
        result = tags_helper.should_ignore(["any-tag"])
        self.assertFalse(result)

    def test_should_ignore_with_matching_tag(self):
        """Test should_ignore when input contains a tag that should be ignored."""
        tags_helper = TagsToIgnore(["ignore-me", "also-ignore"])
        result = tags_helper.should_ignore(["keep-me", "ignore-me", "another-keep"])
        self.assertTrue(result)

    def test_should_ignore_with_no_matching_tags(self):
        """Test should_ignore when input contains no tags that should be ignored."""
        tags_helper = TagsToIgnore(["ignore-me", "also-ignore"])
        result = tags_helper.should_ignore(["keep-me", "keep-this-too"])
        self.assertFalse(result)

    def test_should_ignore_with_all_matching_tags(self):
        """Test should_ignore when all input tags should be ignored."""
        tags_helper = TagsToIgnore(["ignore-me", "also-ignore"])
        result = tags_helper.should_ignore(["ignore-me", "also-ignore"])
        self.assertTrue(result)

    def test_should_ignore_with_empty_input_tags(self):
        """Test should_ignore when input tags list is empty."""
        tags_helper = TagsToIgnore(["ignore-me"])
        result = tags_helper.should_ignore([])
        self.assertFalse(result)

    def test_should_ignore_case_sensitivity(self):
        """Test that should_ignore is case-sensitive."""
        tags_helper = TagsToIgnore(["ignore-me"])
        # Should not match due to case difference
        result = tags_helper.should_ignore(["IGNORE-ME"])
        self.assertFalse(result)
        
        # Should match exact case
        result = tags_helper.should_ignore(["ignore-me"])
        self.assertTrue(result)

    def test_should_ignore_partial_match(self):
        """Test that should_ignore doesn't do partial string matching."""
        tags_helper = TagsToIgnore(["tag"])
        # Should not match partial strings
        result = tags_helper.should_ignore(["tag-extra"])
        self.assertFalse(result)
        
        result = tags_helper.should_ignore(["prefix-tag"])
        self.assertFalse(result)
        
        # Should match exact string
        result = tags_helper.should_ignore(["tag"])
        self.assertTrue(result)

    

    def test_should_ignore_special_characters(self):
        """Test handling of special characters in tags."""
        tags_helper = TagsToIgnore(["tag-with-dashes", "tag_with_underscores", "tag.with.dots"])
        
        result = tags_helper.should_ignore(["tag-with-dashes"])
        self.assertTrue(result)
        
        result = tags_helper.should_ignore(["tag_with_underscores"])
        self.assertTrue(result)
        
        result = tags_helper.should_ignore(["tag.with.dots"])
        self.assertTrue(result)

    def test_should_ignore_multiple_matches(self):
        """Test should_ignore when input has multiple tags that should be ignored."""
        tags_helper = TagsToIgnore(["ignore1", "ignore2", "ignore3"])
        result = tags_helper.should_ignore(["keep", "ignore1", "ignore2", "another-keep"])
        self.assertTrue(result)

    def test_should_ignore_unicode_tags(self):
        """Test handling of unicode characters in tags."""
        tags_helper = TagsToIgnore(["été", "señor", "тест"])
        
        result = tags_helper.should_ignore(["été"])
        self.assertTrue(result)
        
        result = tags_helper.should_ignore(["señor", "other"])
        self.assertTrue(result)
        
        result = tags_helper.should_ignore(["тест"])
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
