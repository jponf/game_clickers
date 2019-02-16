# -*- coding: utf-8 -*-

import argparse
import sys
import time

import cv2
import imutils
import mss
import numpy as np
import pynput
from PIL import Image

try:
    from PIL import ImageGrab
except ImportError:
    import pyscreenshot as ImageGrab


# Constants
################################################################################

KEYS = {"a": frozenset([65, 97]),
        "d": frozenset([68, 100]),
        "h": frozenset([72, 104]),
        "i": frozenset([73, 105]),
        "j": frozenset([74, 106]),
        "k": frozenset([75, 107]),
        "l": frozenset([76, 108]),
        "o": frozenset([79, 111]),
        "q": frozenset([81, 113]),
        "s": frozenset([83, 115]),
        "u": frozenset([85, 117]),
        "w": frozenset([87, 119])}

# Playground starts here
################################################################################

def main(argv=None):
    args = _parse_main_arguments(argv)
    return args.run_fn(args)


################################################################################

def _region_subcommand(_):
    class _MouseListener(pynput.mouse.Listener):

        def __init__(self):
            super().__init__(on_click=self._on_click)
            self.top = -1
            self.left = -1
            self.bottom = -1
            self.right = -1
            print("Click anywhere to register the (top, left) coordinates.")

        def _on_click(self, x, y, button, pressed):
            if button == pynput.mouse.Button.left and pressed:
                if self.top < 0:
                    self.left = x
                    self.top = y
                    print("Click anywhere to register the (bottom, right)"
                          " coordinates")
                else:
                    self.right = x
                    self.bottom = y
                    self.stop()

    with _MouseListener() as listener:
        listener.join()
        print("Top:", listener.top)
        print("Left:", listener.left)
        print("Bottom:", listener.bottom)
        print("Right:", listener.right)
        print("Coordinates Tuple:", (listener.left, listener.top,
                                     listener.right, listener.bottom))

    return 0


################################################################################

def _color_subcommand(_):
    class _MouseListener(pynput.mouse.Listener):

        def __init__(self):
            super().__init__(on_click=self._on_click)

        def _on_click(self, x, y, button, pressed):
            if pressed and button == pynput.mouse.Button.left:
                screen_raw = ImageGrab.grab()
                screen_raw = np.array(screen_raw.convert("RGB"))
                screen_gray = cv2.cvtColor(screen_raw, cv2.COLOR_BGR2GRAY)
                print("{}, {}: {}".format(x, y, screen_gray[y][x]))
            elif pressed and button == pynput.mouse.Button.right:
                self.stop()

    with _MouseListener() as listener:
        print("Left click: show Grayscale color under mouse")
        print("Right click: exit")
        listener.join()

    return 0


################################################################################

def _run_subcommand(args):
    gb_left, gb_right = args.left, args.left + args.width
    gb_top, gb_bot = args.top, args.top + args.height
    gb_coords = {"top": gb_top, "left": gb_left,
                 "width": args.width,
                 "height": args.height,
                 "mon": -1}
                 
    mouse = pynput.mouse.Controller()
    cv2.imshow("WTF", np.zeros((10,10)))
    cv2.waitKey()

    with mss.mss() as sct:
        # counter = 0
        while True:
            start = time.monotonic()
            screen_raw = sct.grab(gb_coords)
            #screen_img = Image.frombytes("RGB", screen_raw.size,
            #                             screen_raw.bgra, "raw", "BGRX")
            #screen_img.show()
            screen_np = np.array(screen_raw)
            screen_cv = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
            #screen_img = Image.fromarray(screen_raw)
            #screen_img.show()
            cv2.imshow("WTF", screen_cv)
            cv2.waitKey(10)

            clicked = False
            for y in range(len(screen_cv)-1, 0, -5):
                width = 0
                for x in range(0, len(screen_cv[y]), 5):
                    if screen_cv[y][x] < 20:
                        width += 1
                        real_x = x + gb_left + 5
                        real_y = y + gb_top + 30
                        # print("Black on: ({}, {})".format(x, y))
                        # print("    Real: ({}, {})".format(real_x, real_y))
                        mouse.position = (real_x, real_y)
                        mouse.click(pynput.mouse.Button.left, 1)
                        clicked = True
                        break
                if clicked:
                    break

            print("Loop takes:", time.monotonic() - start)


