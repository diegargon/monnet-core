"""
Just initial Near do nothing test
"""
# Standard
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import subprocess
import os
import signal
import time
import select

# Local
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook
from shared.app_context import AppContext

class TestMonnetGateway(unittest.TestCase):

    @classmethod
    @patch('monnet_gateway.database.dbmanager.DBManager._connect')
    @patch('monnet_gateway.services.config.Config._load_db_config')
    def setUpClass(cls,  mock_load_db_config, mock_db_connect):
        """Configure the environment to start the server once"""

        # Mock the database connection and config loading
        mock_db_connect.return_value = None
        mock_load_db_config.return_value = None

        cls.server_script = os.path.abspath("monnet_gateway/mgateway.py")
        assert os.path.exists(cls.server_script), f"The script does not exist: {cls.server_script}"

        print(f"Using server script: {cls.server_script}")

        # Start the server in a subprocess
        cls.server_process = subprocess.Popen(
            ["python3", cls.server_script, "--working-dir", os.getcwd(), "--no-daemon"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)  # Allow time for the server to start

        """ Verify it started """
        if cls.server_process.poll() is not None:
            stdout, stderr = cls.server_process.communicate()
            raise RuntimeError(
                f"The server did not start correctly:\nSTDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}\n"
                f"Current directory: {os.getcwd()}"
            )

    @classmethod
    def tearDownClass(cls):
        """Stop the server after all tests"""
        if cls.server_process.poll() is None:  # If the process is still active
            os.kill(cls.server_process.pid, signal.SIGTERM)
            cls.server_process.wait()

    def test_server_is_running(self):
        """Check that the server is still running after starting it"""
        self.assertIsNone(
            self.server_process.poll(),
            "The server is not running after being started"
        )

    def test_server_no_output(self):
        """Check that the server does not produce unexpected output upon startup"""
        # Wait a short moment to check output
        time.sleep(3)

        stdout_lines = []
        stderr_lines = []

        start_time = time.time()
        while time.time() - start_time < 3:
            # Use select to check if there is data to read without blocking
            readable, _, _ = select.select([self.server_process.stdout, self.server_process.stderr], [], [], 0.1)

            for stream in readable:
                if stream is self.server_process.stdout:
                    stdout_line = stream.readline()
                    if stdout_line:
                        stdout_lines.append(stdout_line)

                if stream is self.server_process.stderr:
                    stderr_line = stream.readline()
                    if stderr_line:
                        stderr_lines.append(stderr_line)

            time.sleep(0.1)

        self.assertEqual(b"".join(stdout_lines), b"", "The server produced unexpected output on stdout")
        self.assertEqual(b"".join(stderr_lines), b"", "The server produced errors on stderr")

        # Print the output if it exists
        if stdout_lines:
            print("stdout server lines:")
            print(b"".join(stdout_lines).decode())

        if stderr_lines:
            print("stderr server lines:")
            print(b"".join(stderr_lines).decode())

    @patch('subprocess.Popen')
    def test_run_ansible_playbook_success(self, mock_subprocess):
        ctx = AppContext(os.getcwd())

        # Mock the subprocess response
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            b'{"stats": {}, "custom_stats": {}, "global_custom_stats": {}}',
            b''
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        # Call the function
        result = run_ansible_playbook(ctx, "test.yml", {"var1": "value1"}, "127.0.0.1", "ansible")

        result_dict = json.loads(result)
        print("Complete result:", result_dict)
        # Validate the result
        self.assertEqual(result_dict['status'], 'success')
        self.assertEqual(result_dict['result']['custom_stats'], {})
        self.assertEqual(result_dict['result']['global_custom_stats'], {})

"""
    @patch('subprocess.run')
    def test_run_ansible_playbook_failure(self, mock_subprocess):
        # Simulate an error in Ansible
        mock_subprocess.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"Error ejecutando Ansible")

        # Validate that an exception is raised
        with self.assertRaises(Exception):
            run_ansible_playbook("test_playbook.yml", {"var1": "value1"})
"""

if __name__ == '__main__':
    unittest.main()
