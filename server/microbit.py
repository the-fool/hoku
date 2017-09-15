from bluezero import dbus_tools, constants, microbit
import logging
import time


class MyMicrobit(microbit.Microbit):
    UART_SRV = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
    UART_DATA = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uart_data = self.ubit.add_characteristic(self.UART_SRV,
                                                       self.UART_DATA)

    def _subscribe(self, chrc, cb):
        chrc.resolve_gatt()
        uuid = chrc.chrc_uuid
        path = dbus_tools.get_dbus_path(
            characteristic=uuid,
            device=self.device_addr,
            adapter=self.adapter_addr)

        obj = dbus_tools.get_dbus_obj(path)
        iface = dbus_tools.get_dbus_iface(constants.DBUS_PROP_IFACE, obj)
        iface.connect_to_signal('PropertiesChanged', cb)
        obj.StartNotify(
            reply_handler=lambda: logging.debug('subscribed'),
            error_handler=dbus_tools.generic_error_cb,
            dbus_interface=constants.GATT_CHRC_IFACE)

    def subscribe_uart(self, cb):
        self._subscribe(self._uart_data, cb)

    def subscribe_accel(self, cb):
        self._subscribe(self._accel_data, cb)

    def connect(self):
        try:
            self.ubit.rmt_device.connect()
            counter = 0
            while not self.ubit.services_resolved:
                if counter > 5:
                    raise
                time.sleep(2)
                counter = counter + 1
            return True
        except:
            return False
