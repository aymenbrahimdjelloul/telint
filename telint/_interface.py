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
import sys
import os
import telint
import shutil
import argparse

try:
    from colorama import Fore, Style, unittest

    init(autoreset=True)

    class Colors:
        pass

except ImportError:

    colorama = None

    class Colors:
        pass


class Const:

    author: str = "Aymen Brahim Djelloul"
    version: str = "0.1"
    date: str = "04.07.2025"
    license: str = "MIT License"
    title: str = f"Telint - v{version}"

    help_text: str = """
    
    """


class Interface:

    def __init__(self) -> None:
        pass


    def _print_header(self) -> None:
        """ This method will print the header"""

    def _print_help(self) -> None:
        """ This method will print the help """

    def _clear_screen(self) -> None:
        """ This method will clear the console for both linux and windows"""

    def _set_title(self) -> None:
        """ This method will set the title for both linux and windows"""

    def run(self) -> None:
        """ This method will run the CLI"""


        # set title
        self._set_title()

        # Print header
        self._print_header()

def __main__():
    """ This is the entry point for the CLI """

    try:

        cli = Interface()
        cli.run()

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    sys.exit(0)