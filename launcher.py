from __future__ import annotations

import logging
import asyncio
import contextlib
import asqlite
import discord
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
        async with QillBot() as bot:
            bot.conn = conn
            await bot.start()
    except Exception as e:
        print(e)
            

def main():
    with setup_logging():
        asyncio.run(run_bot())



if __name__ == '__main__':
    main()