# -*- coding: utf-8 -*-

import xbmcgui, xbmc, os, sys
from platformcode import platformtools, xbmc_videolibrary, config
from core import filetools, scrapertools
from core.support import log, dbg
from distutils import dir_util, file_util
from xml.dom import minidom


def move_videolibrary(current_path, new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder):
    log()
    log('current video library path:', current_path)
    log('new video library path:', new_path)
    log('current movies folder:', current_movies_folder)
    log('new movies folder:', new_movies_folder)
    log('current tvshows folder:', current_tvshows_folder)
    log('new tvshows folder:', new_tvshows_folder)

    backup_current_path = current_path
    backup_new_path = new_path

    if current_path != new_path or current_movies_folder != new_movies_folder or current_tvshows_folder != new_tvshows_folder:
        notify = False
        progress = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80011))
        current_path = xbmc.translatePath(current_path)
        new_path = xbmc.translatePath(new_path)
        current_movies_path = filetools.join(current_path, current_movies_folder)
        new_movies_path = filetools.join(new_path, new_movies_folder)
        current_tvshows_path = os.path.join(current_path, current_tvshows_folder)
        new_tvshows_path = os.path.join(new_path, new_tvshows_folder)

        config.verify_directories_created()
        progress.update(10, config.get_localized_string(20000), config.get_localized_string(80012))
        if current_movies_path != new_movies_path:
            if filetools.listdir(current_movies_path):
                dir_util.copy_tree(current_movies_path, new_movies_path)
                notify = True
            filetools.rmdirtree(current_movies_path)
        progress.update(40)
        if current_tvshows_path != new_tvshows_path:
            if filetools.listdir(current_tvshows_path):
                dir_util.copy_tree(current_tvshows_path, new_tvshows_path)
                notify = True
            filetools.rmdirtree(current_tvshows_path)
        progress.update(70)
        if current_path != new_path and not filetools.listdir(current_path) and not "plugin.video.kod\\videolibrary" in current_path:
            filetools.rmdirtree(current_path)

        if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
            set_new_path(backup_current_path, backup_new_path)
            update_db(backup_current_path, backup_new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder, progress)
            clear_cache()
        else:
            progress.update(90, config.get_localized_string(20000), config.get_localized_string(80013))

        progress.update(100)
        progress.close()
        if notify:
            platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80014), icon=0, time=5000, sound=False)


def update_db(current_path, new_path, current_movies_folder, new_movies_folder, current_tvshows_folder, new_tvshows_folder, progress):
    log()

    new = new_path
    old = current_path

    # rename main path for search in the DB
    if new.startswith("special://") or scrapertools.find_single_match(new, r'(^\w+:\/\/)'):
        new = new.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
        sep = '/'
    else:
        sep = os.sep
    if not new.endswith(sep):
        new += sep

    if old.startswith("special://") or scrapertools.find_single_match(old, r'(^\w+:\/\/)'):
        old = old.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
        sep = '/'
    else:
        sep = os.sep
    if not old.endswith(sep):
        old += sep

    # search MAIN path in the DB
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    # change main path
    if records:
        idPath = records[0][0]
        strPath = records[0][1].replace(current_path, new_path)
        sql = 'UPDATE path SET strPath="%s" WHERE idPath=%s' % (strPath, idPath)
        nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    p = 80
    progress.update(90, config.get_localized_string(20000), config.get_localized_string(80013))

    OLD = old
    for OldPath, NewPath in [[current_movies_folder, new_movies_folder], [current_tvshows_folder, new_tvshows_folder]]:
        old = OLD + OldPath
        if not old.endswith(sep): old += sep

        # Search Main Sub Folder
        sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
        nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

        # Change Main Sub Folder
        if records:
            for record in records:
                idPath = record[0]
                strPath = record[1].replace(filetools.join(current_path, OldPath), filetools.join(new_path, NewPath))
                sql = 'UPDATE path SET strPath="%s"WHERE idPath=%s' % (strPath, idPath)
                nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

        # Search if Sub Folder exixt in all paths
        old += '%'
        sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % old
        nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

        #Change Sub Folder in all paths
        if records:
            for record in records:
                idPath = record[0]
                strPath = record[1].replace(filetools.join(current_path, OldPath), filetools.join(new_path, NewPath))
                sql = 'UPDATE path SET strPath="%s"WHERE idPath=%s' % (strPath, idPath)
                nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)


        if OldPath == current_movies_folder:
            # if is Movie Folder
            # search and modify in "movie"
            sql = 'SELECT idMovie, c22 FROM movie where c22 LIKE "%s"' % old
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
            if records:
                for record in records:
                    idMovie = record[0]
                    strPath = record[1].replace(filetools.join(current_path, OldPath), filetools.join(new_path, NewPath))
                    sql = 'UPDATE movie SET c22="%s" WHERE idMovie=%s' % (strPath, idMovie)
                    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
        else:
            # if is Tv Show Folder
            # search and modify in "episode"
            sql = 'SELECT idEpisode, c18 FROM episode where c18 LIKE "%s"' % old
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
            if records:
                for record in records:
                    idEpisode = record[0]
                    strPath = record[1].replace(filetools.join(current_path, OldPath), filetools.join(new_path, NewPath))
                    sql = 'UPDATE episode SET c18="%s" WHERE idEpisode=%s' % (strPath, idEpisode)
                    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
        p += 5
        progress.update(90, config.get_localized_string(20000), config.get_localized_string(80013))

