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

__all__ = ('Device',)


import cc_lib


class Device(cc_lib.types.Device):

    def __init__(self, id: str, name: str, type: str, state: str, mod: str):
        self.id = id
        self.name = name
        self.device_type_id = type
        self.state = state
        self.module_id = mod

    def __iter__(self):
        items = (
            ("name", self.name),
            ("device_type", self.device_type_id),
            ("state", self.state),
            ("module_id", self.module_id)
        )
        for item in items:
            yield item