################################################################################

# Put the code that analyzes the image in the function
# _test_loop located below this one
def _test_subcommand(args):
    window_name = "Realtime capture"
    gb_coords = {"top": args.top, "left": args.left,
                 "width": args.width,
                 "height": args.height,
                 "mon": -1}
    
    with mss.mss() as sct:
        _test_print_help()

        run_flag = True
        while run_flag:
            image_data = _test_loop(np.array(sct.grab(gb_coords)))
            cv2.imshow(window_name, image_data)

            key = cv2.waitKey(args.sleep)
            if key in KEYS["q"]:
                run_flag = False
            elif key in KEYS["a"]:
                gb_coords["left"] -= 1
            elif key in KEYS["d"]:
                gb_coords["left"] += 1
            elif key in KEYS["w"]:
                gb_coords["top"] -= 1
            elif key in KEYS["s"]:
                gb_coords["top"] += 1
            elif key in KEYS["j"]:
                gb_coords["width"] -= 1
            elif key in KEYS["k"]:
                gb_coords["width"] += 1
            elif key in KEYS["l"]:
                gb_coords["height"] -= 1
            elif key in KEYS["o"]:
                gb_coords["height"] += 1
            elif key in KEYS["h"]:
                _test_print_help()

        # end while
        cv2.destroyAllWindows()


def _test_print_help():
    print("Keys:")
    print(" a/d: move the capture area left/right")
    print(" w/s: move the capture area up/down")
    print(" j/k: make the capture area -/+ wide")
    print(" l/o: make the capture area -/+ tall")
    print(" h: show this message")


# Put your test code here
def _test_loop(screen_raw):
    screen_bw = cv2.cvtColor(screen_raw, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(screen_bw, (5, 5), 0)
    thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]

    contours = cv2.findContours(thresh, 
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    for c in contours:
        # m = cv2.moments(c)
        #c_x = int((m["m10"] / m["m00"]))
        #c_y = int((m["m01"] / m["m00"]))

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.01 * peri, True)

        if len(approx) == 4:
            c = c.astype("int")
            cv2.drawContours(screen_raw, [c], -1, (0, 255, 0), 2)

    return screen_raw


################################################################################

def _parse_main_arguments(argv):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    # region
    region_p = subparsers.add_parser(
        "region",
         help="Waits for the user to click on the (top, left) and"
              " (bottom, right) coordinates and reports them back.")
    region_p.set_defaults(run_fn=_region_subcommand)

    # color
    color_p = subparsers.add_parser(
        "color",
        help="Prints the RGB value of the color under the mouse on click.")
    color_p.set_defaults(run_fn=_color_subcommand)

    # run
    run_p = subparsers.add_parser(
        "run",
        help="Runs the loop that plays the game")

    run_p.add_argument("--top", type=int, required=True,
                       help="Game box top coordinate.")
    run_p.add_argument("--left", type=int, required=True,
                       help="Game box left coordinate.")
    run_p.add_argument("--height", type=int, required=True,
                       help="Game box height.")
    run_p.add_argument("--width", type=int, required=True,
                       help="Game box width.")
    
    run_p.set_defaults(run_fn=_run_subcommand)

    # test
    test_p = subparsers.add_parser(
        "test",
        help="Runs a test loop useful to inspect infomation")
    
    test_p.add_argument("--top", type=int, required=True,
                        help="Game box top coordinate.")
    test_p.add_argument("--left", type=int, required=True,
                        help="Game box left coordinate.")
    test_p.add_argument("--height", type=int, required=True,
                        help="Game box height.")
    test_p.add_argument("--width", type=int, required=True,
                        help="Game box width.")
    test_p.add_argument("--sleep", type=int, default=100,
                        help="Sleep time between loops in milliseconds."
                             " 0 = wait for a key to be pressed.")

    test_p.set_defaults(run_fn=_test_subcommand)

    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main(None))