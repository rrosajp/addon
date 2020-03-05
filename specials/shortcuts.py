# -*- coding: utf-8 -*-

def context():
	from platformcode import config
	context = []

	if config.get_setting('quick_menu'): context += [{ 'title': config.get_localized_string(60360).upper(), 'channel': 'shortcuts', 'action': "shortcut_menu"}]
	if config.get_setting('side_menu'): context += [{ 'title': config.get_localized_string(70737).upper(), 'channel': 'shortcuts', 'action': "side_menu"}]
	if config.get_setting('kod_menu'): context += [{ 'title': config.get_localized_string(30025), 'channel': 'shortcuts', 'action': "settings_menu"}]

	return context

def side_menu(item):
    from specials import side_menu
    side_menu.open_menu(item)

def shortcut_menu(item):
    from platformcode import keymaptools
    keymaptools.open_shortcut_menu()

def settings_menu(item):
	from platformcode import config
	config.open_settings()