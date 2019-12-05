# uncompyle6 version 3.4.0
# Python bytecode 2.7
# Decompiled from: Python 2.7.16 (default, Jul  9 2019, 16:43:02)
# [GCC 8.3.0]
# Embedded file name: <string>
"""
Realiza funciones de ocultaci\xc3\xb3n de la url de las web de destino listadas, para bordear los bloqueos judiciales o de las operadoras.  Se pretende que este proceso sea lo m\xc3\xa1s autom\xc3\xa1tico y transparente para los canales en lo posible.

Existen dos tipos de proxies gratuitos:
-       Proxy Web
-       Proxy \xe2\x80\x9cdirecto\xe2\x80\x9d.  Dentro de este grupo hay direcciones que soportar CloudFlare.

En el Proxy Web, se llama a una web Proxy donde se le pasa como Post la url de la web de destino, as\xc3\xad como los par\xc3\xa1metros que indican que NO encripte la url o los datos, y que s\xc3\xad use cookies.

En los datos de respuesta hay que suprimir de las urls una cabecera y una cola, que var\xc3\xadan seg\xc3\xban la web Proxy.  El resultado es una p\xc3\xa1gina bastante parecida a la que se obtendr\xc3\xada sin usar el proxy, aunque en el canal que lo use se debe verificar que las expresiones regex funcionan sin problemas.

El Proxy Web parece m\xc3\xa1s estable y r\xc3\xa1pido, pero tiene el inconveniente que no se vale webs que usen Cloudflare.

Se ha creado un Diccionario con las entradas verificadas de Proxy Webs.  En esas entradas se encuentran los par\xc3\xa1metros necesarios para enviar la url de la web de destino, as\xc3\xad como para convertir los datos de retorno a algo transparente para el canal.  Habr\xc3\xa1 que ir a\xc3\xb1adiendo y borrando Webs Proxy seg\xc3\xban su rendimiento y estabilidad.

El Proxy \xe2\x80\x9cdirecto\xe2\x80\x9d, es totalmente transparente para el canal, permitiendo usar Post, y en algunos casos llamadas a webs que usan Cloudflare.  El problema que tienen estos Proxies es su extremada volatilidad en la disponibilidad y tiempo de respuesta.

Se ha confeccionado una lista inicial de Proxies directos y otra de Proxies CloudFlare, principalmente de Singapur y Hong Kong, que han sido probados y que suelen funcionar con regularidad.  A esta lista inicial se a\xc3\xb1aden din\xc3\xa1micamente otros de web(s) que listan estos proxy gratuitos, con algunos criterios de b\xc3\xbasqueda exigentes de disponibilidad y tiempo de respuesta.

Se ha optado por usar por defecto los Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d, dejando los Proxy Webs como alternativa autom\xc3\xa1tica para el caso de indisponibilidad de Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d.

Desde cualquier Canal se pueden hacer llamadas a Httptools para que sean filtradas por alg\xc3\xban tipo de Proxy.  Las llamadas deben incluir los par\xc3\xa1metros "proxy=True o proxy_web=True" y "forced_proxy=Total|ProxyDirect|ProxyCF|ProxyWeb".  Con la opci\xc3\xb3n "Total" asumir\xc3\xa1 "ProxyDirect" para "proxy=True"

TABLAS:
Como va a ser un m\xc3\xb3dulo de mucho uso, se ha organizado con tablas en memoria en vez de en archivos .json, para minimizar el impacto en el rendimiento.  Por otra parte, es recomendable que este .py (y por tanto sus tablas) est\xc3\xa9 \xe2\x80\x9cencoded\xe2\x80\x9d o mejor encriptado para evitar que las acciones y direcciones que aqu\xc3\xad se describen sean f\xc3\xa1cilmente neutralizables.

-       l111ll = lista de webs bloqueadas a ser tratadas por Proxytools.  Tiene lista de bloqueos geogr\xc3\xa1fica.
-       l1l1ll = lista de Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d iniciales, verificados tanto para http como para https
-   l111l1 = lista de Proxies \xe2\x80\x9cdirectos CloodFlare\xe2\x80\x9d iniciales, verificados
-       ll11ll = lista de Proxy Webs, con sus par\xc3\xa1metros de uso
-       l11111 = lista de webs bloqueadas donde se dice con qu\xc3\xa9 tipo de proxy especifico se quiere tratar.  Si la web bloqueada no est\xc3\xa1 en esta lista, se trata con los proxies por defecto.

M\xc3\x89TODOS:
-       get_proxy_list_monitor: es un SERVICIO que se lanza al inicio de Alfa. Si en los settings se ha especificado que el uso de "Acceso Alternativo a la Web" est\xc3\xa1 desactivado, se activa el "Modo Demanda" usando las direciones de Proxies por defecto.  Si est\xc3\xa1 activo, se asume el "Modo Forzado" y se ejecutar\xc3\xa1 peri\xc3\xb3dicamente (cada 12 horas), siempre que no haya reporducciones activas.  Este servicio realiza las siguiente funciones:
        o       Identifica el pa\xc3\xads del usuario y activa/desactiva el proxy en cada web bloquedad seg\xc3\xban la lista paises bloqueados
        o       Aleatoriza las listas iniciales de direcciones proxy
    o   Si no hay bloqueos en la zona geogr\xc3\xa1fica del usuario, abandona
-   Si estamos en "Modo Forzado", llama al m\xc3\xa9todo get_proxy_list_method, que realiza estas tareas de inicilaizaci\xc3\xb3n de tablas:
        o       Carga la lista inicial de Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d y los aleatoriza
        o       De la web \xe2\x80\x9cHideMy.name\xe2\x80\x9d obtiene una lista adicional de Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d
        o       Usando la web bloqueada \xe2\x80\x9cmejortorrent.com\xe2\x80\x9d, se validan los Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d hasta que se encuentra uno que responde correctamente.  Este proxy encontrado pasa a ser el usado por defecto durante este periodo
    o   Similar a Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d, de la lista inicial se aleatoriza y se verifica uno que funcione
        o       Se valida la lista de Proxy Webs hasta que se encuentra una que responda correctamente.  Esta Proxy Web encontrada pasa a ser la usada por defecto durante este periodo. Es preferible utilizar "Hide.me" por su reputaci\xc3\xb3n y porque soporta bien las llamadas con POST desde el canal.  Si no estuviera disponoble, te tomar\xc3\xada otra, pero las llamadas con POST se realizar\xc3\xadan por "ProxyDirect"
        o       En la \xe2\x80\x9cwhitelist\xe2\x80\x9d se analiza si hay m\xc3\xa1s de una Proxy alternativo por web bloqueada.  Si es as\xc3\xad, se aleatorizan las entradas y se escoge una para este periodo
        o       Los datos de Proxy \xe2\x80\x9cdirecto\xe2\x80\x9d activo, lista de Proxies \xe2\x80\x9cdirectos\xe2\x80\x9d, nombre de Proxy Web activo,  y Proxy \xe2\x80\x9cwhitelist\xe2\x80\x9d en uso se guardan como par\xc3\xa1metros en \xe2\x80\x9csettings.xml, encoded Base64\xe2\x80\x9d, aunque est\xc3\xa1 preparado para encriptarlo con un nivel de seguridad m\xc3\xa1s alto.
-       randomize_lists: aleatoriza las listas iniciales de direcciones proxy
-       set_proxy_web: prepara los par\xc3\xa1metros para llamar a un Proxy Web
-       restore_after_proxy_web: retira los datos del Proxy Web de la respuesta, para hacerlo transparente al canal
-       channel_proxy_list: verifica si la web de la url est\xc3\xa1 bloqueada en esa geolocalizaci\xc3\xb3n
-       get_proxy_addr: pasa los datos del Proxy \xe2\x80\x9cdirecto\xe2\x80\x9d, Proxy \xe2\x80\x9cCloudFlare\xe2\x80\x9d y Proxy Web por defecto, modificados con los valores de la \xe2\x80\x9cwhitelist\xe2\x80\x9d, si los hay
-       encrypt_proxy: codifica en Base64 los datos pasados, con potencial para encriptaci\xc3\xb3n
-       decrypt_proxy: decodifica desde Base64 los datos pasados
"""
import urllib, base64, re, time, threading, traceback, ast, random, Queue
from platformcode import config, logger, platformtools
from platformcode.logger import WebErrorException
import scrapertools
debugging = False
l111ll = {'www.mejortorrent.com': 'ES,PO', 'www.mejortorrent.org': 'ES', 'www.mejortorrent.net': 'ES', 'gnula.nu': 'ES', 'gnula.se': 'ES', 'www.elitetorrent.biz': 'ES', 'mejortorrent1.net': 'ES'}
l1l1ll = [
 '68.183.183.44:1111', '119.28.31.29:8888', '157.230.45.121:1111', '128.199.152.169:31330', '90.145.221.186:80', '157.230.33.37:1111', '178.128.103.3:31330', '104.248.154.97:1111', '157.230.34.190:1111', '128.199.156.37:31330', '128.199.138.136:31330', '111.223.75.178:8080', '128.199.132.128:31330', '128.199.136.197:31330', '128.199.155.182:31330', '128.199.147.208:31330', '128.199.144.174:31330', '128.199.148.45:31330', '128.199.168.132:31330', '178.128.63.155:31330', '52.163.207.100:3128', '103.42.213.177:8080', '103.42.213.176:8080', '13.70.24.15:80', '150.109.55.190:83', '159.138.1.185:80', '218.102.119.7:8380', '218.102.119.7:8383', '218.102.119.7:8382', '47.90.50.17:80', '218.102.119.7:8385', '218.102.119.7:8197', '59.149.60.209:8380', '113.252.222.73:8380', '210.0.128.58:8080']
