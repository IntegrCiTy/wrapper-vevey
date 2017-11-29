import json
import logging

import queue

from ict.connection.node import Node

from ict.protobuf.simulation_pb2 import *
from ict.protobuf.db_pb2 import *
from ict.protobuf.core_pb2 import MetaMessage


class Wrapper(Node):
    def __init__(self, host, vhost, username, password, config_file, obnl_file,
                 input_attr, output_attr):
        super().__init__(host, vhost, username, password, config_file)
        self._obnl_file = obnl_file

        self._input_attr = input_attr
        self._output_attr = output_attr

        self._queue = queue.Queue()

    def on_block(self, ch, method, props, body):
        Node.LOGGER.info(self._name + " receives a block message.")
        m = MetaMessage()
        m.ParseFromString(body)

        if m.details.Is(DataRequired.DESCRIPTOR):
            dr = DataRequired()
            m.details.Unpack(dr)

            fwd = MetaMessage()
            fwd.node_name = self._name

            dr.stored_data.append("values")
            fwd.details.Pack(dr)

            self.send('', 'db.data.init', fwd.SerializeToString(),
                      reply_to='coside.cosim.simu.' + SimulationBlock.Name(dr.block) + '.' + self.name)

        elif m.details.Is(InitInfo.DESCRIPTOR):
            node = self._create_node(m)
            node.start()

        self._channel.basic_ack(delivery_tag=method.delivery_tag)

    def add_message(self, message):
        self._queue.put(message)

    def on_local(self, ch, method, props, body):

        try:
            message = self._queue.get(timeout=0.1)
            self.send('', 'db.data.store', message.SerializeToString())
        except queue.Empty:
            pass

        self._channel.basic_ack(delivery_tag=method.delivery_tag)
        self.send('', 'wrapper.local.' + self.name, "next")

    def _create_node(self, m):
        raise NotImplementedError("Abstract function call.")
