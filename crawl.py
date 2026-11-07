from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
import requests
import asyncio
import aiohttp

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def normalize_url(url):
    o = urlsplit(url)
    hostname = o.hostname
    path = o.path.rstrip("/")
    return f"{hostname}{path}"

def get_heading_from_html(html: str) -> str:
    tag = BeautifulSoup(html, 'html.parser')
    heading = tag.find("h1")
    if heading:
        if isinstance(heading, Tag):
            return heading.get_text(strip=True)
        else:
            return ""
    elif tag.find("h2"):
        heading_2 = tag.find("h2")
        if isinstance(heading_2, Tag):
            return heading_2.get_text(strip=True)
        else:
            return ""
    else:
        return ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find("main")
    if tag:
        if isinstance(tag, Tag):
            tag_level_2 = tag.find("p")
            if isinstance (tag_level_2, Tag):
                return tag_level_2.get_text(strip=True)
        else:
            return "" 
    elif soup.find("p"):
        tag_2 = soup.find("p")
        if isinstance(tag_2, Tag):
            return tag_2.get_text(strip=True)
        else:
            return ""
    else:
        return ""

def get_urls_from_html(html, base_url):
    hrefs = []
    soup = BeautifulSoup(html, 'html.parser')
    link_tag = soup.find_all('a')
    if link_tag:
        for link in link_tag:
            href = link.get("href")
            absolute_href = urljoin(base_url, href)
            hrefs.append(absolute_href)
        return hrefs
    else:
        return ""

def get_images_from_html(html, base_url):
    img_links = []
    soup = BeautifulSoup(html, 'html.parser')
    img_tags = soup.find_all("img")
    if img_tags:
        for img_tag in img_tags:
            img_link = img_tag.get("src")
            absolute_link = urljoin(base_url, img_link)
            img_links.append(absolute_link)
        return img_links
    else:
        return ""

def extract_page_data(input_body: str, input_url: str) -> PageData:
    url = input_url
    heading = get_heading_from_html(input_body)
    first_paragraph = get_first_paragraph_from_html(input_body)
    links = get_urls_from_html(input_body, input_url)
    img_links = get_images_from_html(input_body, input_url)

    return {"url": url, "heading":heading, "first_paragraph":first_paragraph, "outgoing_links":links, "image_urls":img_links}

def get_html(url):
    try:
        response = requests.get(url, headers={"User-Agent":"BootCrawler/1.0"})
        if response.status_code > 400:
            raise Exception(f"There is an error. response {response.status_code}")
        if 'text/html' not in response.headers.get('content-type'):
            raise Exception(f"Content type is not valid")
    except Exception as e:
        raise Exception(f"An exception occured: {e}")
    return response.text

def crawl_page(base_url, current_url=None, page_data={}):
    current_url_hostname = urlsplit(current_url).hostname
    base_url_hostname = urlsplit(base_url).hostname
    if current_url_hostname != base_url_hostname:
        return
    norm_url = normalize_url(current_url)
    if norm_url in page_data:
        return
    response = get_html(current_url)
    print(f"Got response from {norm_url}")
    page_data[norm_url] = extract_page_data(response, current_url)
    for outgoing_link in page_data[norm_url]['outgoing_links']:
        crawl_page(base_url, current_url=outgoing_link, page_data=page_data)

    return page_data
        
class AsyncCrawler():
    def __init__(self, base_url, max_concurrency, max_pages):
        self.base_domain = urlsplit(base_url).hostname
        self.base_url = base_url
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(int(max_concurrency))
        self.session = None
        self.max_pages = int(max_pages)
        self.should_stop = False
        self.all_tasks = set()

    async def normalized_url(self, url):
        o = urlsplit(url)
        hostname = o.hostname
        path = o.path.rstrip("/")
        return f"{hostname}{path}"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False
            if len(self.visited) == self.max_pages:
                self.should_stop=True
                print("Reached maximum number of pages to crawl")
                return False
            if normalized_url in self.visited:
                return False
            else:
                self.visited.add(normalized_url)
                return True
    
    async def get_html(self, current_url):
        resp = await self.session.get(current_url, raise_for_status=False)
        async with resp:
            if resp.status > 400:
                raise Exception(f"There is an error. response {resp.status}")
            if 'text/html' not in resp.headers.get('content-type'):
                raise Exception(f"Content type is not valid")
            return await resp.text()
        
    async def crawl_page(self, base_url, current_url=None):
        try:
            if self.should_stop:
                return 
            current_url_hostname = urlsplit(current_url).hostname
            base_url_hostname = urlsplit(base_url).hostname
            if current_url_hostname != base_url_hostname:
                return
            norm_url = normalize_url(current_url)
            is_visited = await self.add_page_visit(norm_url)
            
            if not is_visited:
                return
            
            async with self.semaphore:
                input_body = await self.get_html(current_url)
                
                print(f"crawling {current_url}")
                
                data = extract_page_data(input_body, current_url)

                async with self.lock:
                    if norm_url in self.page_data:
                        return
                    self.page_data[norm_url] = data

            for outgoing_link in self.page_data[norm_url]['outgoing_links']:
                self.all_tasks.add(asyncio.create_task(self.crawl_page(base_url, current_url=outgoing_link)))

        finally:
            self.all_tasks.discard(asyncio.current_task())

    async def crawl(self, current_url=None):
        if current_url is None:
            current_url = self.base_url
    
        await self.crawl_page(self.base_url, current_url=current_url)

        while self.all_tasks:
            async with self.lock:
                all_tasks = self.all_tasks.copy()
            if all_tasks:
                await asyncio.gather(*all_tasks)
            else:
                break

        return self.page_data


async def crawl_site_async(base_url, max_concurrency, max_pages):
    crawler = AsyncCrawler(base_url, max_concurrency, max_pages)
    async with crawler as c:
        page_data = await c.crawl(current_url = base_url)
        return page_data

            