l111l1 = [
 '68.183.183.44:1111', '128.199.156.37:31330', '119.28.31.29:8888', '93.88.75.31:8080', '104.248.154.97:1111', '90.145.221.186:80', '157.230.34.190:1111', '128.199.132.128:31330', '128.199.138.136:31330', '128.199.136.197:31330', '128.199.144.174:31330', '128.199.148.45:31330', '128.199.155.182:31330', '128.199.204.6:31330', '13.229.66.154:80', '139.99.6.142:3128', '159.65.1.26:80', '52.163.207.100:3128', '54.254.198.71:80', '13.70.24.15:80']
ll11ll = {'hide.me': ('https://nl.hideproxy.me/includes/process.php?action=update', 'https://nl.hideproxy.me',
 '', '/go.php?u=', '&b=4|&amp;b=4', 'u=%s&proxy_formdata_server=nl&allowCookies=1&encodeURL=0'),
   'webproxy.to': ('http://webproxy.to/includes/process.php?action=update', 'http://webproxy.to', '',
 '/browse.php?u=', '&b=4|&amp;b=4', 'u=%s&encodeURL=0&encodePage=0&allowCookies=on&stripJS=0&stripObjects=0')}
ll1111 = 'hide.me'
l11111 = {'gnula.nu': 'ProxyCF', 'www.mejortorrent.com': 'ProxyWeb:hide.me', 'www.mejortorrent.org': 'ProxyWeb:hide.me,webproxy.to', 'mejortorrent1.net': 'ProxyWeb'}

