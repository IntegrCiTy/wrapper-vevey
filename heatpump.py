import json
import logging

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class HeatPump(ClientNode):
    """Heat pump model with COP as ratio of Carnot's COP"""

    def __init__(self, host, vhost, username, password, config_file, api,
                 p_nom, alpha=0.25,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)
        self._api = api

        # Parameters
        self.p_nom = p_nom  # kW
        self._alpha = alpha
        self._K = 273.15

        # Input
        self.io = 0
        self.t_src = 25.0
        self.t_snk_set = 70.0

        # Output
        self.p_src = 0  # kW
        self.p_snk = 0  # kW
        self.p_ele = 0  # kW

        # State
        self.cop = 1.0

    def step(self, current_time, time_step):
        self.cop = self._alpha * (self._K+self.t_snk_set) / (self.t_snk_set - self.t_src)

        self.p_snk = self.io * self.p_nom
        self.p_ele = self.p_snk / self.cop
        self.p_src = self.p_snk - self.p_ele

        self.update_attribute("p_snk", self.p_snk)
        self._api.add_message(self.simulation, self.name, "p_snk", self.p_snk)
        self.update_attribute("p_ele", self.p_ele)
        self._api.add_message(self.simulation, self.name, "p_ele", self.p_ele)
        self.update_attribute("p_src", self.p_src)
        self._api.add_message(self.simulation, self.name, "p_src", self.p_src)


class HeatPumpWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _get_params(self):
        return ["p_nom", "alpha"]

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = HeatPump(host=self.host,
                        vhost='obnl_vhost',
                        username='obnl',
                        password='obnl',
                        config_file=self._obnl_file,
                        api=self,
                        p_nom=ii.data_values['p_nom'],
                        alpha=ii.data_values['alpha'],
                        input_attributes=self._input_attr,
                        output_attributes=self._output_attr,
                        is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    HeatPumpWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    backend_data = json.loads(open(sys.argv[3]).read())
    obnl_data = json.loads(open(sys.argv[4]).read())

    backend_data["name"] = sys.argv[5]
    obnl_data["name"] = sys.argv[5]

    w = HeatPumpWrapper("172.17.0.1", "backend_vhost", "tool", "tool",
                        backend_data, obnl_data,
                        input_attr, output_attr)
    w.start()
