import unittest
import json
import os
from datetime import datetime, timezone
from populate_discussion import (
    get_url_redir_str, 
    get_readable_date, 
    decode_html_entities, 
    TagsToIgnore,
    remove_tags_under_threshold,
    get_tags_under_threshold, 
    get_tags_at_or_above_threshold,
    format_header_data,
    MetaAction
)

class TestFormatNoteMetaData(unittest.TestCase):
    """Unit tests for the format_note_meta_data function."""

    def test_format_note_meta_data(self):
        """Test the format_note_meta_data function."""
        json_data = '{"owner": {"display_name": "Test User"},"score": 1,"creation_date": 1752172239}'
        data = json.loads(json_data)

        expected = f"> [!NOTE]\n> Originally asked by Test User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had 1 vote.\n\n"
        result = format_header_data(data, MetaAction.ASKED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_empty_author(self):
        """Test the format_note_meta_data function."""
        json_data = '{"owner": {},"score": 0,"creation_date": 1752172239}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally asked by Unknown User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had 0 votes.\n\n"
        result = format_header_data(data, MetaAction.ASKED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_with_negative_score(self):   
        """Test the format_note_meta_data function with negative score."""
        json_data = '{"owner": {"display_name": "Test User"},"score": -2,"creation_date": 1752172239}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally asked by Test User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had -2 votes.\n\n"
        result = format_header_data(data, MetaAction.ASKED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_with_empty_date(self):   
        """Test the format_note_meta_data function with empty date."""
        json_data = '{"owner": {"display_name": "Test User"},"score": 1}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally asked by Test User on Unknown Date in BC Gov Stack Overflow.\n" + \
           f"> It had 1 vote.\n\n"
        result = format_header_data(data, MetaAction.ASKED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_with_empty_score(self):   
        """Test the format_note_meta_data function with empty score."""
        json_data = '{"owner": {"display_name": "Test User"},"creation_date": 1752172239}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally asked by Test User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had 0 votes.\n\n"
        result = format_header_data(data, MetaAction.ASKED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_with_comment_action(self):  
        """Test the format_note_meta_data function with comment action."""
        json_data = '{"owner": {"display_name": "Test User"},"score": 1,"creation_date": 1752172239}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally commented on by Test User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had 1 vote.\n\n"
        result = format_header_data(data, MetaAction.COMMENTED)
        self.assertEqual(result, expected)

    def test_format_note_meta_data_with_answered_action(self):
        """Test the format_note_meta_data function with answered action."""
        json_data = '{"owner": {"display_name": "Test User"},"score": 1,"creation_date": 1752172239}'
        data = json.loads(json_data)
        expected = f"> [!NOTE]\n> Originally answered by Test User on Jul 10, 2025 at 18:30 UTC in BC Gov Stack Overflow.\n" + \
           f"> It had 1 vote.\n\n"
        result = format_header_data(data, MetaAction.ANSWERED)
        self.assertEqual(result, expected)
        

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
        expected = "Jan 15, 2025 at 10:10 UTC"
        result = get_readable_date(timestamp)
        self.assertEqual(result, expected)

    def test_float_timestamp_conversion(self):
        """Test conversion of float timestamp to readable date."""
        # Test with a float timestamp
        timestamp = 1736935800.123
        expected = "Jan 15, 2025 at 10:10 UTC"
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
        expected = "Dec 31, 1969 at 00:00 UTC"
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

    def test_string_date(self):
        """Test with string date."""
        date_string = "2025-06-15 14:30:00"
        expected = "Jun 15, 2025 at 14:30 UTC"
        result = get_readable_date(date_string)
        self.assertEqual(result, expected)

    def test_ISO8601_date(self):
        """Test with ISO 8601 date string."""
        iso_date = "2025-01-15T10:10:00Z"
        expected = "Jan 15, 2025 at 10:10 UTC"
        result = get_readable_date(iso_date)
        self.assertEqual(result, expected)

    def test_ISO8601_date_with_timezone_offset(self):
        """Test with ISO 8601 date string with timezone offset."""
        iso_date = "2025-01-15T10:10:00+00:00"
        expected = "Jan 15, 2025 at 10:10 UTC"
        result = get_readable_date(iso_date)
        self.assertEqual(result, expected)

    def test_ISO8601_date_with_UTC_suffix(self):
        """Test with ISO 8601 date with UTC suffix."""
        iso_date = "2025-01-15T10:10:00.323UTC" 
        result = get_readable_date(iso_date)
        self.assertEqual(result, "Unknown Date")

    def test_ISO8601_date_with_no_suffix(self):
        """Test with ISO 8601 date without suffix."""
        iso_date = "2025-01-15T10:10:00.198"
        expected = "Jan 15, 2025 at 10:10 UTC"
        result = get_readable_date(iso_date)
        self.assertEqual(result, expected)

    def test_invalid_string(self):
        """Test with invalid date format"""
        date_string = "this-is-not-a-date"
        result = get_readable_date(date_string)
        self.assertEqual(result, "Unknown Date")


    def test_invalid_date_format(self):
        """Test with invalid date format"""
        date_string = "Jan 15 2025 14:30:00"
        result = get_readable_date(date_string)
        self.assertEqual(result, "Unknown Date")


    def test_invalid_timestamp(self):
        """Test with invalid timestamp that causes exception."""
        # Test with a timestamp that's too large (year > 9999)
        invalid_timestamp = 999999999999999
        result = get_readable_date(invalid_timestamp)
        # Should return the original value when conversion fails
        self.assertEqual(result, "Unknown Date")

    def test_string_number_conversion(self):
        """Test with string representation of a number."""
        # This should not be converted as it's a string, not int/float
        timestamp_string = "1736935800"
        result = get_readable_date(timestamp_string)
        self.assertEqual(result, "Unknown Date")

    def test_boolean_false(self):
        """Test with boolean False."""
        result = get_readable_date(False)
        self.assertEqual(result, "Unknown Date")

    def test_boolean_true(self):
        """Test with boolean True (which equals 1 in numeric context)."""
        result = get_readable_date(True)
        expected = "Jan 01, 1970 at 00:00 UTC"
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


class TestRemoveTagsUnderThreshold(unittest.TestCase):
    """Unit tests for the remove_tags_under_threshold function."""

    def test_remove_empty_lists(self):
        """Test with empty lists."""
        result = remove_tags_under_threshold([], [])
        self.assertEqual(result, [])

    def test_remove_empty_tags_under_threshold(self):
        """Test with empty tags_under_threshold list."""
        tags = ["tag1", "tag2", "tag3"]
        result = remove_tags_under_threshold([], tags)
        self.assertEqual(result, ["tag1", "tag2", "tag3"])

    def test_remove_empty_tags(self):
        """Test with empty tags list."""
        tags_under_threshold = ["tag1", "tag2"]
        result = remove_tags_under_threshold(tags_under_threshold, [])
        self.assertEqual(result, [])

    def test_remove_no_matches(self):
        """Test when no tags match the threshold list."""
        tags_under_threshold = ["low1", "low2"]
        tags = ["high1", "high2", "high3"]
        result = remove_tags_under_threshold(tags_under_threshold, tags)
        self.assertEqual(result, ["high1", "high2", "high3"])

    def test_remove_some_matches(self):
        """Test when some tags match the threshold list using realistic tag names."""
        # Based on actual Stack Overflow tag usage patterns
        tags_under_threshold = ["debugging", "troubleshooting", "help"]
        tags = ["openshift", "debugging", "kubernetes", "troubleshooting", "docker", "help", "security"]
        result = remove_tags_under_threshold(tags_under_threshold, tags)
        self.assertEqual(result, ["openshift", "kubernetes", "docker", "security"])

    def test_remove_all_matches(self):
        """Test when all tags match the threshold list."""
        tags_under_threshold = ["tag1", "tag2", "tag3"]
        tags = ["tag1", "tag2", "tag3"]
        result = remove_tags_under_threshold(tags_under_threshold, tags)
        self.assertEqual(result, [])

    def test_remove_duplicate_tags(self):
        """Test with duplicate tags in input list."""
        tags_under_threshold = ["low1"]
        tags = ["high1", "low1", "high1", "low1", "high2"]
        result = remove_tags_under_threshold(tags_under_threshold, tags)
        self.assertEqual(result, ["high1", "high1", "high2"])

    def test_remove_case_sensitive(self):
        """Test that removal is case sensitive."""
        tags_under_threshold = ["Low1", "LOW2"]
        tags = ["low1", "Low1", "low2", "LOW2", "high1"]
        result = remove_tags_under_threshold(tags_under_threshold, tags)
        self.assertEqual(result, ["low1", "low2", "high1"])


class TestGetTagsUnderThreshold(unittest.TestCase):
    """Unit tests for the get_tags_under_threshold function."""

    def test_get_empty_tags_data(self):
        """Test with empty tags_data."""
        result = get_tags_under_threshold(5, [])
        self.assertEqual(result, [])

    def test_get_zero_threshold(self):
        """Test with zero threshold (should return empty list as all counts >= 0)."""
        tags_data = [
            {"name": "tag1", "count": 0},
            {"name": "tag2", "count": 1}, 
            {"name": "tag3", "count": 10}
        ]
        result = get_tags_under_threshold(0, tags_data)
        self.assertEqual(result, [])

    def test_get_threshold_one(self):
        """Test with threshold of 1."""
        tags_data = [
            {"name": "tag1", "count": 0},
            {"name": "tag2", "count": 1},
            {"name": "tag3", "count": 2}
        ]
        result = get_tags_under_threshold(1, tags_data)
        self.assertEqual(result, ["tag1"])

    def test_get_threshold_five(self):
        """Test with threshold of 5 using realistic tag data."""
        # Based on actual tags.json structure
        tags_data = [
            {
                "name": "openshift",
                "count": 145,
                "description": "Topics related to the Province's implementation of OpenShift.",
                "id": 12,
                "has_synonyms": False
            },
            {
                "name": "database", 
                "count": 8,
                "description": "Questions about database design, queries, and administration.",
                "id": 15,
                "has_synonyms": False
            },
            {
                "name": "authentication",
                "count": 3,
                "description": "Authentication and authorization questions.",
                "id": 23,
                "has_synonyms": False
            },
            {
                "name": "api",
                "count": 2,
                "description": "Questions about API development and integration.",
                "id": 45,
                "has_synonyms": False
            }
        ]
        result = get_tags_under_threshold(5, tags_data)
        expected = ["authentication", "api"]  # Only tags with count < 5
        self.assertEqual(sorted(result), sorted(expected))

    def test_get_missing_count_field(self):
        """Test with tags missing count field (should default to 0)."""
        tags_data = [
            {"name": "tag1", "count": 5},
            {"name": "tag2"},  # Missing count field
            {"name": "tag3", "count": 10}
        ]
        result = get_tags_under_threshold(5, tags_data)
        self.assertEqual(result, ["tag2"])

    def test_get_mixed_count_types(self):
        """Test with different count value types."""
        tags_data = [
            {"name": "tag1", "count": 1},
            {"name": "tag2", "count": 5.0},  # Float count
            {"name": "tag3", "count": 10}    # Int count  
        ]
        result = get_tags_under_threshold(5, tags_data)
        # tag1 (1 < 5)
        self.assertEqual(result, ["tag1"])

    def test_get_high_threshold(self):
        """Test with high threshold where all realistic tags are under."""
        # Using realistic BC Gov technology tags
        tags_data = [
            {
                "name": "openshift", 
                "count": 145,
                "description": "OpenShift container platform questions.",
                "id": 12
            },
            {
                "name": "keycloak",
                "count": 42,
                "description": "Keycloak authentication questions.",
                "id": 156
            },
            {
                "name": "postgresql",
                "count": 38,
                "description": "PostgreSQL database questions.",
                "id": 203
            }
        ]
        result = get_tags_under_threshold(200, tags_data)
        expected = ["openshift", "keycloak", "postgresql"]
        self.assertEqual(sorted(result), sorted(expected))

    def test_get_preserve_tag_structure(self):
        """Test that function only returns tag names, not full structures."""
        # Realistic tags.json structure
        tags_data = [
            {
                "name": "keycloak",
                "count": 12,
                "description": "Questions about Keycloak authentication service.",
                "id": 34,
                "has_synonyms": False,
                "last_activity_date": 1749501492
            },
            {
                "name": "nodejs", 
                "count": 3,
                "description": "Node.js development questions.",
                "id": 67,
                "has_synonyms": True,
                "last_activity_date": 1749401392
            }
        ]
        result = get_tags_under_threshold(5, tags_data)
        self.assertEqual(result, ["nodejs"])
        # Verify it's just strings, not dicts
        self.assertIsInstance(result[0], str)


class TestGetTagsAtOrAboveThreshold(unittest.TestCase):
    """Unit tests for the get_tags_at_or_above_threshold function."""

    def test_get_empty_tags_data(self):
        """Test with empty tags_data."""
        result = get_tags_at_or_above_threshold(5, [])
        self.assertEqual(result, [])

    def test_get_zero_threshold(self):
        """Test with zero threshold (should return all tags)."""
        tags_data = [
            {"name": "tag1", "count": 0},
            {"name": "tag2", "count": 1},
            {"name": "tag3", "count": 10}
        ]
        result = get_tags_at_or_above_threshold(0, tags_data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, tags_data)

    def test_get_threshold_one(self):
        """Test with threshold of 1."""
        tags_data = [
            {"name": "tag1", "count": 0},
            {"name": "tag2", "count": 1},
            {"name": "tag3", "count": 2}
        ]
        result = get_tags_at_or_above_threshold(1, tags_data)
        expected = [
            {"name": "tag2", "count": 1},
            {"name": "tag3", "count": 2}
        ]
        self.assertEqual(result, expected)

    def test_get_threshold_five(self):
        """Test with threshold of 5 using realistic tag data."""
        # Based on actual tags.json structure  
        tags_data = [
            {
                "name": "openshift",
                "count": 145,
                "description": "Topics related to the Province's implementation of OpenShift.",
                "id": 12,
                "has_synonyms": False,
                "last_activity_date": 1749501492
            },
            {
                "name": "database",
                "count": 8, 
                "description": "Questions about database design, queries, and administration.",
                "id": 15,
                "has_synonyms": False,
                "last_activity_date": 1749401292
            },
            {
                "name": "authentication",
                "count": 3,
                "description": "Authentication and authorization questions.",
                "id": 23,
                "has_synonyms": False,
                "last_activity_date": 1749301192
            },
            {
                "name": "api",
                "count": 2,
                "description": "Questions about API development and integration.", 
                "id": 45,
                "has_synonyms": False,
                "last_activity_date": 1749201092
            }
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        expected = [
            {
                "name": "openshift",
                "count": 145,
                "description": "Topics related to the Province's implementation of OpenShift.",
                "id": 12,
                "has_synonyms": False,
                "last_activity_date": 1749501492
            },
            {
                "name": "database",
                "count": 8,
                "description": "Questions about database design, queries, and administration.",
                "id": 15,
                "has_synonyms": False,
                "last_activity_date": 1749401292
            }
        ]
        self.assertEqual(result, expected)

    def test_get_missing_count_field(self):
        """Test with tags missing count field (should default to 0)."""
        tags_data = [
            {"name": "tag1", "count": 5},
            {"name": "tag2"},  # Missing count field
            {"name": "tag3", "count": 10}
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        expected = [
            {"name": "tag1", "count": 5},
            {"name": "tag3", "count": 10}
        ]
        self.assertEqual(result, expected)

    def test_get_mixed_count_types(self):
        """Test with different count value types."""
        tags_data = [
            {"name": "tag1", "count": 1},
            {"name": "tag2", "count": 5.0},  # Float count
            {"name": "tag3", "count": 10}    # Int count
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        expected = [
            {"name": "tag2", "count": 5.0},
            {"name": "tag3", "count": 10}
        ]  
        self.assertEqual(result, expected)

    def test_get_high_threshold(self):
        """Test with high threshold where no tags qualify."""
        tags_data = [
            {"name": "tag1", "count": 1},
            {"name": "tag2", "count": 50},
            {"name": "tag3", "count": 100}
        ]
        result = get_tags_at_or_above_threshold(200, tags_data)
        self.assertEqual(result, [])

    def test_get_preserve_full_structure(self):
        """Test that function returns full tag structures using realistic data."""
        # Realistic tags.json structure
        tags_data = [
            {
                "name": "docker",
                "count": 25,
                "description": "Container technology and Docker-related questions.",
                "id": 89,
                "has_synonyms": True,
                "last_activity_date": 1749501492,
                "is_moderator_only": False
            },
            {
                "name": "testing",
                "count": 3,
                "description": "Software testing and quality assurance.",
                "id": 156,
                "has_synonyms": False,
                "last_activity_date": 1749301192,
                "is_moderator_only": False
            }
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        expected = [{
            "name": "docker",
            "count": 25,
            "description": "Container technology and Docker-related questions.",
            "id": 89,
            "has_synonyms": True,
            "last_activity_date": 1749501492,
            "is_moderator_only": False
        }]
        self.assertEqual(result, expected)
        
        # Verify it returns the complete dictionary structure
        self.assertEqual(result[0]["description"], "Container technology and Docker-related questions.")
        self.assertEqual(result[0]["id"], 89)
        self.assertTrue(result[0]["has_synonyms"])

    def test_get_exact_threshold_matches(self):
        """Test that tags with count exactly equal to threshold are included using realistic data."""
        # Realistic BC Gov Stack Overflow tags with various counts
        tags_data = [
            {
                "name": "documentation",
                "count": 4,
                "description": "Questions about documentation and guides.",
                "id": 301
            },
            {
                "name": "devops", 
                "count": 5,
                "description": "DevOps practices and tools.",
                "id": 302
            },
            {
                "name": "cicd",
                "count": 5,
                "description": "Continuous Integration and Deployment.", 
                "id": 303
            },
            {
                "name": "monitoring",
                "count": 7,
                "description": "Application and infrastructure monitoring.",
                "id": 304
            }
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        expected = [
            {
                "name": "devops",
                "count": 5,
                "description": "DevOps practices and tools.",
                "id": 302
            },
            {
                "name": "cicd",
                "count": 5,
                "description": "Continuous Integration and Deployment.",
                "id": 303
            },
            {
                "name": "monitoring",
                "count": 7,
                "description": "Application and infrastructure monitoring.",
                "id": 304
            }
        ]
        self.assertEqual(result, expected)

    def test_get_preserve_order(self):
        """Test that original order is preserved in results using realistic data."""
        # Realistic tags in the order they might appear in tags.json
        tags_data = [
            {
                "name": "keycloak",
                "count": 42,
                "description": "Questions about Keycloak authentication service.",
                "id": 156
            },
            {
                "name": "api-gateway", 
                "count": 18,
                "description": "API Gateway configuration and usage.",
                "id": 234
            },
            {
                "name": "microservices",
                "count": 31,
                "description": "Microservices architecture questions.", 
                "id": 189
            }
        ]
        result = get_tags_at_or_above_threshold(5, tags_data)
        # Should maintain original order: keycloak, api-gateway, microservices
        expected_names = ["keycloak", "api-gateway", "microservices"]
        actual_names = [tag["name"] for tag in result]
        self.assertEqual(actual_names, expected_names)


if __name__ == '__main__':
    unittest.main()
