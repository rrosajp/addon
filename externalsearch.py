import xbmc, sys, xbmcgui, os
from platformcode import config, logger

# incliuding folder libraries
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from core.item import Item


def execute_search():
  """
  Gather the selected ListItem's attributes in order to compute the `Item` parameters
  and perform the KOD's globalsearch.
  Globalsearch will be executed specifing the content-type of the selected ListItem

  NOTE: this method needs the DBTYPE and TMDB_ID specified as ListItem's properties
  """

  # These following lines are commented and keep in the code just as reminder.
  # In future, they could be used to filter the search outcome

  # IMDB: the imdb of the selected ListItem
  # this field is the Kodi's core field (not TMDB)
  #
  # imdb = xbmc.getInfoLabel('ListItem.IMDBNumber')

  # ADDON: maybe can we know if the current windows is related to a specific addon?
  # we could skip the ContextMenu if we already are in KOD's window
  #
  # addon = xbmc.getInfoLabel('ListItem.Property(Addon.ID)')

  # YEAR: the year of the selected ListItem
  # this field is the Kodi's core field
  #
  # year = xbmc.getInfoLabel('ListItem.Year')


  tmdb = xbmc.getInfoLabel('ListItem.Property(tmdb_id)')
  mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
  title = xbmc.getInfoLabel('ListItem.Title')


  logstr = "Selected ListItem is: 'TMDB: {}' - 'Title: {}' - 'Type: {}'".format(tmdb, title, mediatype)
  logger.info(logstr)

  item = Item(
    action="Search",
    channel="globalsearch",
    contentType= mediatype,
    mode="search",
    text= title,
    type= mediatype,
    infoLabels= {
      'tmdb_id': tmdb
    },
    folder= False
  )

  logger.info("Invoking Item: {}".format(item.tostring()))

  itemurl = item.tourl()
  xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + itemurl + ")")


if __name__ == '__main__':
  execute_search()
