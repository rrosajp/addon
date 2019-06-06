# -*- coding: utf-8 -*-

from servers import turbovid

def test_video_exists(page_url):
    return turbovid.test_video_exists(page_url)

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    return turbovid.get_video_url(page_url, premium, user, password, video_password, 'deltabit')
