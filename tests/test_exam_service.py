import unittest

from src.exceptions import UpstreamError
from src.service.ujian_service import extract_redirect, resolve_trusted_url


class ExamRedirectTest(unittest.TestCase):
    def test_extract_redirect_from_location_header(self):
        self.assertEqual(
            extract_redirect({"Location": "/dashboard"}, ""), "/dashboard"
        )

    def test_extract_redirect_from_meta_refresh(self):
        html = '<meta http-equiv="refresh" content="0; url=/dashboard">'
        self.assertEqual(extract_redirect({}, html), "/dashboard")

    def test_relative_exam_url_is_resolved(self):
        self.assertEqual(
            resolve_trusted_url(
                "https://ujiankampusa.bsi.ac.id", "/dashboard"
            ),
            "https://ujiankampusa.bsi.ac.id/dashboard",
        )

    def test_lookalike_exam_host_is_rejected(self):
        with self.assertRaisesRegex(UpstreamError, "untrusted host"):
            resolve_trusted_url(
                "https://ujiankampusa.bsi.ac.id",
                "https://ujiankampusa.bsi.ac.id.evil.example/dashboard",
            )


if __name__ == "__main__":
    unittest.main()
