import argparse
from wp.wallpaper import WallPaperClient


def run(*passed_args):
    parser = get_parser()
    args = vars(parser.parse_args(*passed_args))

    if args['cache'] == 'refresh':
        WallPaperClient.init_wallpaper_url()

    WallPaperClient.set_wallpaper(args=args)


def get_parser():
    parser = argparse.ArgumentParser(description='set wallpaper for your os')
    parser.add_argument("-d", "--display", type=int, default=0,
                        help="Desktop display number on OS X (0: all displays, 1: main display, etc")
    parser.add_argument('-u', '--url',
                        type=str,
                        help="set wallpaper by web url")
    parser.add_argument('-c', '--cache',
                        type=str,
                        choices=['refresh'],
                        help="refresh random  web url from https://wallpapercave.com, tips: It is very time consuming!")
    return parser


if __name__ == '__main__':
    run()
