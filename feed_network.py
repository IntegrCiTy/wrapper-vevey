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
        self.sum_src = sum([getattr(self, 'p_src_{}'.format(i)) for i in self.list_id_src])

        self.feeder = (1 + self.losses) * self.sum_snk - self.sum_src


class FeedNetworkWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = FeedNetwork(host=self.host,
                           vhost='obnl_vhost',
                           username='obnl',
                           password='obnl',
                           config_file=self._obnl_file,
                           api=self,
                           list_id_snk=ii.arrays['list_id_snk'].values,
                           list_id_src=ii.arrays['list_id_src'].values,
                           losses=ii.data_values['losses'],
                           input_attributes=self._input_attr,
                           output_attributes=self._output_attr,
                           is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    FeedNetworkWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    w = FeedNetworkWrapper("172.17.0.1", "backend_vhost", "tool", "tool", sys.argv[3], sys.argv[4],
                           input_attr, output_attr)
    w.start()