def get_proxy_list():

    def get_proxy_list_monitor(test=False, debugging=debugging):
        import httptools, os
        alfa_s = True
        try:
            if not config.get_setting('proxy_addr'):
                if debugging:
                    logger.error('NO proxy_addr')
                randomize_lists()
        except:
            if debugging:
                logger.error('NO proxy_addr')
            randomize_lists()

        if os.path.exists(os.path.join(config.get_runtime_path(), 'channels', 'custom.py')):
            proxy_dev = 'dev'
            alfa_s = False
        else:
            proxy_dev = 'user'
            if debugging:
                alfa_s = False
        config.set_setting('proxy_dev', encrypt_proxy(proxy_dev))
        proxy_geoloc = 'https://geoip-db.com/json/'
        country_code = 'ES'
        proxy_channel_bloqued = l111ll.copy()
        try:
            data = ''
            data = httptools.downloadpage(proxy_geoloc, proxy=False, proxy_web=False, timeout=10, random_headers=True, alfa_s=alfa_s).data
            country_code = scrapertools.find_single_match(data, '"country_code":"([^"]+)"')
        except:
            logger.error(traceback.format_exc())
            country_code = 'ES'
        else:
            if proxy_dev == 'dev' or debugging:
                logger.info('Geoloc: ' + country_code + ' / ' + data)
            proxy_active = False
            for channel, countries in proxy_channel_bloqued.items():
                if country_code in countries or 'ALL' in countries:
                    proxy_channel_bloqued.update({channel: 'ON'})
                    proxy_active = True
                else:
                    proxy_channel_bloqued.update({channel: 'OFF'})

            if proxy_channel_bloqued:
                config.set_setting('proxy_channel_bloqued', encrypt_proxy(str(proxy_channel_bloqued)))
            else:
                config.set_setting('proxy_channel_bloqued', encrypt_proxy(''))
            if proxy_dev == 'dev' or debugging:
                logger.info('Alternative_web_access: ' + str(config.get_setting('alternative_web_access')) + ' / Proxy Activo: ' + str(proxy_active))
            if proxy_dev == 'dev' or debugging:
                logger_disp(debugging=debugging)
            if not proxy_active:
                randomize_lists()
                return
            if not config.get_setting('alternative_web_access'):
                randomize_lists()
                return

        if debugging:
            logger.info('Entrando en Monitor :' + str(config.get_setting('alternative_web_access')))
        if config.get_platform(True)['num_version'] >= 14:
            import xbmc
            monitor = xbmc.Monitor()
        else:
            get_proxy_list_method(test=test, debugging=debugging)
            return
        while not monitor.abortRequested():
            if not platformtools.is_playing():
                get_proxy_list_method(test=test, debugging=debugging)
            timer = 43200
            if monitor.waitForAbort(timer):
                break

    try:
        threading.Thread(target=get_proxy_list_monitor).start()
        time.sleep(5)
    except:
        logger.error(traceback.format_exc())


