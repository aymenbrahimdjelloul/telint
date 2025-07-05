"""


@author : Aymen Brahim Djelloul
@version : 0.1
@date : 07.05.2025
@license : MIT License

"""

# IMPORTS
import unittest
import telint


class Test(unittest.TestCase):

    def test_phone_number(self) -> None:
        """ This method will test the functionality of telint
            PhoneNumber class and check for number validity and carrier, country name, region, timezone, type
        """


# Test formating
numbers = [
    ("+1 650-555-1234", "US"),
    ("+44 20 7946 0958", "UK"),
    ("011 33 1 42 68 53 00", "FR"),
    ("555-1234", "US")
]

for num, country in numbers:
    formatter = NumFormatter(num, country)
    print(f"\nOriginal: {num}")
    print(f"E.164: {formatter.format(PhoneFormat.E164)}")
    print(f"International: {formatter.format(PhoneFormat.INTERNATIONAL)}")
    print(f"National: {formatter.format(PhoneFormat.NATIONAL)}")
    print(f"Dashed: {formatter.format(PhoneFormat.DASHED)}")
    print(f"Local: {formatter.format(PhoneFormat.LOCAL)}")