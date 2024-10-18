from __future__ import annotations

import xml.etree.ElementTree as ET
import logging
import asyncio
import contextlib
import asqlite
import discord
from config import JMdict_e
from main import QillBot

from logging.handlers import RotatingFileHandler


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(filename='qill.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)

def parse_jmdict(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    dictionary = {}

    for entry in root.findall('entry'):
        kanji_entries = entry.findall('k_ele/keb')
        readings = entry.findall('r_ele/reb')
        senses = entry.findall('sense')

        for kanji in kanji_entries:
            kanji_text = kanji.text
            if kanji_text:  
                if kanji_text not in dictionary:
                    dictionary[kanji_text] = {
                        'readings': [],
                        'senses': []
                    }
                for reading in readings:
                    if reading.text:
                        dictionary[kanji_text]['readings'].append(reading.text)
                for sense in senses:
                    sense_info = {
                        'pos': [pos.text for pos in sense.findall('pos')],
                        'glosses': [gloss.text for gloss in sense.findall('gloss') if gloss.text]
                    }
                    dictionary[kanji_text]['senses'].append(sense_info)
    return dictionary


async def run_bot():
    try:
        conn = await asqlite.connect('qill.db')
        cursor = await conn.cursor()
        with open('schema.sql', 'r') as file:
                query = file.read()
                queries = query.split('\n\n')

        for query in queries:
            await cursor.execute(query)
            await conn.commit()
        await cursor.close()
        jmdict = parse_jmdict(JMdict_e)
        print("loaded jmdict")
        async with QillBot() as bot:
            bot.jmdict = jmdict
            bot.conn = conn
            await bot.start()
    except Exception as e:
        print(e)
            

def main():
    with setup_logging():
        asyncio.run(run_bot())



if __name__ == '__main__':
    main()