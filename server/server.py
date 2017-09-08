from bluezero import microbit, tools, constants
from .web.ws import run as ws_run
from .web.http import run as http_run
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import threading

# ACCEL_SRV = 'E95D0753-251D-470A-A062-FA1922DFA9A8'
# ACCEL_DATA = 'E95DCA4B-251D-470A-A062-FA1922DFA9A8'
loop = None


class MyMicrobit(microbit.Microbit):
    def _accel_notify_cb(self):
        print('Accel subscribed!!!')
        return 1

    def subscribe_accel(self, user_callback):
        accel_obj = tools.get_dbus_obj(constants.BLUEZ_SERVICE_NAME,
                                       self.accel_data_path)
        accel_iface = tools.get_dbus_iface(constants.DBUS_PROP_IFACE,
                                           accel_obj)
        accel_iface.connect_to_signal('PropertiesChanged', user_callback)
        accel_obj.StartNotify(
            reply_handler=self._accel_notify_cb,
            error_handler=tools.generic_error_cb,
            dbus_interface=constants.GATT_CHRC_IFACE)


def find_mbit(name):
    try:
        return MyMicrobit(name=name)
    except:
        return None


def connect_mbit(mbit):
    try:
        mbit.connect()
        return True
    except:
        return False


def setup_dbus_loop():
    DBusGMainLoop(set_as_default=True)


def run_dbus_loop():
    global loop
    loop = GLib.MainLoop()
    loop.run()


def quit_dbus_loop():
    global loop
    loop.quit()


# BEGIN MAIN
def connect_to_vozuz():
    print('Finding VOZUZ')
    vozuz = find_mbit(name='vozuz')
    if vozuz is None:
        print('Failed to find VOZUZ')
        exit(1)

        print('Connecting to VOZUZ')
    if not connect_mbit(vozuz):
        print('Failed to connect to VOZUZ')
        exit(1)

    print('Subscribing to accel')
    vozuz.subscribe_accel(lambda l, data, sig: print('got: {}'.format(tools.bytes_to_xyz(data['Value']))))

    print('Setting up dbus loop')
    setup_dbus_loop()

    print('Running main loop')
    run_dbus_loop()


def run():
    ws = threading.Thread(target=ws_run, args=())
    http = threading.Thread(target=http_run, args=())
    ws.start()
    http.start()

    ws.join()
    http.join()
