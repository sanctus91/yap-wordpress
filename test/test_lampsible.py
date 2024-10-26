import os
import unittest
from lampsible import __version__
from lampsible.lampsible import Lampsible

class TestLampsible(unittest.TestCase):

    def setUp(self):
        self.lampsible = Lampsible(
            web_user='user',
            # TODO: This won't work because fetch_ansible_facts needs the host
            # to actually be real and reachable. Maybe we can use localhost, but that
            # requires some additional setup - remote_sudo_password and so on.
            web_host='localhost',
            # TODO: This will probably be optional soon.
            action='apache',
            # TODO
            private_data_dir=os.path.join(
                'test',
                'tmp-private-data',
            ),
            database_password='password'
        )


    def tearDown(self):
        # TODO: This should be baked into the Lampsible class.
        self.lampsible.private_data_helper.cleanup_dir()


    def test_banner(self):
        self.assertIn(__version__, self.lampsible.banner)


    # TODO
    def test_validator(self):
        self.lampsible._validate_args()