def randomize_lists():
    proxies = l1l1ll[:]
    random.shuffle(proxies)
    config.set_setting('proxy_addr', encrypt_proxy(str(proxies[0])))
    config.set_setting('proxy_list', encrypt_proxy(str(proxies)))
    proxies = l111l1[:]
    random.shuffle(proxies)
    config.set_setting('proxy_CF_addr', encrypt_proxy(str(proxies[0])))
    config.set_setting('proxy_CF_list', encrypt_proxy(str(proxies)))
    config.set_setting('proxy_web_name', encrypt_proxy('hide.me'))
    proxy_white_list = l11111.copy()
    proxy_table = []
    for label_a, value_a in proxy_white_list.items():
        proxy_t_s = ''
        proxy_t = proxy_white_list[label_a]
        if 'ProxyCF:' in proxy_t:
            proxy_t_s = 'ProxyCF:'
            proxy_t = proxy_t.replace('ProxyCF:', '')
        if 'ProxyWeb:' in proxy_t:
            proxy_t_s = 'ProxyWeb:'
            proxy_t = proxy_t.replace('ProxyWeb:', '')
        proxy_table = proxy_t.split(',')
        if len(proxy_table) > 1:
            random.shuffle(proxy_table)
        if proxy_t_s:
            proxy_table[0] = proxy_t_s + str(proxy_table[0])
        proxy_white_list.update({label_a: proxy_table[0]})

    config.set_setting('proxy_white_list', encrypt_proxy(str(proxy_white_list)))


def get_proxy_list_method(test=False, proxy_init='Total', debugging=debugging, lote_len=5):
    if debugging:
        logger.info('Test: ' + str(test) + ', Proxy_init: ' + str(proxy_init))
    import httptools
    alfa_s = True
    try:
        proxy_dev = decrypt_proxy(config.get_setting('proxy_dev'))
    except:
        proxy_dev = 'user'
        config.set_setting('proxy_dev', encrypt_proxy(proxy_dev))

    if proxy_dev == 'dev' or debugging:
        alfa_s = False
    proxies_save = []
    proxy_addr = ''
    proxy_list = []
    proxy_CF_addr = ''
    proxy_CF_list = []
    proxy_web_name = ''
    proxy_url_test = 'http://www.mejortorrent.com/torrents-de-peliculas.html'
    proxy_pattern_test = '<a href="((?:[^"]+)?/peli-descargar-torrent[^"]+)">?'
    proxy_CF_url_test = 'http://gnula.nu/peliculas-online/lista-de-peliculas-online-parte-1/'
    proxy_CF_pattern_test = '<a class="Ntooltip" href="([^"]+)">([^<]+)<span><br[^<]+<img src="([^"]+)"></span></a>(.*?)<br'
    randomize_lists()
    proxies = []
    proxies_str = decrypt_proxy(config.get_setting('proxy_list'))
    proxies = ast.literal_eval(proxies_str)
    proxies_init = proxies[:]
    if proxy_dev == 'dev' or debugging:
        logger.debug('Tabla inicial ProxyDirect: ' + str(proxies))
    if proxy_dev == 'dev' or debugging:
        logger.debug('Tabla inicial ProxyCF: ' + str(decrypt_proxy(config.get_setting('proxy_CF_list'))))
    country_list = [
     'SG', 'HK']
    for country in country_list:
        try:
            data = ''
            data = httptools.downloadpage('https://www.proxy-list.download/api/v1/get?type=https&anon=elite&country=%s' % country, proxy=False, proxy_web=False, proxy_retries=0, count_retries_tot=2, timeout=10, random_headers=True).data
            if data:
                data = re.sub('\\r|\\t|&nbsp;|<br>|\\s{2,}', '', data)
                data = "'" + re.sub('\\n', "', '", data)
                if data.endswith(", '"):
                    data = data[:-3]
                matches = []
                matches = ast.literal_eval(data)
                for var_a in matches:
                    proxy_a = var_a
                    if proxy_a not in proxies:
                        proxies.append(proxy_a)

        except:
            logger.error(traceback.format_exc())
        else:
            if proxy_dev == 'dev' or debugging:
                logger.debug('Tabla proxy-list.download ' + country + ': ' + str(matches))

    if test:
        try:
            data = ''
            data = httptools.downloadpage('https://hidemyna.me/en/proxy-list/?country=HKNLSG&maxtime=1000&type=s&anon=4#list', proxy=True, proxy_web=False, proxy_retries=1, count_retries_tot=2, timeout=10, random_headers=True, forced_proxy='ProxyCF').data
        except:
            logger.error(traceback.format_exc())

        if data:
            data = re.sub('\\n|\\r|\\t|&nbsp;|<br>|\\s{2,}', '', data)
            patron = '<td class=tdl>(.*?)<\\/td><td>(.*?)<\\/td>'
            matches = re.compile(patron, re.DOTALL).findall(data)
            for var_a, var_c in matches:
                proxy_a = '%s:%s' % (var_a, var_c)
                if proxy_a not in proxies:
                    proxies.append(proxy_a)

            if proxy_dev == 'dev' or debugging:
                logger.debug('Tabla HideMy.name: ' + str(matches))
    if proxy_dev == 'dev' or debugging:
        logger.debug('Tabla ANTES del testing: ' + str(proxies))
    if proxy_init == 'Total' or proxy_init == 'ProxyDirect':
        if proxy_dev == 'dev' or debugging:
            logger.debug('INIT ProxyDirect: ' + proxy_init)
        threads_list = []
        proxy_que = Queue.Queue()
        for proxy_lote in range(0, len(proxies), lote_len):
            if proxy_addr and not test:
                break
            for proxy_a in proxies[proxy_lote:proxy_lote + lote_len]:
                if proxy_a in proxy_list:
                    continue
                try:
                    proxy_thread = threading.Thread(target=test_proxy_addr, args=(proxy_a, proxy_url_test, proxy_pattern_test, True, False, 'ProxyDirect', 0, 1, 7, alfa_s, proxy_que, test, debugging))
                    proxy_thread.daemon = True
                    proxy_thread.start()
                    threads_list.append(proxy_thread)
                except:
                    logger.error(traceback.format_exc())

            while [ thread_x for thread_x in threads_list if thread_x.isAlive() ]:
                try:
                    proxy_addr = proxy_que.get(True, 1)
                    proxy_list.append(proxy_addr)
                    config.set_setting('proxy_addr', encrypt_proxy(str(proxy_addr)))
                    if not test:
                        proxy_list = proxies_init
                        break
                except Queue.Empty:
                    proxy_addr = ''

        if not proxy_addr and len(proxy_list) > 0:
            proxy_addr = proxy_list[(-1)]
        if not proxy_addr and proxy_init == 'Total':
            proxy_addr = l1l1ll[0]
        config.set_setting('proxy_addr', encrypt_proxy(str(proxy_addr)))
        config.set_setting('proxy_list', encrypt_proxy(str(proxy_list)))
        if proxy_dev == 'dev' or debugging:
            logger.info('ProxyDirect addr: ' + str(proxy_addr))
    if proxy_init == 'Total' or proxy_init == 'ProxyCF':
        if proxy_dev == 'dev' or debugging:
            logger.debug('INIT ProxyCF: ' + proxy_init)
        proxies_str = decrypt_proxy(config.get_setting('proxy_CF_list'))
        proxies_cf = ast.literal_eval(proxies_str)
        proxies_init = proxies_cf[:]
        if proxy_init == 'Total':
            proxies_cf.extend(proxies)
        else:
            proxies_cf.extend(ast.literal_eval(decrypt_proxy(config.get_setting('proxy_list'))))
        threads_list_CF = []
        proxy_que_CF = Queue.Queue()
        lote_len = 2
        for proxy_lote in range(0, len(proxies_cf), lote_len):
            if proxy_CF_addr and not test:
                break
            for proxy_a in proxies_cf[proxy_lote:proxy_lote + lote_len]:
                if proxy_a in proxy_CF_list:
                    continue
                try:
                    proxy_thread = threading.Thread(target=test_proxy_addr, args=(proxy_a, proxy_CF_url_test, proxy_CF_pattern_test, True, False, 'ProxyCF', 0, 1, 10, alfa_s, proxy_que_CF, test, debugging))
                    proxy_thread.daemon = True
                    proxy_thread.start()
                    threads_list_CF.append(proxy_thread)
                except:
                    logger.error(traceback.format_exc())

            while [ thread_x for thread_x in threads_list_CF if thread_x.isAlive() ]:
                try:
                    proxy_CF_addr = proxy_que_CF.get(True, 1)
                    proxy_CF_list.append(proxy_CF_addr)
                    config.set_setting('proxy_CF_addr', encrypt_proxy(str(proxy_CF_addr)))
                    if not test:
                        proxy_CF_list = proxies_init
                        break
                except Queue.Empty:
                    proxy_CF_addr = ''

        if not proxy_CF_addr and len(proxy_CF_list) > 0:
            proxy_CF_addr = proxy_CF_list[(-1)]
        if not proxy_CF_addr:
            proxy_CF_addr = l111l1[0]
        config.set_setting('proxy_CF_addr', encrypt_proxy(str(proxy_CF_addr)))
        config.set_setting('proxy_CF_list', encrypt_proxy(str(proxy_CF_list)))
        if proxy_dev == 'dev' or debugging:
            logger.info('ProxyCF addr: ' + str(proxy_CF_addr))
    proxy_table = []
    if proxy_init == 'Total' or proxy_init == 'ProxyWeb':
        if proxy_dev == 'dev' or debugging:
            logger.debug('INIT ProxyWeb: ' + proxy_init)
        for label_a, value_a in ll11ll.items():
            proxy_table.append(label_a)

        proxy_table = sorted(proxy_table)
        for label_a in proxy_table:
            proxy_web_name = label_a
            config.set_setting('proxy_web_name', encrypt_proxy(str(proxy_web_name)))
            try:
                data = ''
                data = httptools.downloadpage(proxy_url_test, proxy=False, proxy_web=True, forced_proxy='ProxyWeb', proxy_retries=0, count_retries_tot=1, timeout=10, alfa_s=alfa_s).data
            except:
                logger.error(traceback.format_exc())
                proxy_web_name = ''
                continue
            else:
                if data:
                    data = re.sub('\\n|\\r|\\t|&nbsp;|<br>|\\s{2,}', '', data)
                    data_test = scrapertools.find_single_match(data, proxy_pattern_test)
                    if not data_test:
                        if proxy_dev == 'dev' or debugging:
                            logger.error('ProxyWeb error: ' + proxy_web_name)
                        proxy_web_name = ''
                        continue
                    elif not test:
                        break
                else:
                    proxy_web_name = ''

        if not proxy_web_name and proxy_init == 'Total':
            config.set_setting('proxy_web_name', encrypt_proxy('hide.me'))
        elif not proxy_web_name and proxy_init != 'Total':
            config.set_setting('proxy_web_name', encrypt_proxy(''))
    logger_disp(debugging=debugging)


