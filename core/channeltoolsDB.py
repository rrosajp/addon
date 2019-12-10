import _sqlite3 as sql
import os

# from platformcode import config
from platformcode import config, logger

db = os.path.join(config.get_runtime_path(), 'kod_db.sqlite')
# db = '/home/casa/.kodi/userdata/addon_data/plugin.video.kod/kod_db.sqlite'
conn = sql.connect(db)
conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
cur = conn.cursor()
baseQuery = "select channels.*,(select group_concat(category) from categories WHERE categories.channel=id) as 'categories', (select group_concat(language) from languages WHERE languages.channel=id) as 'language' from channels "
thumb_path = 'https://raw.githubusercontent.com/kodiondemand/media/master/'


def filter(category, language='all', adult=False):
    cur.execute(baseQuery + "join categories on channels.id=categories.channel where category=? and adult=? and active=1", (category,adult))
    ris = []
    for channel in cur.fetchall():
        el = {}
        for col in channel.keys():
            if channel[col] and col in ['categories', 'language']:
                el[col] = channel[col].split(',')
            elif col == 'thumbnail':  # remote thumbnail
                el[col] = os.path.join(thumb_path, 'resources', "thumb", channel[col])
            elif channel[col]:
                el[col] = channel[col]
            else:
                el[col] = ''
        ris.append(el)
    # ris = [{channel[col].split(',') if col in ['category', 'language'] else channel[col]} for col in channel.keys() for channel in cur.fetchall()]
    logger.info(ris)

    return ris

def get_channel_parameters(channel_id):
    cur.execute('select * from channels where id=?', (channel_id,))
    ris = cur.fetchall()[0]
    ris["channel"] = ris["id"]
    ris["title"] = ris["name"]
    ris["fanart"] = ''
    ris["compatible"] = True
    cur.execute('select category from categories where channel=?', (channel_id,))
    ris["categories"] = [cat["category"] for cat in cur.fetchall()]
    cur.execute('select language from languages where channel=?', (channel_id,))
    ris["language"] = [lang["language"] for lang in cur.fetchall()]
    ris["has_settings"] = False

    return ris


def create_db():
    import json
    cur.execute('delete from channels')
    for f in os.walk('../channels/'):
        for file in f[2]:
            if file.split('.')[-1] == 'json':
                j = json.load(open(os.path.join(f[0], file)))
                id = j.get('id', '')
                name = j.get('name', '')
                active = j.get('active', False)
                adult = j.get('adult', False)
                thumbnail = j.get('thumbnail', '')
                banner = j.get('banner', '')
                cur.execute('insert into channels values (?,?,?,?,?,?,?,?)', (id, name, active, adult, thumbnail, banner, '', ''))
                for cat in j.get('categories', ''):
                    cur.execute('insert into categories values(?,?)', (id, cat))
                for cat in j.get('language', 'all'):
                    cur.execute('insert into languages values(?,?)', (id, cat))
    conn.commit()

# print get_channel_parameters('altadefinizione01')
# print create_db()