# -*- coding: utf-8 -*-
"""index.html：端末の札が、中継あての認証コード付きの通信に付く（2026-11-12）。中身は devtag_common.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from devtag_common import main
if __name__ == '__main__':
    sys.exit(main('index.html'))
