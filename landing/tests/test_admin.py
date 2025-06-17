from core.test_base.test_admin import TestAdminBase


class TextAdminTestCase(TestAdminBase):

    def setUp(self):

        # Submit endpoint
        super().setUp()
        self.endpoint = "/admin/landing/text/"

    def test_search_bar(self):
        """Validate search bar working"""

        self.submit_search_bar(self.endpoint)


class ImageAdminTestCase(TestAdminBase):

    def setUp(self):

        # Submit endpoint
        super().setUp()
        self.endpoint = "/admin/landing/image/"

    def test_search_bar(self):
        """Validate search bar working"""

        self.submit_search_bar(self.endpoint)


class VideoAdminTestCase(TestAdminBase):

    def setUp(self):

        # Submit endpoint
        super().setUp()
        self.endpoint = "/admin/landing/video/"

    def test_search_bar(self):
        """Validate search bar working"""

        self.submit_search_bar(self.endpoint)
