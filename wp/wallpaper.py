#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import asyncio
import platform
import subprocess

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

from lxml import etree
import ctypes
from urllib import parse, request
from aiofile import AIOFile
import aiohttp
import async_timeout
from wp.log import logger
from wp.conf import get_random_wallpaper_url, get_random_image_path

WALLPAPERCAVE_CATEGORY_URL = 'https://wallpapercave.com/categories'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')


def detect_desktop_environment():
    """Get current Desktop Environment
       http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
    :return: environment
    """
    environment = {}
    if os.environ.get("KDE_FULL_SESSION") == "true":
        environment["name"] = "kde"
        environment["command"] = """
                    qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
                        var allDesktops = desktops();
                        print (allDesktops);
                        for (i=0;i<allDesktops.length;i++) {{
                            d = allDesktops[i];
                            d.wallpaperPlugin = "org.kde.image";
                            d.currentConfigGroup = Array("Wallpaper",
                                                   "org.kde.image",
                                                   "General");
                            d.writeConfig("Image", "file:///{image_path}")
                        }}
                    '
                """
    elif os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        environment["name"] = "gnome"
        environment["command"] = "gsettings set org.gnome.desktop.background picture-uri file://{image_path}"
    elif os.environ.get("DESKTOP_SESSION") == "Lubuntu":
        environment["name"] = "lubuntu"
        environment["command"] = "pcmanfm -w {image_path} --wallpaper-mode=fit"
    elif os.environ.get("DESKTOP_SESSION") == "mate":
        environment["name"] = "mate"
        environment["command"] = "gsettings set org.mate.background picture-filename {image_path}"
    else:
        try:
            info = subprocess.getoutput("xprop -root _DT_SAVE_MODE")
            if ' = "xfce4"' in info:
                environment["name"] = "xfce"
        except (OSError, RuntimeError):
            environment = None
            pass
    return environment


class WallPaperClient(object):
    """
    set wallpaper client
    """

    @staticmethod
    def add_image(urls: list = None):
        loop = asyncio.get_event_loop()
        if urls is None:
            loop.run_until_complete(WallPaperClient.download_image(loop=loop))
        loop.run_until_complete(WallPaperClient.download_image(urls=urls, loop=loop))

    @staticmethod
    def set_wallpaper(args=None):
        web_url = args['url']
        if web_url is not None:
            # TODO: 那么就是本地的url
            base_name = os.path.basename(web_url)
            WallPaperClient.add_image(urls=[web_url])
            image_path = os.path.join(IMAGE_DIR, base_name)
        else:
            web_url = get_random_wallpaper_url()
            WallPaperClient.add_image(urls=web_url)
            web_url = web_url[0]
            image_path = os.path.join(IMAGE_DIR, os.path.basename(web_url))
        print("Your wallpaper from :", web_url)
        print("Your wallpaper local path at : :", image_path)
        platform_name = platform.system()

        # Windows
        if platform_name.startswith("Win"):
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

        # OS X/macOS
        if platform_name.startswith("Darwin"):
            if args['display'] == 0:
                command = """
                        osascript -e 'tell application "System Events"
                            set desktopCount to count of desktops
                            repeat with desktopNumber from 1 to desktopCount
                                tell desktop desktopNumber
                                    set picture to "{image_path}"
                                end tell
                            end repeat
                        end tell'
                          """.format(image_path=image_path)
            else:
                command = """osascript -e 'tell application "System Events"
                                set desktopCount to count of desktops
                                tell desktop {display}
                                    set picture to "{image_path}"
                                end tell
                            end tell'""".format(display=args['display'],
                                                image_path=image_path)
            os.system(command)
        if platform_name.startswith("Lin"):

            # Check desktop environments for linux
            desktop_environment = detect_desktop_environment()
            if desktop_environment and desktop_environment["name"] in supported_linux_desktop_envs:
                os.system(desktop_environment["command"].format(image_path=image_path))
            else:
                print("Unsupported desktop environment")

    @staticmethod
    async def download_image(loop, urls=get_random_wallpaper_url()):
        async with aiohttp.ClientSession(loop=loop) as session:
            for url in list(urls):
                await WallPaperSpider.download_resources(session, url)


class WallPaperSpider(object):

    def __init__(self, request_session=None):
        self.request_session = request_session
        self.categories = {}
        self.wallpaper = []
        self.retry_times = 2

    def get_session(self):
        if self.request_session is None:
            self.request_session = aiohttp.ClientSession()
        return self.request_session

    async def fetch(self, session, url):
        body = None
        with async_timeout.timeout(10):
            try:
                async with session.get(url=url) as resp:
                    if resp.status in [200, 201]:
                        body = await resp.text()

            except Exception as e:
                logger.error("ERROR request: {} and info:{}".format(url, e))
                body = None

            if self.retry_times > 0 and body is None:
                self.retry_times -= 1
                logger.info("wallpaper spider retry 3 times, and this is {} time".format(self.retry_times))
                return await self.fetch(session, url)

            return body

    @staticmethod
    async def download_resources(session, url):
        with async_timeout.timeout(20):
            async with session.get(url) as resp:
                filename = os.path.join(IMAGE_DIR, os.path.basename(url))
                with open(filename, 'wb+') as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                return await resp.release()

    def init_categories(self):
        loop = asyncio.get_event_loop()
        category_list = self.etree(request.urlopen(WALLPAPERCAVE_CATEGORY_URL).read()).xpath('//*[@id="catsinbox"]/li')

        for i in category_list:
            self.categories.update(
                {os.path.basename(i.xpath('a/@href')[0]): parse.urljoin(WALLPAPERCAVE_CATEGORY_URL,
                                                                        i.xpath('a/@href')[0])})
        tmp = {}
        for i in self.categories.values():
            tmp.update(
                {os.path.basename(i): self.etree(request.urlopen(i).read()).xpath('//*[@class="albumphoto"]/@href')})
        loop.run_until_complete(
            asyncio.gather(
                *(self.nth2_categories(session=self.get_session(), url=url) for url in
                  [i for k in tmp.values() for i in k]))
        )

    async def nth2_categories(self, session, url):
        res = await self.fetch(session, parse.urljoin(WALLPAPERCAVE_CATEGORY_URL, url))
        if res is not None:
            self.wallpaper.extend([parse.urljoin(WALLPAPERCAVE_CATEGORY_URL, i) for i in
                                   self.etree(res).xpath('//*[@class="wallpaper"]/a/img/@src')])
            for i in self.etree(res).xpath('//*[@class="wallpaper"]/a/img/@src'):
                await self.aio_write(filename='wallpaper.json', text=parse.urljoin(WALLPAPERCAVE_CATEGORY_URL, i))

    async def aio_write(self, filename, text):
        async with AIOFile(filename, 'a+') as afp:
            await afp.write(text + '\001')

    def etree(self, body):
        if body is not None:
            return etree.HTML(body)
