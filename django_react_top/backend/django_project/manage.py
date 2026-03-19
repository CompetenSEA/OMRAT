#!/usr/bin/env python
"""Django management entrypoint for the standalone OMRAT web backend."""

import os
import sys


def main() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omrat_web.settings')
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
