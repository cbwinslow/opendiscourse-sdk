#!/usr/bin/env python3
"""
Comprehensive Bill Text Extraction System

This script implements a hybrid approach to extract bill text from multiple sources:
1. GovInfo API (primary source for comprehensive text coverage)
2. Congress.gov API scraping (fallback)
3. OCR for PDF/image content (last resort)

Author: OpenDiscourse AI Agent
Date: December 3, 2025
"""

import os
import sys
import requests
import psycopg2
import logging
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.rate_limiter import rate_limiter
from scripts.env_config import get_optional_env_var

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BillTextResult:
    """Result of bill text extraction"""
    bill_id: str
    congress: int
    bill_type: str
    bill_number: int
    text_content: str
    source: str  # 'govinfo', 'congress_gov', 'ocr'
    format: str  # 'xml', 'html', 'plain', 'ocr'
    extracted_at: datetime
    metadata: Dict[str, Any]

class BillTextExtractor:
    """Comprehensive bill text extraction system"""

    def __init__(self):
        self.govinfo_api_key = get_optional_env_var('GOVINFO_API_KEY')
        self.congress_api_key = get_optional_env_var('CONGRESS_API_KEY')
        self.session = requests.Session()

        # Configure headers for different APIs
        self.session.headers.update({
            'User-Agent': 'OpenDiscourse-BillTextExtractor/1.0'
        })

        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'govinfo_success': 0,
            'congress_success': 0,
            'ocr_success': 0,
            'total_failures': 0,
            'source_breakdown': {}
        }

    def extract_bill_text(self, congress: int, bill_type: str, bill_number: int) -> Optional[BillTextResult]:
        """
        Extract bill text using hybrid approach

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'HR', 'S', 'HJRES')
            bill_number: Bill number (e.g., 897)

        Returns:
            BillTextResult if successful, None otherwise
        """
        self.stats['total_processed'] += 1

        bill_id = f"{congress}-{bill_type}-{bill_number}"
        logger.info(f"Extracting text for bill: {bill_id}")

        # Phase 1: Try Congress.gov web scraping (primary source)
        result = self._extract_from_congress_website(congress, bill_type, bill_number)
        if result:
            self.stats['congress_success'] += 1
            logger.info(f"✅ Congress.gov web extraction successful for {bill_id}")
            return result

        # Phase 2: Try GovInfo API (fallback)
        result = self._extract_from_govinfo(congress, bill_type, bill_number)
        if result:
            self.stats['govinfo_success'] += 1
            logger.info(f"✅ GovInfo extraction successful for {bill_id}")
            return result

        # Phase 3: Try Congress.gov API as another fallback
        result = self._extract_from_congress_gov(congress, bill_type, bill_number)
        if result:
            self.stats['congress_success'] += 1
            logger.info(f"✅ Congress.gov API extraction successful for {bill_id}")
            return result

        # Phase 4: Try OCR as last resort
        result = self._extract_with_ocr(congress, bill_type, bill_number)
        if result:
            self.stats['ocr_success'] += 1
            logger.info(f"✅ OCR extraction successful for {bill_id}")
            return result

        # All methods failed
        self.stats['total_failures'] += 1
        logger.error(f"❌ All extraction methods failed for {bill_id}")
        return None

    def _extract_from_congress_website(self, congress: int, bill_type: str, bill_number: int) -> Optional[BillTextResult]:
        """Extract bill text by scraping Congress.gov website"""
        try:
            # Construct the Congress.gov bill URL
            bill_url = f"https://www.congress.gov/bill/{congress}th-congress/{bill_type.lower()}-{bill_number}"

            logger.info(f"Scraping Congress.gov website: {bill_url}")

            # Rate limiting for web requests
            time.sleep(1)  # Be respectful to the website

            response = self.session.get(bill_url, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple selectors to find bill text
            text_content = None

            # Method 1: Look for bill text in specific divs
            text_selectors = [
                '.bill-text-container',
                '.full-text-display',
                '.bill-summary',
                '.overview',
                '[data-testid="bill-text"]',
                '.legislation-text'
            ]

            for selector in text_selectors:
                text_element = soup.select_one(selector)
                if text_element:
                    text_content = self._extract_text_from_html(str(text_element))
                    if text_content and len(text_content.strip()) > 200:
                        break

            # Method 2: Look for "Full Text" link and follow it
            if not text_content:
                full_text_link = soup.find('a', string=lambda text: text and 'Full Text' in text)
                if full_text_link and full_text_link.get('href'):
                    full_text_url = full_text_link['href']
                    if not full_text_url.startswith('http'):
                        full_text_url = f"https://www.congress.gov{full_text_url}"

                    time.sleep(1)  # Rate limiting
                    text_response = self.session.get(full_text_url, timeout=30)
                    text_response.raise_for_status()

                    text_soup = BeautifulSoup(text_response.text, 'html.parser')
                    text_content = self._extract_text_from_html(text_response.text)

            # Method 3: Look for bill summary/overview as fallback
            if not text_content:
                summary_selectors = [
                    '.bill-summary',
                    '.overview',
                    '.summary-text',
                    '.bill-details'
                ]

                for selector in summary_selectors:
                    summary_element = soup.select_one(selector)
                    if summary_element:
                        text_content = self._extract_text_from_html(str(summary_element))
                        if text_content and len(text_content.strip()) > 100:
                            break

            if text_content and len(text_content.strip()) > 100:
                return BillTextResult(
                    bill_id=f"{congress}-{bill_type}-{bill_number}",
                    congress=congress,
                    bill_type=bill_type,
                    bill_number=bill_number,
                    text_content=text_content,
                    source='congress_website',
                    format='html',
                    extracted_at=datetime.now(),
                    metadata={
                        'source_url': bill_url,
                        'extraction_method': 'web_scraping',
                        'content_length': len(text_content)
                    }
                )

        except Exception as e:
            logger.error(f"Congress.gov web scraping error for {congress}-{bill_type}-{bill_number}: {e}")

        return None

    def _extract_from_govinfo(self, congress: int, bill_type: str, bill_number: int) -> Optional[BillTextResult]:
        """Extract bill text from GovInfo API"""
        try:
            if not self.govinfo_api_key:
                logger.warning("GovInfo API key not available")
                return None

            # Convert bill type to GovInfo format
            govinfo_bill_type = self._convert_bill_type_for_govinfo(bill_type)

            # Search for bill packages
            search_url = "https://api.govinfo.gov/packages"
            params = {
                'api_key': self.govinfo_api_key,
                'pageSize': 100,
                'offsetMark': 0,
                'congress': congress,
                'packageType': 'BILLS',
                'billVersion': govinfo_bill_type
            }

            # Rate limiting for GovInfo API
            rate_limiter.wait("govinfo.gov")

            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()

            packages = response.json().get('packages', [])

            # Find matching package
            target_package = None
            for package in packages:
                package_name = package.get('packageId', '')
                if f"{congress}{bill_type}{bill_number}" in package_name:
                    target_package = package
                    break

            if not target_package:
                logger.debug(f"No GovInfo package found for {congress}-{bill_type}-{bill_number}")
                return None

            # Get package content
            package_url = f"https://api.govinfo.gov/packages/{target_package['packageId']}"
            params = {'api_key': self.govinfo_api_key}

            rate_limiter.wait("govinfo.gov")
            response = self.session.get(package_url, params=params, timeout=30)
            response.raise_for_status()

            package_data = response.json()

            # Extract text from different formats
            text_content = self._extract_text_from_govinfo_package(package_data)

            if text_content:
                return BillTextResult(
                    bill_id=f"{congress}-{bill_type}-{bill_number}",
                    congress=congress,
                    bill_type=bill_type,
                    bill_number=bill_number,
                    text_content=text_content,
                    source='govinfo',
                    format=self._detect_text_format(text_content),
                    extracted_at=datetime.now(),
                    metadata={
                        'package_id': target_package['packageId'],
                        'package_name': target_package.get('packageTitle', ''),
                        'last_modified': target_package.get('lastModified', '')
                    }
                )

        except Exception as e:
            logger.error(f"GovInfo extraction error for {congress}-{bill_type}-{bill_number}: {e}")

        return None

    def _extract_from_congress_gov(self, congress: int, bill_type: str, bill_number: int) -> Optional[BillTextResult]:
        """Extract bill text by scraping Congress.gov"""
        try:
            if not self.congress_api_key:
                logger.warning("Congress API key not available")
                return None

            # Get bill details including text versions
            bill_url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}"
            params = {'api_key': self.congress_api_key, 'format': 'json'}

            rate_limiter.wait("congress.gov")
            response = self.session.get(bill_url, params=params, timeout=30)
            response.raise_for_status()

            bill_data = response.json().get('bill', {})

            # Check for text versions
            text_versions = bill_data.get('textVersions', {}).get('textVersions', [])
            if not text_versions:
                logger.debug(f"No text versions found on Congress.gov for {congress}-{bill_type}-{bill_number}")
                return None

            # Get the latest text version
            latest_version = text_versions[0]
            formats = latest_version.get('formats', [])

            # Try different formats in order of preference
            for format_item in formats:
                format_type = format_item.get('type', '').lower()
                url = format_item.get('url', '')

                if not url:
                    continue

                # Rate limiting for Congress.gov API
                rate_limiter.wait("congress.gov")

                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()

                    # Extract text based on format
                    if format_type == 'xml':
                        text_content = self._extract_text_from_xml(response.text)
                    elif format_type == 'html':
                        text_content = self._extract_text_from_html(response.text)
                    elif format_type == 'pdf':
                        # For PDF, we'd need OCR - skip for now
                        continue
                    else:
                        # Try as plain text
                        text_content = response.text

                    if text_content and len(text_content.strip()) > 100:
                        return BillTextResult(
                            bill_id=f"{congress}-{bill_type}-{bill_number}",
                            congress=congress,
                            bill_type=bill_type,
                            bill_number=bill_number,
                            text_content=text_content,
                            source='congress_gov',
                            format=format_type,
                            extracted_at=datetime.now(),
                            metadata={
                                'version': latest_version.get('version', ''),
                                'format_type': format_type,
                                'url': url
                            }
                        )

                except Exception as e:
                    logger.debug(f"Failed to extract {format_type} from Congress.gov: {e}")
                    continue

        except Exception as e:
            logger.error(f"Congress.gov extraction error for {congress}-{bill_type}-{bill_number}: {e}")

        return None

    def _extract_with_ocr(self, congress: int, bill_type: str, bill_number: int) -> Optional[BillTextResult]:
        """Extract text using OCR (placeholder for future implementation)"""
        # TODO: Implement OCR functionality
        logger.info(f"OCR extraction not yet implemented for {congress}-{bill_type}-{bill_number}")
        return None

    def _convert_bill_type_for_govinfo(self, bill_type: str) -> str:
        """Convert bill type to GovInfo format"""
        conversions = {
            'HR': 'hr',
            'S': 's',
            'HJRES': 'hjres',
            'SJRES': 'sjres',
            'HCONRES': 'hconres',
            'SCONRES': 'sconres',
            'HAMEND': 'hamend',
            'SAMEND': 'samend'
        }
        return conversions.get(bill_type.upper(), bill_type.lower())

    def _extract_text_from_govinfo_package(self, package_data: Dict) -> Optional[str]:
        """Extract text from GovInfo package data"""
        try:
            # Try to get text content from different sources in the package
            text_content = None

            # Method 1: Check for text in package metadata
            if 'text' in package_data:
                text_content = package_data['text']

            # Method 2: Get granule content (individual bill text)
            if not text_content and 'granules' in package_data:
                granules = package_data['granules']
                if granules:
                    # Get the first granule (main bill text)
                    granule_url = f"https://api.govinfo.gov/packages/{package_data['packageId']}/granules/{granules[0]['granuleId']}"
                    params = {'api_key': self.govinfo_api_key}

                    rate_limiter.wait("govinfo.gov")
                    response = self.session.get(granule_url, params=params, timeout=30)
                    response.raise_for_status()

                    granule_data = response.json()
                    text_content = granule_data.get('text', '')

            # Method 3: Download and parse XML content
            if not text_content and 'download' in package_data:
                download_url = package_data['download'].get('txtLink', '')
                if download_url:
                    rate_limiter.wait("govinfo.gov")
                    response = self.session.get(download_url, timeout=30)
                    response.raise_for_status()
                    text_content = response.text

            return text_content.strip() if text_content else None

        except Exception as e:
            logger.error(f"Error extracting text from GovInfo package: {e}")
            return None

    def _extract_text_from_xml(self, xml_content: str) -> str:
        """Extract clean text from XML content"""
        try:
            # Parse XML and extract text content
            root = ET.fromstring(xml_content)

            # Remove namespace prefixes for easier parsing
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]

            # Extract text from all elements
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())

            return ' '.join(text_parts)

        except Exception as e:
            logger.debug(f"XML parsing error: {e}")
            return xml_content

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.debug(f"HTML parsing error: {e}")
            return html_content

    def _detect_text_format(self, content: str) -> str:
        """Detect the format of text content"""
        if content.strip().startswith('<?xml'):
            return 'xml'
        elif '<html' in content.lower() or '<body' in content.lower():
            return 'html'
        else:
            return 'plain'

    def save_bill_text_to_database(self, result: BillTextResult) -> bool:
        """Save extracted bill text to database"""
        try:
            conn = psycopg2.connect(
                database='opendiscourse',
                user='cbwinslow',
                host='/var/run/postgresql'
            )
            cursor = conn.cursor()

            # Update the bill record with text content
            update_query = """
            UPDATE congress.bills
            SET summary_text = %s, updated_at = %s
            WHERE congress_number = %s AND bill_type = %s AND bill_number = %s
            """

            cursor.execute(update_query, (
                result.text_content[:5000],  # Limit summary_text length
                result.extracted_at,
                result.congress,
                result.bill_type,
                result.bill_number
            ))

            # Insert into bill_text_versions table for full text
            insert_query = """
            INSERT INTO congress.bill_text_versions (
                bill_id, version, format, source, content, extracted_at, metadata
            ) VALUES (
                (SELECT bill_id FROM congress.bills
                 WHERE congress_number = %s AND bill_type = %s AND bill_number = %s),
                %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (bill_id, version) DO UPDATE SET
                content = EXCLUDED.content,
                extracted_at = EXCLUDED.extracted_at
            """

            cursor.execute(insert_query, (
                result.congress,
                result.bill_type,
                result.bill_number,
                'extracted',  # version
                result.format,
                result.source,
                result.text_content,
                result.extracted_at,
                json.dumps(result.metadata)
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Saved text for bill {result.bill_id} to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save bill text to database: {e}")
            return False

    def print_statistics(self):
        """Print extraction statistics"""
        print("\n" + "="*60)
        print("Bill Text Extraction Statistics")
        print("="*60)
        print(f"Total bills processed: {self.stats['total_processed']}")
        print(f"GovInfo successes:   {self.stats['govinfo_success']}")
        print(f"Congress.gov successes: {self.stats['congress_success']}")
        print(f"OCR successes:       {self.stats['ocr_success']}")
        print(f"Total failures:      {self.stats['total_failures']}")

        if self.stats['total_processed'] > 0:
            success_rate = ((self.stats['govinfo_success'] + self.stats['congress_success'] + self.stats['ocr_success']) / self.stats['total_processed']) * 100
            print(f"Success rate:        {success_rate:.1f}%")

        print("="*60)

def main():
    """Main execution function"""
    extractor = BillTextExtractor()

    # Example usage - extract text for a specific bill
    if len(sys.argv) >= 4:
        congress = int(sys.argv[1])
        bill_type = sys.argv[2]
        bill_number = int(sys.argv[3])

        result = extractor.extract_bill_text(congress, bill_type, bill_number)
        if result:
            print(f"✅ Successfully extracted text for {result.bill_id}")
            print(f"Source: {result.source}")
            print(f"Format: {result.format}")
            print(f"Text length: {len(result.text_content)} characters")

            # Save to database
            if extractor.save_bill_text_to_database(result):
                print("✅ Text saved to database")
            else:
                print("❌ Failed to save to database")
        else:
            print(f"❌ Failed to extract text for {congress}-{bill_type}-{bill_number}")
    else:
        print("Usage: python3 bill_text_extractor.py <congress> <bill_type> <bill_number>")
        print("Example: python3 bill_text_extractor.py 118 HR 897")

    extractor.print_statistics()

if __name__ == "__main__":
    main()
