import argparse
from wp.wallpaper import WallPaperClient


def run(*passed_args):
    parser = get_parser()
    args = vars(parser.parse_args(*passed_args))
    WallPaperClient.set_wallpaper(args=args)


def get_parser():
    parser = argparse.ArgumentParser(description='Random wallpaper for your os')
    parser.add_argument("-d", "--display", type=int, default=0,
                        help="Desktop display number on OS X (0: all displays, 1: main display, etc")
    parser.add_argument('-u', '--url',
                        type=str,
                        help="set wallpaper by web url")
    return parser


if __name__ == '__main__':
    run()
