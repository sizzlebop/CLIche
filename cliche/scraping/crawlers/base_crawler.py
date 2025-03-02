"""Base crawler implementation with proper async browser handling."""
import aiohttp
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse
import asyncio
from playwright.async_api import async_playwright, Error as PlaywrightError
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

class BaseCrawler:
    """Base crawler with proper browser management."""
    
    def __init__(self):
        """Initialize the crawler."""
        self.logger = logging.getLogger(__name__)
        self.browser = None
        self.context = None
        self.browser_lock = asyncio.Lock()

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self.browser:
            try:
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch()
            except Exception as e:
                self.logger.error(f"Failed to initialize browser: {str(e)}")
                raise

    async def check_url_accessibility(self, url: str) -> Tuple[bool, Optional[str]]:
        """Check if a URL is accessible."""
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme:
                url = f"https://{url}"

            # Try HEAD request first
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url, allow_redirects=True, timeout=10) as response:
                        if response.status == 405:  # Method not allowed, try GET
                            raise aiohttp.ClientError("HEAD not allowed")
                        return response.status == 200, None
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    # If HEAD fails, try GET
                    async with session.get(url, allow_redirects=True, timeout=10) as response:
                        return response.status == 200, None

        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            return False, "Connection timeout"
        except Exception as e:
            return False, str(e)

    async def create_crawler(self) -> AsyncWebCrawler:
        """Create a properly configured crawler instance."""
        try:
            # Ensure browser is ready
            await self._ensure_browser()

            # Create crawler with custom browser
            crawler = AsyncWebCrawler()
            
            # Configure crawler to use our browser instance
            crawler.browser = self.browser
            
            return crawler

        except Exception as e:
            self.logger.error(f"Failed to create crawler: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise