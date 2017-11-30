import json
import logging

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class FeedNetwork(ClientNode):
    """Network model with feeder, can be used for gas network and power grid"""
    def __init__(self, host, vhost, username, password, config_file, api,
                 list_id_snk, list_id_src=set(), losses=0.0,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)
        self._api = api

        # Parameters
        self.list_id_snk = list_id_snk
        self.list_id_src = list_id_src

        self.losses = losses

        # Input
        for i in list_id_snk:
            setattr(self, 'p_snk_{}'.format(i), 0)

        for i in list_id_src:
            setattr(self, 'p_src_{}'.format(i), 0)

        # Output
        self.feeder = 0

        # State
        self.sum_snk = 0
        self.sum_src = 0

    def step(self, current_time, time_step):
        self.sum_snk = sum([getattr(self, 'p_snk_{}'.format(i)) for i in self.list_id_snk])
        # self.sum_src = sum([getattr(self, 'p_src_{}'.format(i)) for i in self.list_id_src])

        self.feeder = (1 + self.losses) * self.sum_snk

        print(self.feeder)

        self.update_attribute("feeder", self.feeder)
        self._api.add_message(self.simulation, self.name, "feeder", current_time, self.feeder)


class FeedNetworkWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _get_params(self):
        return ["list_id_snk", "list_id_src", "losses"]

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        print(ii.arrays['list_id_snk'].strings)

        node = FeedNetwork(host=self.host,
                           vhost='obnl_vhost',
                           username='obnl',
                           password='obnl',
                           config_file=self._obnl_file,
                           api=self,
                           list_id_snk=ii.arrays['list_id_snk'].strings,
                           list_id_src=ii.arrays['list_id_src'].strings,
                           losses=ii.data_values['losses'],
                           input_attributes=self._input_attr,
                           output_attributes=self._output_attr,
                           is_first=False)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    FeedNetworkWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    backend_data = json.loads(open(sys.argv[3]).read())
    obnl_data = json.loads(open(sys.argv[4]).read())

    backend_data["name"] = sys.argv[5]
    obnl_data["name"] = sys.argv[5]

    w = FeedNetworkWrapper("172.17.0.1", "backend_vhost", "tool", "tool",
                           backend_data, obnl_data,
                           input_attr, output_attr)
    w.start()
