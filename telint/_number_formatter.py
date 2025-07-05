"""

@author  : Aymen Brahim Djelloul
@version : 1.0.0
@date : 07.05.2025
@license : MIT License


"""

# IMPORTS
import re
import sys
from enum import Enum
from typing import Optional


class PhoneFormat(Enum):
    """Supported formatting styles"""
    E164 = 1          # +CCNNNNNNNNN
    INTERNATIONAL = 2  # +CC NNN NNN NNNN
    NATIONAL = 3       # (0NN) NNN-NNNN (country-specific)
    DASHED = 4        # +CC-NNN-NNN-NNNN
    DOT = 5           # +CC.NNN.NNN.NNNN
    PARENTHESES = 6   # +CC (NNN) NNN-NNNN
    SPACES = 7        # +CC NNN NNN NNNN
    RFC3966 = 8       # tel:+CC-NNN-NNN-NNNN
    LOCAL = 9         # NNN-NNNN (no country code)

class NumFormatter:
    """
    Pure phone number formatter with:
    - 9 formatting styles
    - Country-aware national formatting
    - Extension handling
    - Minimal dependencies
    """

    # Common international prefixes
    INTL_PREFIXES = {
        '00': '+',
        '011': '+',
        '810': '+'
    }

    # Basic country formatting rules (extend as needed)
    COUNTRY_RULES = {
        'US': {
            'code': '1',
            'pattern': [3, 3, 4],
            'national_prefix': '1',
            'trunk_prefix': '1'
        },
        'UK': {
            'code': '44',
            'pattern': [4, 3, 4],
            'national_prefix': '0',
            'trunk_prefix': '0'
        },
        'FR': {
            'code': '33',
            'pattern': [3, 3, 3, 3],
            'national_prefix': '0',
            'trunk_prefix': '0'
        }
    }

    def __init__(self, number: str, country_code: Optional[str] = None):
        """
        Initialize with raw number and optional country code

        Args:
            number: Raw phone number string
            country_code: ISO country code (e.g., 'US', 'UK')
        """
        self.original = number.strip()
        self.country_code = country_code.upper() if country_code else None
        self._digits = self._extract_digits()
        self._extension = self._extract_extension()

    def format(self, style: PhoneFormat = PhoneFormat.E164) -> str:
        """
        Format the number according to specified style

        Args:
            style: One of the PhoneFormat enum values

        Returns:
            Formatted phone number string
        """
        digits = self._digits

        if style == PhoneFormat.E164:
            return self._format_e164(digits)
        elif style == PhoneFormat.INTERNATIONAL:
            return self._format_international(digits)
        elif style == PhoneFormat.NATIONAL:
            return self._format_national(digits)
        elif style == PhoneFormat.DASHED:
            return self._format_delimited(digits, '-')
        elif style == PhoneFormat.DOT:
            return self._format_delimited(digits, '.')
        elif style == PhoneFormat.PARENTHESES:
            return self._format_parentheses(digits)
        elif style == PhoneFormat.SPACES:
            return self._format_spaces(digits)
        elif style == PhoneFormat.RFC3966:
            return f"tel:{self._format_delimited(digits, '-')}"
        elif style == PhoneFormat.LOCAL:
            return self._format_local(digits)
        else:
            raise ValueError(f"Unknown format style: {style}")

    def _extract_digits(self) -> str:
        """Extract only digits from the number"""
        # Remove all non-digit characters except leading +
        cleaned = re.sub(r'(?!^\+)[^\d]', '', self.original)

        # Replace international prefixes
        for prefix, replacement in self.INTL_PREFIXES.items():
            if cleaned.startswith(prefix):
                cleaned = replacement + cleaned[len(prefix):]
                break

        return cleaned

    def _extract_extension(self) -> str:
        """Extract extension if present"""
        match = re.search(r'(?:ext|ex|x|#)\s*(\d+)$', self.original, re.IGNORECASE)
        return match.group(1) if match else ''

    def _format_e164(self, digits: str) -> str:
        """Format in E.164 standard (+CCNNNNNNNNN)"""
        if digits.startswith('+'):
            return digits + (f" ext{self._extension}" if self._extension else '')

        if not self.country_code:
            return digits  # Can't properly format without country code

        country_rule = self.COUNTRY_RULES.get(self.country_code)
        if not country_rule:
            return digits

        return f"+{country_rule['code']}{digits.lstrip(country_rule['national_prefix'])}" + \
               (f" ext{self._extension}" if self._extension else '')

    def _format_international(self, digits: str) -> str:
        """Format with international spacing (+CC NNN NNN NNNN)"""
        e164 = self._format_e164(digits)
        if not e164.startswith('+'):
            return e164

        # Split into country code and national number
        country_code = e164[1:3] if len(e164) > 3 else e164[1:]
        national_num = e164[len(country_code)+1:]

        # Group digits
        grouped = self._group_digits(national_num)
        return f"+{country_code} {grouped}"

    def _format_national(self, digits: str) -> str:
        """Format according to national conventions"""
        if not self.country_code:
            return digits

        country_rule = self.COUNTRY_RULES.get(self.country_code)
        if not country_rule:
            return digits

        # Remove country code if present
        national_num = digits.lstrip(country_rule['code']).lstrip(country_rule['national_prefix'])

        # Apply national formatting pattern
        return self._group_digits(national_num, country_rule['pattern'])

    def _group_digits(self, digits: str, pattern: Optional[list] = None) -> str:
        """Group digits according to specified pattern"""
        if not pattern:
            pattern = [3, 3, 4]  # Default grouping

        result = []
        pos = 0
        for group in pattern:
            if pos >= len(digits):
                break
            result.append(digits[pos:pos+group])
            pos += group

        # Add remaining digits
        if pos < len(digits):
            result.append(digits[pos:])

        return '-'.join(result)

    def _format_delimited(self, digits: str, delimiter: str) -> str:
        """Generic delimited formatter"""
        e164 = self._format_e164(digits)
        if not e164.startswith('+'):
            return e164

        country_code = e164[1:3] if len(e164) > 3 else e164[1:]
        national_num = e164[len(country_code)+1:]

        grouped = self._group_digits(national_num)
        return f"+{country_code}{delimiter}{grouped.replace('-', delimiter)}"

    def _format_parentheses(self, digits: str) -> str:
        """Format with parentheses for area code"""
        if not self.country_code:
            return self._format_international(digits)

        country_rule = self.COUNTRY_RULES.get(self.country_code)
        if not country_rule:
            return self._format_international(digits)

        national_num = digits.lstrip(country_rule['code']).lstrip(country_rule['national_prefix'])
        area_code_length = country_rule['pattern'][0] if country_rule['pattern'] else 3

        if len(national_num) <= sum(country_rule['pattern']):
            area_code = national_num[:area_code_length]
            local_num = national_num[area_code_length:]
            grouped_local = self._group_digits(local_num, country_rule['pattern'][1:])
            return f"+{country_rule['code']} ({area_code}) {grouped_local}"

        return self._format_international(digits)

    def _format_spaces(self, digits: str) -> str:
        """Format with spaces between groups"""
        return self._format_delimited(digits, ' ').replace('-', ' ')

    def _format_local(self, digits: str) -> str:
        """Format without country code"""
        if not self.country_code:
            return digits

        country_rule = self.COUNTRY_RULES.get(self.country_code)
        if not country_rule:
            return digits

        national_num = digits.lstrip(country_rule['code']).lstrip(country_rule['national_prefix'])
        return self._group_digits(national_num, country_rule['pattern'])

# Example usage
if __name__ == "__main__":
    sys.exit(0)
