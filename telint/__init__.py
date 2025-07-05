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

# IMPORTS
from ._phone_number import PhoneNumber
from ._number_parser import NumParser
from ._number_formatter import NumFormatter
from ._interface import __main__

__all__ = ["PhoneNumber", "NumFormatter", "NumParser", "__main__"]
__version__ = "0.1"
