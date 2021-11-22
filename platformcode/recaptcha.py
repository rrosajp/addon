# -*- coding: utf-8 -*-
import random
import time
from threading import Thread
from specials.globalsearch import CLOSE

import xbmcgui
from core import httptools
from core import filetools
from platformcode import config, platformtools
from platformcode import logger
from lib.librecaptcha.recaptcha import ReCaptcha, Solver, DynamicSolver, MultiCaptchaSolver, Solution, \
    ImageGridChallenge

lang = 'it'
tiles_pos = (75+390, 90+40)
grid_width = 450
tiles_texture_focus = 'white.png'
tiles_texture_checked = 'Controls/check_mark.png'

TITLE = 10
PANEL = 11
IMAGE = 12
CONTROL = 1

OK = 21
CANCEL = 22
RELOAD = 23


class Kodi:
    def __init__(self, key, referer):
        self.rc = ReCaptcha(
            api_key=key,
            site_url=referer,
            user_agent=httptools.get_user_agent(),
        )

    def run(self) -> str:
        result = self.rc.first_solver()
        while not isinstance(result, str) and result is not False:
            solution = self.run_solver(result)
            if solution:
                result = self.rc.send_solution(solution)
        logger.debug(result)
        platformtools.dialog_notification("Captcha corretto", "Verifica conclusa")
        return result

    def run_solver(self, solver: Solver) -> Solution:
        a = {
            DynamicSolver: DynamicKodi,
            MultiCaptchaSolver: MultiCaptchaKodi,
        }
        b = a[type(solver)]
        c = b("Recaptcha.xml", config.get_runtime_path())
        c.solver = solver
        return c.run()


class SolverKodi(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.goal = ""
        self.closed = False
        self.result = None
        self.image_path = ''
        self.indices = {}
        logger.debug()

    def show_image(self, image, goal):
        self.image_path = config.get_temp_file(str(random.randint(1, 1000)) + '.png')
        filetools.write(self.image_path, image)
        self.goal = goal.replace('<strong>', '[B]').replace('</strong>', '[/B]')
        self.doModal()

    def onInit(self):
        logger.debug(self.image_path)
        items=[]
        self.getControl(IMAGE).setImage(self.image_path, False)
        self.getControl(TITLE).setLabel(self.goal)

        for x in range(self.num_tiles):
            item = xbmcgui.ListItem(str(x))
            item.setProperty('selected', 'false')
            items.append(item)
        self.getControl(PANEL).reset()
        self.getControl(PANEL).addItems(items)

class MultiCaptchaKodi(SolverKodi):
    """
    multicaptcha challenges present you with one large image split into a grid of tiles and ask you to select the tiles that contain a given object.
    Occasionally, the image will not contain the object, but rather something that looks similar.
    It is possible to select no tiles in this case, but reCAPTCHA may have been fooled by the similar-looking object and would reject a selection of no tiles.
    """
    def run(self) -> Solution:
        result = self.solver.first_challenge()
        while not isinstance(result, Solution):
            if not isinstance(result, ImageGridChallenge):
                raise TypeError("Unexpected type: {}".format(type(result)))
            indices = self.handle_challenge(result)
            result = self.solver.select_indices(indices)
        return result

    def handle_challenge(self, challenge: ImageGridChallenge):
        goal = challenge.goal.plain
        self.num_rows = challenge.dimensions.rows
        self.num_columns = challenge.dimensions.columns
        logger.debug('RIGHE',self.num_rows, 'COLONNE',self.num_columns)

        self.num_tiles = challenge.dimensions.count
        image = challenge.image
        self.show_image(image, goal)
        if self.closed:
            return False
        return self.result

    def onClick(self, control):
        if control == CANCEL:
            self.closed = True
            self.close()

        elif control == RELOAD:
            self.result = None
            self.close()

        elif control == OK:
            self.result = [int(k) for k in range(9) if self.indices.get(k, False)]
            self.close()
        else:
            item = self.getControl(PANEL)
            index = item.getSelectedPosition()
            selected = True if item.getSelectedItem().getProperty('selected') == 'false' else False
            item.getSelectedItem().setProperty('selected', str(selected).lower())
            self.indices[index] = selected


class DynamicKodi(SolverKodi):
    """
    dynamic challenges present you with a grid of different images and ask you to select the images that match the given description.
    Each time you click an image, a new one takes its place. Usually, three images from the initial set match the description,
    and at least one of the replacement images does as well.
    """
    def run(self):
        challenge = self.solver.get_challenge()
        image = challenge.image
        goal = challenge.goal.raw
        self.num_rows = challenge.dimensions.rows
        self.num_columns = challenge.dimensions.columns
        self.num_tiles = challenge.dimensions.count
        logger.debug('RIGHE',self.num_rows, 'COLONNE',self.num_columns)

        self.show_image(image, goal)
        if self.closed:
            return False
        return self.result

    def changeTile(self, path, index, delay):
        time.sleep(delay)
        self.getControl(PANEL).getListItem(index).setArt({'image', path})
        # tile = self.getControl(10005 + index)
        # self.addControl(xbmcgui.ControlImage(tile.getX(), tile.getY(), tile.getWidth(), tile.getHeigh(), path))

    def onClick(self, control):
        if control == CLOSE:
            self.closed = True
            self.close()

        elif control == RELOAD:
            self.result = None
            self.close()

        elif control == OK:
            self.result = self.solver.finish()
            self.close()
        else:
            item = self.getControl(PANEL)
            index = item.getSelectedPosition()
            selected = True if item.getSelectedItem().getProperty('selected') == 'false' else False
            item.getSelectedItem().setProperty('selected', str(selected).lower())
            self.indices[index] = selected

            tile = self.solver.select_tile(index)
            path = config.get_temp_file(str(random.randint(1, 1000)) + '.png')
            filetools.write(path, tile.image)
            Thread(target=self.changeTile, args=(path, index, tile.delay)).start()
