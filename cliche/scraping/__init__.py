"""Scraping module for the CLIche application."""
from .extractors.manager import get_extractor_manager
from .models.data_models import (
    ScrapedData,
    ScrapedImage,
    CrawlerConfig,
    ExtractionResult,
    ExtractionStrategy
)

__all__ = [
    'get_extractor_manager',
    'ScrapedData',
    'ScrapedImage',
    'CrawlerConfig',
    'ExtractionResult',
    'ExtractionStrategy'
]