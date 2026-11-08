"""Desktop key bindings, kept independent of physics and GUI construction."""


class InputBindings:
    def __init__(self, app):
        for key in ('w','a','s','d','shift','space'):
            app.accept(key,app.key,[key,True])
            app.accept(key+'-up',app.key,[key,False])
        actions = {
            'space': app.jump, 'tab': app.menu, 'escape': app.pause,
            'e': app.interact, 'mouse1': app.tools.select, 'mouse3': app.tools.cancel,
            'delete': app.tools.delete, 'r': app.tools.rotate, 'f': app.tools.freeze,
            'g': app.tools.grab, 'j': app.tools.attach,
            'f5': app.quick_save, 'f9': app.quick_load,
        }
        for event, callback in actions.items(): app.accept(event, callback)
        app.accept('h',app.tools.attach,[True])
        app.accept('wheel_up',app.adjust_distance,[-.5])
        app.accept('wheel_down',app.adjust_distance,[.5])
