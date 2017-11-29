import json
import logging

from ict.protobuf.db_pb2 import *
from obnl.core.client import ClientNode

from node import Wrapper


class Profile(ClientNode):
    """Fixed profile model, can be used for heat or electricity consumers or PV production"""

    def __init__(self, host, vhost, username, password, config_file, api,
                 profile,
                 input_attributes=None, output_attributes=None, is_first=False):
        super().__init__(host, vhost, username, password, config_file,
                         input_attributes, output_attributes, is_first)
        
        # Parameters
        self.profile = profile
        
        # Output
        self.value = profile[0]
        
        # State
        self.t = 0

    def step(self, current_time, time_step):
        self.t += time_step
        self.value = self.profile[self.t % len(self.profile)]


class ProfileWrapper(Wrapper):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr)
        self.on_block(self._channel, *self._channel.consume("coside.cosim.simu.PROFILE"))

    def _get_params(self):
        return ["profile"]

    def _create_node(self, m):
        ii = InitInfo()
        m.details.Unpack(ii)

        node = Profile(host=self.host,
                       vhost='obnl_vhost',
                       username='obnl',
                       password='obnl',
                       config_file=self._obnl_file,
                       api=self,
                       profile=ii.arrays['profile'].values,
                       input_attributes=self._input_attr,
                       output_attributes=self._output_attr,
                       is_first=True)
        self.send('', 'wrapper.local.' + self.name, "next")
        return node


if __name__ == "__main__":
    ProfileWrapper.activate_console_logging(logging.DEBUG)

    input_attr = json.loads(sys.argv[1])
    output_attr = json.loads(sys.argv[2])

    backend_data = json.loads(open(sys.argv[3]).read())
    obnl_data = json.loads(open(sys.argv[4]).read())

    backend_data["name"] = sys.argv[5]
    obnl_data["name"] = sys.argv[5]

    w = ProfileWrapper("172.17.0.1", "backend_vhost", "tool", "tool",
                       backend_data, obnl_data,
                       input_attr, output_attr)
    w.start()