def test_proxy_addr(proxy_addr, proxy_url_test, proxy_pattern_test, proxy, proxy_web, forced_proxy, proxy_retries, count_retries_tot, timeout, alfa_s, proxy_que, test, debugging):
    import httptools
    header = scrapertools.find_single_match(proxy_url_test, '(http.*):\\/\\/')
    if not header:
        header = 'http'
    proxy_a = {header: proxy_addr}
    try:
        data = ''
        data = httptools.downloadpage(proxy_url_test, proxy=proxy, proxy_web=proxy_web, forced_proxy=forced_proxy, proxy_addr_forced=proxy_a, proxy_retries=proxy_retries, count_retries_tot=count_retries_tot, timeout=timeout, alfa_s=alfa_s).data
    except:
        logger.error(traceback.format_exc())
        return ''

    if data:
        if proxy_pattern_test:
            data = re.sub('\\n|\\r|\\t|&nbsp;|<br>|\\s{2,}', '', data)
            data_test = scrapertools.find_single_match(data, proxy_pattern_test)
            if data_test:
                if isinstance(proxy_que, Queue.Queue):
                    proxy_que.put(proxy_addr)
            else:
                proxy_addr = ''
        elif isinstance(proxy_que, Queue.Queue):
            proxy_que.put(proxy_addr)
    else:
        proxy_addr = ''
    return proxy_addr


