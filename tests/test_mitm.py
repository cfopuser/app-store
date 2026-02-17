import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from core.utils import run_apk_mitm

class TestMitmIntegration(unittest.TestCase):
    @patch('shutil.which')
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.replace')
    def test_run_apk_mitm_success(self, mock_replace, mock_exists, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = '/usr/local/bin/apk-mitm'
        mock_exists.side_effect = lambda path: True  # APK exists and patched APK exists
        mock_run.return_value = MagicMock(returncode=0)
        
        apk_path = "test.apk"
        result = run_apk_mitm(apk_path)
        
        # Verify
        self.assertTrue(result)
        mock_run.assert_called_once_with(["apk-mitm", apk_path], check=True)
        # Check if it tried to replace with -patched version
        mock_replace.assert_called_once()
        args, _ = mock_replace.call_args
        self.assertEqual(args[0], "test-patched.apk")
        self.assertEqual(args[1], "test.apk")

    @patch('shutil.which')
    def test_run_apk_mitm_missing_binary(self, mock_which):
        mock_which.return_value = None
        
        with patch('os.path.exists', return_value=True):
            result = run_apk_mitm("test.apk")
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
