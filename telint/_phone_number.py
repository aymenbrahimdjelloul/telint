"""
This code or file is part of 'Telint' project
copyright (c) 2025 , Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 0.1
date : 04.07.2025
license : MIT License

    // Telint - Telephone Intelligence Library
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import hashlib
import time
import pickle
import gzip
import threading


class CachePolicy(Enum):
    """Simplified cache policy options."""
    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    data: Any
    timestamp: float


class TelintError(Exception):
    """Base exception for telint errors."""
    pass


class MetadataDownloadError(TelintError):
    """Raised when metadata download fails."""
    pass


class _Const:
    """Constants for phone number validation and metadata sources."""
    metadata_urls: dict[str, str] = {

        'phone_metadata': [
            'https://cdn.jsdelivr.net/gh/jackocnr/intl-tel-input@master/build/js/data.json'
        ],

        'country_data': [
            'https://raw.githubusercontent.com/mledoze/countries/master/countries.json'
        ]
    }

    CACHE_DIR = Path.home() / '.telint_cache'
    CACHE_TTL = 86400  # 24 hours
    REQUEST_TIMEOUT = 10  # seconds


class _CacheManager:
    """Simplified cache manager."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.CacheManager")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    def get(self, key: str) -> Any:
        """Get item from cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                compressed_data = f.read()
                data = gzip.decompress(compressed_data)
                entry = pickle.loads(data)
                return entry.data
        except Exception as e:
            self.logger.warning(f"Failed to load cache entry {key}: {e}")
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> bool:
        """Set item in cache."""
        cache_path = self._get_cache_path(key)
        entry = CacheEntry(data=value, timestamp=time.time())

        try:
            serialized = pickle.dumps(entry)
            compressed = gzip.compress(serialized)

            with open(cache_path, 'wb') as f:
                f.write(compressed)
            return True
        except Exception as e:
            self.logger.warning(f"Failed to save cache entry {key}: {e}")
            return False

    def is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return True

        try:
            with open(cache_path, 'rb') as f:
                compressed_data = f.read()
                data = gzip.decompress(compressed_data)
                entry = pickle.loads(data)
                return time.time() - entry.timestamp > _Const.CACHE_TTL
        except Exception:
            return True


class _MetadataHandler:
    """Simplified metadata handler."""

    def __init__(self, cache_policy: CachePolicy = CachePolicy.CACHE_FIRST):
        self.cache_policy = cache_policy
        self.cache_manager = _CacheManager(_Const.CACHE_DIR)
        self._metadata_cache = {}
        self._load_metadata()

    def _download_json(self, url: str, cache_key: str) -> Optional[Dict]:
        """Download JSON data from URL with caching."""
        try:
            # Check cache first if policy is CACHE_FIRST
            if self.cache_policy == CachePolicy.CACHE_FIRST:
                cached_data = self.cache_manager.get(cache_key)
                if cached_data is not None and not self.cache_manager.is_expired(cache_key):
                    return cached_data

            # Download fresh data
            request = urllib.request.Request(url, headers={'User-Agent': 'telint-metadata-fetcher/1.0'})
            with urllib.request.urlopen(request, timeout=_Const.REQUEST_TIMEOUT) as response:
                data = response.read()
                json_data = json.loads(data.decode('utf-8'))
                self.cache_manager.set(cache_key, json_data)
                return json_data

        except Exception as e:
            logging.warning(f"Failed to download {url}: {e}")
            # Return cached data even if expired
            return self.cache_manager.get(cache_key)

    def _load_metadata(self):
        """Load metadata from backup sources."""
        # Load country data
        country_data = self._download_json(
            _Const.metadata_urls['country_data'][0],
            'country_data'
        )
        if country_data:
            self._metadata_cache['countries'] = {
                country.get('cca2', ''): {
                    'name': country.get('name', {}).get('common', ''),
                    'calling_code': country.get('idd', {}).get('root', '') +
                                    (country.get('idd', {}).get('suffixes', [''])[0] if country.get('idd', {}).get(
                                        'suffixes') else ''),
                } for country in country_data if isinstance(country, dict)
            }

        # Load phone metadata
        phone_metadata = self._download_json(
            _Const.metadata_urls['phone_metadata'][0],
            'phone_metadata'
        )
        if phone_metadata:
            self._metadata_cache['phone_data'] = phone_metadata

    def get_country_info(self, country_code: str) -> Optional[Dict]:
        """Get country information from metadata."""
        countries = self._metadata_cache.get('countries', {})
        return countries.get(country_code.upper())


import re
from typing import Optional, Dict, Any


class PhoneNumber:
    """A class for handling phone number validation and information extraction."""

    _metadata_handler = None

    def __init__(self, number: str, region: Optional[str] = None) -> None:
        """
        Initialize a PhoneNumber instance.

        Args:
            number: The phone number string to analyze
            region: Optional country/region code (e.g., 'US', 'UK', 'DZ')

        Raises:
            ValueError: If number is empty or invalid format
        """
        if not number or not isinstance(number, str):
            raise ValueError("Phone number must be a non-empty string")

        # Initialize metadata handler if not already done
        if PhoneNumber._metadata_handler is None:
            PhoneNumber._metadata_handler = _MetadataHandler()

        self.number = self._normalize_number(number)
        self.region = region.upper() if region else self._detect_region()

    @staticmethod
    def _normalize_number(number: str) -> str:
        """Remove non-digit characters except + from phone number."""
        return re.sub(r'[^\d+]', '', number)

    def _detect_region(self) -> Optional[str]:
        """Attempt to detect region from number format."""
        # If number starts with +, try to extract country code
        if self.number.startswith('+'):
            # Extract potential country codes (1-4 digits)
            for i in range(1, 5):
                if len(self.number) > i:
                    potential_code = self.number[1:i + 1]
                    # Check against known country codes
                    countries = self._metadata_handler._metadata_cache.get('countries', {})
                    for code, info in countries.items():
                        if info.get('calling_code', '').replace('+', '') == potential_code:
                            return code
        return None

    @property
    def is_valid(self) -> bool:
        """Check if the phone number is valid."""
        if not self.number:
            return False

        # Basic validation: should have 7-15 digits
        digits_only = re.sub(r'[^\d]', '', self.number)
        return 7 <= len(digits_only) <= 15

    @property
    def type(self) -> str:
        """
        Get phone number type.
        Returns 'mobile', 'landline', or 'unknown'.
        """
        if not self.is_valid or not self.region:
            return "unknown"

        # Simple heuristic: mobile numbers often start with specific digits
        digits = re.sub(r'[^\d]', '', self.number)
        if len(digits) > 3:
            first_digits = digits[-10:][:2]  # Look at first 2 digits of local number
            if first_digits in ['70', '77', '78', '79', '55', '50']:
                return "mobile"
            if first_digits in ['20', '30', '40']:
                return "landline"

        return "unknown"

    @property
    def country_name(self) -> Optional[str]:
        """Get the phone number's country name."""
        if not self.region:
            return None

        country_info = self._metadata_handler.get_country_info(self.region)
        return country_info.get('name') if country_info else None

    @property
    def calling_code(self) -> Optional[str]:
        """Get the phone number's calling code."""
        if not self.region:
            return None

        country_info = self._metadata_handler.get_country_info(self.region)
        return country_info.get('calling_code') if country_info else None

    def get_number_report(self) -> Dict[str, Any]:
        """Get comprehensive phone number report as a dictionary."""
        return {
            'number': self.number,
            'region': self.region,
            'is_valid': self.is_valid,
            'type': self.type,
            'country_name': self.country_name,
            'calling_code': self.calling_code,
        }

    def __str__(self) -> str:
        """String representation of the phone number."""
        return f"PhoneNumber({self.number}, {self.region})"

    def __repr__(self) -> str:
        """Detailed string representation of the phone number."""
        return f"PhoneNumber(number='{self.number}', region='{self.region}')"

if __name__ == '__main__':
    sys.exit(0)
