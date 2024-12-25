import os
import unittest
from lampsible import __version__
from lampsible.lampsible import Lampsible

class TestLampsible(unittest.TestCase):

    def setUp(self):
        try:
            tmp_remote = os.environ['LAMPSIBLE_REMOTE'].split('@')
            web_user = tmp_remote[0]
            web_host = tmp_remote[1]
        except (KeyError, AttributeError):
            web_user = 'user'
            web_host = 'localhost'

        self.lampsible = Lampsible(
            web_user=web_user,
            web_host=web_host,
            action='apache',
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


    # TODO?
    # def test_validator(self):
    #     self.assertEqual(1, 1)