def logger_disp(debugging=debugging):
    proxy_dev = decrypt_proxy(config.get_setting('proxy_dev'))
    proxy_channel_bloqued_str = decrypt_proxy(config.get_setting('proxy_channel_bloqued'))
    proxy_addr = decrypt_proxy(config.get_setting('proxy_addr'))
    proxy_list = decrypt_proxy(config.get_setting('proxy_list'))
    proxy_CF_addr = decrypt_proxy(config.get_setting('proxy_CF_addr'))
    proxy_CF_list = decrypt_proxy(config.get_setting('proxy_CF_list'))
    proxy_web_name = decrypt_proxy(config.get_setting('proxy_web_name'))
    if proxy_dev == 'dev' or debugging:
        logger.info('PROXY Lists: ProxyDirect: ' + str(proxy_addr) + ' / ProxyDirect Pool: ' + str(proxy_list) + ' / ProxyCF: ' + str(proxy_CF_addr) + ' / ProxyCF Pool: ' + str(proxy_CF_list) + ' / ProxyWeb: ' + str(proxy_web_name) + ' / Proxy Whitelist: ' + str(decrypt_proxy(config.get_setting('proxy_white_list'))) + ' / Bloqued Channels: ' + str(proxy_channel_bloqued_str))
    else:
        logger.debug(str(encrypt_proxy('PROXY Lists: ProxyDirect: ' + str(proxy_addr) + ' / ProxyDirect Pool: ' + str(proxy_list) + ' / ProxyCF: ' + str(proxy_CF_addr) + ' / ProxyCF Pool: ' + str(proxy_CF_list) + ' / ProxyWeb: ' + str(proxy_web_name) + ' / Proxy Whitelist: ' + str(decrypt_proxy(config.get_setting('proxy_white_list'))) + ' / Bloqued Channels: ' + str(proxy_channel_bloqued_str))))


def set_proxy_web(url, proxy_web_name, post=None):
    proxy_site_url_post = ll11ll[proxy_web_name][0]
    proxy_site_url_get = ll11ll[proxy_web_name][1] + ll11ll[proxy_web_name][3]
    proxy_site_referer = ll11ll[proxy_web_name][2]
    proxy_site_header = ll11ll[proxy_web_name][3]
    proxy_site_tail = ll11ll[proxy_web_name][4]
    proxy_site_post = ll11ll[proxy_web_name][5]
    if debugging:
        logger.info('PROXY POST: ' + proxy_site_url_post + ' / GET: ' + proxy_site_url_get)
    if post and proxy_web_name != ll1111:
        proxy_web_name = ''
    headers = ''
    if proxy_web_name:
        url = urllib.quote_plus(url)
        if post:
            tail = proxy_site_tail.split('|')
            url = proxy_site_url_get + url + tail[0]
        else:
            post = proxy_site_post % url
            post = post.replace('[', '%5B').replace(']', '%5D')
            url = proxy_site_url_post
        if proxy_site_referer:
            headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Referer': proxy_site_referer}
    if debugging:
        logger.debug(url + ' / ' + post + ' / ' + headers + ' / ' + proxy_web_name)
    return (
     url, post, headers, proxy_web_name)


def restore_after_proxy_web(data, proxy_web_name, url):
    proxy_site_header = ll11ll[proxy_web_name][3]
    proxy_site_tail = ll11ll[proxy_web_name][4]
    if 'Hotlinking directly to proxied pages is not permitted.' in data:
        data = 'ERROR'
        return data
    if not scrapertools.find_single_match(data, '^d\\d+:.*?\\d+:') and not data.startswith('PK'):
        data = urllib.unquote(data)
        proxy_site_table = []
        proxy_site_table = proxy_site_header.split('|')
        for proxy_header in proxy_site_table:
            data = data.replace(proxy_header, '')

        proxy_site_table = []
        proxy_site_table = proxy_site_tail.split('|')
        for proxy_tail in proxy_site_table:
            data = data.replace(proxy_tail, '')

        data = data.replace('href="%smagnet:?' % url, 'href="magnet:?')
        data = data.replace("href='%smagnet:?" % url, "href='magnet:?")
    return data


