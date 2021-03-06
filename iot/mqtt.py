"""
   Copyright 2020 InfAI (CC SES)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

__all__ = ("Client", )


from .logger import root_logger, logging_levels
from .configuration import config, EnvVars
import paho.mqtt.client
import logging
import threading


logger = root_logger.getChild(__name__.split(".", 1)[-1])

mqtt_logger = logging.getLogger("mqtt-client")
mqtt_logger.setLevel(logging_levels.setdefault(config.Logger.mqtt_level, "info"))


class Client(threading.Thread):
    def __init__(self, upstream_queue):
        super().__init__(name="mqtt", daemon=True)
        self.__upstream_queue = upstream_queue
        self.__mqtt = paho.mqtt.client.Client(
            client_id=EnvVars.ModuleID.value,
            clean_session=config.MQTTClient.clean_session
        )
        self.__mqtt.on_connect = self.__onConnect
        self.__mqtt.on_disconnect = self.__onDisconnect
        self.__mqtt.on_message = self.__onMessage
        self.__mqtt.enable_logger(mqtt_logger)
        self.__discon_count = 0

    def run(self) -> None:
        while True:
            try:
                self.__mqtt.connect(config.MB.host, config.MB.port, keepalive=config.MQTTClient.keep_alive)
            except Exception as ex:
                logger.error(
                    "could not connect to '{}' on '{}' - {}".format(config.MB.host, config.MB.port, ex)
                )
            try:
                self.__mqtt.loop_forever()
            except Exception as ex:
                logger.error("mqtt loop broke - {}".format(ex))

    def __onConnect(self, client, userdata, flags, rc):
        if rc == 0:
            self.__discon_count = 0
            logger.info("connected to '{}'".format(config.MB.host))
            self.__mqtt.subscribe(config.MQTTClient.event_topic)
            self.__mqtt.subscribe(config.MQTTClient.response_topic)
        else:
            logger.error("could not connect to '{}' - {}".format(config.MB.host, paho.mqtt.client.connack_string(rc)))

    def __onDisconnect(self, client, userdata, rc):
        if self.__discon_count < 1:
            if rc == 0:
                logger.info("disconnected from '{}'".format(config.MB.host))
            else:
                logger.warning("disconnected from '{}' unexpectedly".format(config.MB.host))
            self.__discon_count += 1

    def __onMessage(self, client, userdata, message: paho.mqtt.client.MQTTMessage):
        try:
            self.__upstream_queue.put_nowait((message.topic.split("/"), message.payload))
        except Exception as ex:
            logger.error(ex)

    def publish(self, topic: str, payload: str, qos: int) -> None:
        try:
            msg_info = self.__mqtt.publish(topic=topic, payload=payload, qos=qos, retain=False)
            if msg_info.rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
                logger.debug("publish '{}' - (q{}, m{})".format(payload, qos, msg_info.mid))
            elif msg_info.rc == paho.mqtt.client.MQTT_ERR_NO_CONN:
                logger.error("not connected")
            else:
                logger.error(paho.mqtt.client.error_string(msg_info.rc).replace(".", "").lower())
        except (ValueError, OSError) as ex:
            logger.error(ex)