def clear_videolibrary_db():
    log()
    progress = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(60601))
    progress.update(0)


    config.set_setting('videolibrary_kodi_flag', 1)
    config.set_setting('videolibrary_kodi', False)
    path = config.get_setting('videolibrarypath')

    # rename main path for search in the DB
    if path.startswith("special://") or scrapertools.find_single_match(path, r'(^\w+:\/\/)'):
        path = path.replace('/profile/', '/%/').replace('/home/userdata/', '/%/')
        sep = '/'
    else:
        sep = os.sep
    if not path.endswith(sep):
        path += sep

    # search path in the db
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % path
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    # change main path
    if records:
        idPath = records[0][0]
        sql = 'DELETE from path WHERE idPath=%s' % idPath
        nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    progress.update(20)

    path += '%'
     # search path in the db
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % path
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    # change main path
    if records:
        for record in records:
            idPath = record[0]
            sql = 'DELETE from path WHERE idPath=%s' % idPath
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    # search path in the db
    sql = 'SELECT idMovie, c22 FROM movie where c22 LIKE "%s"' % path
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    progress.update(40)
    # change main path
    if records:
        for record in records:
            idMovie = record[0]
            sql = 'DELETE from movie WHERE idMovie=%s' % idMovie
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)

    # search path in the db
    sql = 'SELECT idEpisode, c18 FROM episode where c18 LIKE "%s"' % path
    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    progress.update(60)
    # change main path
    if records:
        for record in records:
            idEpisode = record[0]
            sql = 'DELETE from episode WHERE idEpisode=%s' % idEpisode
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)
    progress.update(80)
    set_new_path(path)
    clear_cache()
    progress.update(100)
    progress.close()


def set_new_path(old, new=''):
    log()
    SOURCES_PATH = xbmc.translatePath("special://userdata/sources.xml")
    if filetools.isfile(SOURCES_PATH):
        xmldoc = minidom.parse(SOURCES_PATH)

        # collect nodes
        # nodes = xmldoc.getElementsByTagName("video")
        video_node = xmldoc.childNodes[0].getElementsByTagName("video")[0]
        paths_node = video_node.getElementsByTagName("path")

        # delete old path
        for node in paths_node:
            if node.firstChild.data == old:
                parent = node.parentNode
                remove = parent.parentNode
                remove.removeChild(parent)

        # write changes
        if sys.version_info[0] >= 3: #PY3
            filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
        else:
            filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)

        if new:
            # create new path
            list_path = [p.firstChild.data for p in paths_node]
            if new in list_path:
                log("path %s already exists in sources.xml" % new)
                return
            log("path %s does not exist in sources.xml" % new)

            # if the path does not exist we create one
            source_node = xmldoc.createElement("source")

            # <name> Node
            name_node = xmldoc.createElement("name")
            sep = os.sep
            if new.startswith("special://") or scrapertools.find_single_match(new, r'(^\w+:\/\/)'):
                sep = "/"
            name = new
            if new.endswith(sep):
                name = new[:-1]
            name_node.appendChild(xmldoc.createTextNode(name.rsplit(sep)[-1]))
            source_node.appendChild(name_node)

            # <path> Node
            path_node = xmldoc.createElement("path")
            path_node.setAttribute("pathversion", "1")
            path_node.appendChild(xmldoc.createTextNode(new))
            source_node.appendChild(path_node)

            # <allowsharing> Node
            allowsharing_node = xmldoc.createElement("allowsharing")
            allowsharing_node.appendChild(xmldoc.createTextNode('true'))
            source_node.appendChild(allowsharing_node)

            # Añadimos <source>  a <video>
            video_node.appendChild(source_node)

            # write changes
            if sys.version_info[0] >= 3: #PY3
                filetools.write(SOURCES_PATH, '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))
            else:
                filetools.write(SOURCES_PATH, b'\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]), vfs=False)

    else:
        xmldoc = minidom.Document()
        source_nodes = xmldoc.createElement("sources")

        for type in ['programs', 'video', 'music', 'picture', 'files']:
            nodo_type = xmldoc.createElement(type)
            element_default = xmldoc.createElement("default")
            element_default.setAttribute("pathversion", "1")
            nodo_type.appendChild(element_default)
            source_nodes.appendChild(nodo_type)
        xmldoc.appendChild(source_nodes)


def clear_cache():
    path = xbmc.translatePath('special://home/cache/archive_cache/')
    for file in filetools.listdir(path):
        log(file)
        filetools.remove(filetools.join(path, file))