def channel_proxy_list(url, forced_proxy=None):
    proxy_channel_bloqued_str = decrypt_proxy(config.get_setting('proxy_channel_bloqued'))
    proxy_channel_bloqued = dict()
    if proxy_channel_bloqued_str:
        proxy_channel_bloqued = ast.literal_eval(proxy_channel_bloqued_str)
    if not url.endswith('/'):
        url += '/'
    if scrapertools.find_single_match(url, '(?:http.*:\\/\\/)?([^\\?|\\/]+)(?:\\?|\\/)') in proxy_channel_bloqued:
        if forced_proxy:
            return True
        if 'ON' in proxy_channel_bloqued[scrapertools.find_single_match(url, '(?:http.*:\\/\\/)?([^\\?|\\/]+)(?:\\?|\\/)')]:
            if debugging:
                logger.debug(scrapertools.find_single_match(url, '(?:http.*:\\/\\/)?([^\\?|\\/]+)(?:\\?|\\/)'))
            return True
    return False


def get_proxy_addr(url, post=None, forced_proxy=None):
    proxy_a = ''
    proxy_CF_a = ''
    proxy_white_list_str = ''
    proxy_w = False
    proxy_log = ''
    header = 'http'
    domain = ''
    url_f = url
    proxy_a = decrypt_proxy(config.get_setting('proxy_addr'))
    proxy_CF_a = decrypt_proxy(config.get_setting('proxy_CF_addr'))
    proxy_white_list_str = decrypt_proxy(config.get_setting('proxy_white_list'))
    proxy_web_name = decrypt_proxy(config.get_setting('proxy_web_name'))
    proxy_dev = decrypt_proxy(config.get_setting('proxy_dev'))
    header = scrapertools.find_single_match(url_f, '(http.*):\\/\\/')
    if not url_f.endswith('/'):
        url_f += '/'
    domain = scrapertools.find_single_match(url_f, '(?:http.*:\\/\\/)?([^\\?|\\/]+)(?:\\?|\\/)')
    if domain and proxy_white_list_str and not forced_proxy:
        if domain in proxy_white_list_str:
            proxy_w = True
            proxy_white_list = dict()
            proxy_white_list = ast.literal_eval(proxy_white_list_str)
            if 'ProxyWeb' in proxy_white_list[domain]:
                proxy_a = ''
                proxy_CF_a = ''
                if ':' in proxy_white_list[domain]:
                    proxy_web_name = proxy_white_list[domain].replace('ProxyWeb:', '')
            elif 'ProxyCF' in proxy_white_list[domain]:
                proxy_a = ''
                proxy_web_name = ''
                if ':' in proxy_white_list[domain]:
                    proxy_CF_a = proxy_white_list[domain].replace('ProxyCF:', '')
            else:
                proxy_a = proxy_white_list[domain]
                proxy_CF_a = ''
                proxy_web_name = ''
    if forced_proxy:
        if forced_proxy == 'Total':
            pass
        elif forced_proxy == 'ProxyCF':
            proxy_a = ''
            proxy_web_name = ''
        elif forced_proxy == 'ProxyWeb':
            proxy_a = ''
            proxy_CF_a = ''
        else:
            proxy_CF_a = ''
            proxy_web_name = ''
    elif not proxy_w:
        proxy_CF_a = ''
        proxy_web_name = ''
    if proxy_web_name:
        proxy_log = url
    if proxy_a:
        proxy_log = proxy_a
        proxy_a = {header: proxy_a}
    if proxy_CF_a:
        proxy_log = proxy_CF_a
        proxy_CF_a = {header: proxy_CF_a}
    if not proxy_a and not proxy_CF_a and not proxy_web_name:
        proxy_CF_a = decrypt_proxy(config.get_setting('proxy_CF_addr'))
        proxy_a = ''
        proxy_web_name = ''
        if proxy_CF_a:
            proxy_log = proxy_CF_a
            proxy_CF_a = {header: proxy_CF_a}
        else:
            proxy_CF_a = ''
    if proxy_dev != 'dev':
        proxy_log = ''
    if debugging:
        logger.debug('Proxy: ' + str(proxy_a) + ' / Proxy CF: ' + str(proxy_CF_a) + ' / ProxyWeb: ' + str(proxy_web_name) + ' / ProxyLog: ' + str(proxy_log))
    return (
     proxy_a, proxy_CF_a, proxy_web_name, proxy_log)


def encrypt_proxy(data):
    if debugging:
        logger.debug(data)
    if data:
        data = base64.b64encode(data.encode('utf-8'))
    if debugging:
        logger.debug(data)
    return data


def decrypt_proxy(data):
    if debugging:
        logger.debug(data)
    if data:
        data = base64.b64decode(data).decode('utf-8')
    if debugging:
        logger.debug(data)
    return data


l1 = [[], [99, 71, 120, 49, 90, 50, 108, 117, 76, 110, 90, 112, 90, 71, 86, 118, 76, 109, 70, 115, 90, 109, 69, 61]]