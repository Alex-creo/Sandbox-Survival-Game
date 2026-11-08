"""Native desktop entry point. --offscreen is intended for automated testing."""
import argparse
import logging
import sys
from engine.config import DATA, load_settings
from panda3d.core import loadPrcFileData


def main():
    parser=argparse.ArgumentParser(description='Physics Sandbox 3D')
    parser.add_argument('--offscreen',action='store_true')
    parser.add_argument('--smoke-test',action='store_true',help='Render 120 frames, save a screenshot and exit')
    args=parser.parse_args()
    settings=load_settings()
    DATA.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=DATA/'game.log',level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    loadPrcFileData('',f'window-title Physics Sandbox 3D\nwin-size {settings["resolution"][0]} {settings["resolution"][1]}\nsync-video true\naudio-library-name null\nnotify-level warning\ntextures-power-2 none')
    if args.offscreen: loadPrcFileData('','window-type offscreen\nload-display p3headlessgl')
    try:
        from engine.application import SandboxApp
        app=SandboxApp()
        if args.smoke_test:
            from panda3d.core import ClockObject
            clock=ClockObject.getGlobalClock(); clock.setMode(ClockObject.MNonRealTime); clock.setDt(1/60)
            for _ in range(120): app.taskMgr.step()
            app.win.saveScreenshot(str(DATA/'smoke-test.png'))
            app.destroy()
            print('Smoke test passed')
        else: app.run()
    except Exception:
        logging.exception('Game stopped unexpectedly')
        print(f'Unable to run Physics Sandbox. Details: {DATA / "game.log"}',file=sys.stderr)
        raise


if __name__=='__main__': main()
