# -*- coding: utf-8 -*-
"""TriSight_v5.html：「前のページに戻る」は前の画面が無いときは出さない（2026-11-06）。中身は backbar_common.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from backbar_common import main
if __name__ == '__main__':
    sys.exit(main('TriSight_v5.html'))
