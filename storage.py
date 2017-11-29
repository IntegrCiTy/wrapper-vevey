import json
import logging

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class Storage(ClientNode):
    """Energy storage model (without losses), can be used for battery and thermal buffer"""

    def __init__(self, host, vhost, username, password, config_file, api,
                 capacity, soc_init=0.5,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)

        # Parameters
        self.capacity = capacity  # kWh

        # Input
        self.p_src = 0  # kW
        self.p_snk = 0  # kW

        # Output
        self.soc = soc_init

    def step(self, current_time, time_step):
        self.soc += time_step / 3600 * (self.p_src - self.p_snk) / self.capacity


class StorageWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = Storage(host=self.host,
                       vhost='obnl_vhost',
                       username='obnl',
                       password='obnl',
                       config_file=self._obnl_file,
                       api=self,
                       capacity=ii.data_values['capacity'],
                       soc_init=ii.data_values['soc_init'],
                       input_attributes=self._input_attr,
                       output_attributes=self._output_attr,
                       is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    StorageWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    w = StorageWrapper("172.17.0.1", "backend_vhost", "tool", "tool", sys.argv[3], sys.argv[4],
                       input_attr, output_attr)
    w.start()
