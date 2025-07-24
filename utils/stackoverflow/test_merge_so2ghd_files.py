import unittest
import unittest.mock
from unittest.mock import mock_open, patch, MagicMock
from merge_so2ghd_files import MergeFiles, main


class TestMergeFiles(unittest.TestCase):
    """Unit tests for the MergeFiles class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_file = "base_test.log"
        self.patch_file = "patch_test.log"
        self.new_file = "merged_test.log"
        self.merge_files = MergeFiles(self.base_file, self.patch_file, self.new_file)

    def test_init(self):
        """Test MergeFiles initialization."""
        self.assertEqual(self.merge_files.base_file, self.base_file)
        self.assertEqual(self.merge_files.patch_file, self.patch_file)
        self.assertEqual(self.merge_files.new_file, self.new_file)
        self.assertIsInstance(self.merge_files.lines_mapping, dict)
        self.assertEqual(len(self.merge_files.lines_mapping), 0)

    @patch('builtins.open', new_callable=mock_open)
    def test_read_file_basic(self, mock_file):
        """Test reading a basic file with valid redirect lines."""
        # Simulate file content
        file_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent\n",
            "redir /a/1203 https://github.com/org/repo/discussions/2810#discussioncomment-13836210 permanent\n"
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        # Test the private method directly
        self.merge_files._MergeFiles__read_file(self.base_file)
        
        # Verify the lines_mapping was populated correctly
        expected_mapping = {
            '/questions/1201': 'redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent',
            '/a/1203': 'redir /a/1203 https://github.com/org/repo/discussions/2810#discussioncomment-13836210 permanent'
        }
        self.assertEqual(self.merge_files.lines_mapping, expected_mapping)
        mock_file.assert_called_once_with(self.base_file, 'r')

    @patch('builtins.open', new_callable=mock_open)
    @patch('merge_so2ghd_files.logger')
    def test_read_file_with_invalid_lines(self, mock_logger, mock_file):
        """Test reading a file with some invalid lines (insufficient tokens)."""
        file_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent\n",
            "invalid_line\n",  # Only one token
            "redir /a/1203 https://github.com/org/repo/discussions/2810 permanent\n",
            "another_invalid\n"  # Only one token
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        self.merge_files._MergeFiles__read_file(self.base_file)
        
        # Should only have valid lines in mapping
        expected_mapping = {
            '/questions/1201': 'redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent',
            '/a/1203': 'redir /a/1203 https://github.com/org/repo/discussions/2810 permanent'
        }
        self.assertEqual(self.merge_files.lines_mapping, expected_mapping)
        
        # Should have logged warnings for invalid lines
        self.assertEqual(mock_logger.warning.call_count, 2)
        mock_logger.warning.assert_any_call("Skipping line in file 'base_test.log': invalid_line")
        mock_logger.warning.assert_any_call("Skipping line in file 'base_test.log': another_invalid")

    @patch('builtins.open', new_callable=mock_open)
    def test_read_file_empty_file(self, mock_file):
        """Test reading an empty file."""
        mock_file.return_value.readlines.return_value = []
        
        self.merge_files._MergeFiles__read_file(self.base_file)
        
        self.assertEqual(len(self.merge_files.lines_mapping), 0)

    @patch('builtins.open', new_callable=mock_open)
    def test_read_file_with_whitespace_variations(self, mock_file):
        """Test reading a file with different whitespace patterns."""
        file_content = [
            "redir /questions/1201   https://github.com/org/repo/discussions/2809   permanent\n",  # Extra spaces
            " redir /a/1203 https://github.com/org/repo/discussions/2810 permanent \n",  # Leading/trailing spaces
            "redir\t/share/1204\thttps://github.com/org/repo/discussions/2811\tpermanent\n"  # Tabs
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        self.merge_files._MergeFiles__read_file(self.base_file)
        
        expected_mapping = {
            '/questions/1201': 'redir /questions/1201   https://github.com/org/repo/discussions/2809   permanent',
            '/a/1203': 'redir /a/1203 https://github.com/org/repo/discussions/2810 permanent',
            '/share/1204': 'redir\t/share/1204\thttps://github.com/org/repo/discussions/2811\tpermanent'
        }
        self.assertEqual(self.merge_files.lines_mapping, expected_mapping)

    def test_merge_method(self):
        """Test that merge() correctly calls both base and patch file methods."""
        with patch('builtins.open', mock_open()) as mock_file:
            self.merge_files.merge()
            
            # Verify both files were attempted to be opened for reading
            expected_calls = [
                unittest.mock.call(self.base_file, 'r'),
                unittest.mock.call(self.patch_file, 'r'),
                unittest.mock.call(self.new_file, 'w')
            ]
            mock_file.assert_has_calls(expected_calls, any_order=True)

    @patch('builtins.open', new_callable=mock_open)
    def test_merge_complete_workflow(self, mock_file):
        """Test the complete merge workflow."""
        # Base file content
        base_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent\n",
            "redir /questions/1202 https://github.com/org/repo/discussions/2810 permanent\n"
        ]
        
        # Patch file content 
        patch_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/3000 permanent\n",  # Overwrite existing
            "redir /a/1203 https://github.com/org/repo/discussions/3001 permanent\n"  # New entry
        ]
        
        # Create separate mock objects for each file operation
        base_mock = mock_open(read_data="")
        base_mock.return_value.readlines.return_value = base_content
        
        patch_mock = mock_open(read_data="")
        patch_mock.return_value.readlines.return_value = patch_content
        
        write_mock = mock_open()
        
        # Configure side_effect to return different mocks for different files
        def side_effect(file_path, mode):
            if file_path == self.base_file and mode == 'r':
                return base_mock.return_value
            elif file_path == self.patch_file and mode == 'r':
                return patch_mock.return_value
            elif file_path == self.new_file and mode == 'w':
                return write_mock.return_value
            else:
                return mock_open().return_value
        
        mock_file.side_effect = side_effect
        
        # Execute merge
        self.merge_files.merge()
        
        # Verify the final mapping
        expected_mapping = {
            '/questions/1201': 'redir /questions/1201 https://github.com/org/repo/discussions/3000 permanent',  # Overwritten
            '/questions/1202': 'redir /questions/1202 https://github.com/org/repo/discussions/2810 permanent',  # From base
            '/a/1203': 'redir /a/1203 https://github.com/org/repo/discussions/3001 permanent'  # New from patch
        }
        self.assertEqual(self.merge_files.lines_mapping, expected_mapping)
        
        # Verify that write was called with the correct lines (with newlines)
        written_calls = write_mock.return_value.write.call_args_list
        written_lines = [call[0][0].rstrip('\n') for call in written_calls]
        
        # Should contain all three lines (order may vary due to dict)
        self.assertEqual(len(written_lines), 3)
        self.assertIn('redir /questions/1201 https://github.com/org/repo/discussions/3000 permanent', written_lines)
        self.assertIn('redir /questions/1202 https://github.com/org/repo/discussions/2810 permanent', written_lines)
        self.assertIn('redir /a/1203 https://github.com/org/repo/discussions/3001 permanent', written_lines)



class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.merge_files = MergeFiles("base.log", "patch.log", "merged.log")

    @patch('builtins.open', new_callable=mock_open)
    def test_file_with_only_whitespace_lines(self, mock_file):
        """Test handling of files with only whitespace lines."""
        file_content = [
            "   \n",
            "\t\t\n",
            "     \n"
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        with patch('merge_so2ghd_files.logger') as mock_logger:
            self.merge_files._MergeFiles__read_file("test.log")
            
            # All lines should be skipped silently (empty lines don't generate warnings)
            self.assertEqual(len(self.merge_files.lines_mapping), 0)
            self.assertEqual(mock_logger.warning.call_count, 0)

    @patch('builtins.open', new_callable=mock_open)
    def test_file_with_mixed_valid_invalid_lines(self, mock_file):
        """Test file with mixture of valid and invalid redirect lines."""
        file_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent\n",
            "# This is a comment\n",  # Invalid - comment
            "redir\n",  # Invalid - insufficient tokens
            "redir /a/1203 https://github.com/org/repo/discussions/2810 permanent\n",
            "not_a_redirect_line\n",  # Invalid - single token
            "redir /share/1204 https://github.com/org/repo/discussions/2811 permanent\n"
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        with patch('merge_so2ghd_files.logger') as mock_logger:
            self.merge_files._MergeFiles__read_file("test.log")
            
            # Should have 3 valid entries
            self.assertEqual(len(self.merge_files.lines_mapping), 3)
            self.assertIn('/questions/1201', self.merge_files.lines_mapping)
            self.assertIn('/a/1203', self.merge_files.lines_mapping)
            self.assertIn('/share/1204', self.merge_files.lines_mapping)
            
            # Should have logged 3 warnings for invalid lines
            self.assertEqual(mock_logger.warning.call_count, 3)

    @patch('builtins.open', new_callable=mock_open)
    def test_duplicate_keys_in_same_file(self, mock_file):
        """Test handling of duplicate keys within the same file."""
        file_content = [
            "redir /questions/1201 https://github.com/org/repo/discussions/2809 permanent\n",
            "redir /questions/1201 https://github.com/org/repo/discussions/2999 permanent\n",  # Duplicate key
            "redir /a/1203 https://github.com/org/repo/discussions/2810 permanent\n"
        ]
        mock_file.return_value.readlines.return_value = file_content
        
        self.merge_files._MergeFiles__read_file("test.log")
        
        # Should have 2 unique entries, with the last one winning for duplicates
        self.assertEqual(len(self.merge_files.lines_mapping), 2)
        self.assertEqual(
            self.merge_files.lines_mapping['/questions/1201'],
            'redir /questions/1201 https://github.com/org/repo/discussions/2999 permanent'
        )
        self.assertIn('/a/1203', self.merge_files.lines_mapping)


if __name__ == '__main__':
    unittest.main()
