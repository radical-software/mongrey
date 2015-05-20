# -*- coding: utf-8 -*-

import os, sys
CURRENT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(CURRENT, '..', '..')))
from shared_conf import *

language = "en"
today_fmt = '%Y-%m-%d %H:%M:%S'
html_last_updated_fmt = today_fmt
html_static_path = ['_static', '../../_static']

extlinks = {
    'wikipedia': ('http://fr.wikipedia.org/wiki/' '%s', ''),
}

html_theme_options['lang'] = 'en'
html_search_language = "en"