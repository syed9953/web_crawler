import unittest
from crawl import normalize_url, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html, extract_page_data


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_strip_trailing_slash(self):
        input_url = "https://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_http_https(self):
        input_url = "http://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic(self):
        html = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(html)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic_2(self):
            html = "<html><body><h2>Test Title</h2></body></html>"
            actual = get_heading_from_html(html)
            expected = "Test Title"
            self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic_3(self):
        html = "<html><body><h3>Test Title</h3></body></html>"
        actual = get_heading_from_html(html)
        expected = ""
        self.assertEqual(actual, expected)

    
    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
                    <p>Outside paragraph.</p>
                    <main>
                        <p>Main paragraph.</p>
                    </main>
                </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority_2(self):
        input_body = """<html><body>
                    <p>Outside paragraph.</p>
                    <p>
                        Main paragraph.
                    </p>
                </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Outside paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority_3(self):
        input_body = """<html><body>
                    <p>
                        Main paragraph.
                    </p>
                </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute_1(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/page.html"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/page.html"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute_2(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/page/page_1.html"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/page/page_1.html"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)
    
    def test_get_images_from_html_relative_1(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://crawler-test.com/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative_2(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo/logo_1.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo/logo_1.png"]
        self.assertEqual(actual, expected)
        
    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic_1(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h2>Test Title</h2>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic_2(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <main>
                <p>This is the first paragraph.</p>
            </main>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)


if __name__=="__main__":
    unittest.main()

