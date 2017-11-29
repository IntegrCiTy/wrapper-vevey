import json
import logging

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class Hysteresis(ClientNode):
    """Hysteresis model, for control application"""

    def __init__(self, host, vhost, username, password, config_file, api,
                 t_set=70.0, v_min=0.25, v_max=1, io_init=0,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)

        # Parameters
        self.v_min = v_min
        self.v_max = v_max

        # Input
        self.v_mes = v_max - 0.01

        # Output
        self.io = io_init
        self.t_set = t_set

    def step(self, current_time, time_step):
        if self.io == 0 and self.v_mes <= self.v_min:
            self.io = 1

        if self.io == 1 and self.v_mes >= self.v_max:
            self.io = 0


class HysteresisWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = Hysteresis(host=self.host,
                          vhost='obnl_vhost',
                          username='obnl',
                          password='obnl',
                          config_file=self._obnl_file,
                          api=self,
                          t_set=ii.data_values['t_set'],
                          v_min=ii.data_values['v_min'],
                          v_max=ii.data_values['v_max'],
                          io_init=ii.data_values['io_init'],
                          input_attributes=self._input_attr,
                          output_attributes=self._output_attr,
                          is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    HysteresisWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    backend_data = json.loads(open(sys.argv[3]).read())
    obnl_data = json.loads(open(sys.argv[4]).read())

    backend_data["name"] = sys.argv[5]
    obnl_data["name"] = sys.argv[5]

    w = HysteresisWrapper("172.17.0.1", "backend_vhost", "tool", "tool",
                          backend_data, obnl_data,
                          input_attr, output_attr)
    w.start()
