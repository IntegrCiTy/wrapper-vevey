import json
import logging
import uuid

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class Efficiency(ClientNode):
    """Production model, based on a fixed efficiency, can be used for gas or oil boiler"""

    def __init__(self, host, vhost, username, password, config_file, api,
                 eff=1.0,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)

        # Parameters
        self.eff = eff

        # Input
        self.p_snk = 0

        # Output
        self.p_src = 0

    def step(self, current_time, time_step):
        self.p_src = self.p_snk / self.eff


class EfficiencyWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = Efficiency(host=self.host,
                          vhost='obnl_vhost',
                          username='obnl',
                          password='obnl',
                          config_file=self._obnl_file,
                          api=self,
                          eff=ii.data_values['eff'],
                          input_attributes=self._input_attr,
                          output_attributes=self._output_attr,
                          is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    EfficiencyWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    backend_data = json.loads(open(sys.argv[3]).read())
    obnl_data = json.loads(open(sys.argv[4]).read())

    node_id = uuid.uuid1()
    backend_data["name"] = "Efficiency_"+str(node_id)
    obnl_data["name"] = "Efficiency_"+str(node_id)

    w = EfficiencyWrapper("172.17.0.1", "backend_vhost", "tool", "tool", backend_data, obnl_data,
                          input_attr, output_attr)
    w.start()
