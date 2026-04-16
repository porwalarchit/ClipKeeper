#!/usr/bin/env python3
"""
ClipKeeper v2 — Clipboard History Manager for Ubuntu
Built with PyQt5 (pip-installable, no sudo needed).
Stores clipboard items, persists across reboots.
"""

import sys
import os

# Ensure the directory containing this script is on sys.path so the
# clipkeeper package (clipkeeper/) can be found when running directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clipkeeper import main

if __name__ == '__main__':
    main()
