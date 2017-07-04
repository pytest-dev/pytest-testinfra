# coding: utf-8
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=import-error

import threading


class TimedThread(threading.Thread):  # pylint: disable=too-many-instance-attributes
    """Timed Thread helper

    The default arguments specifically @join=False will not time the target
    execution and therefore will background the thread.

    If you set @join=True then, you will be timing the thread execution
    and you can check to see if the timeout occured by looking at
    the @timedout attribute.

    """

    def __init__(self, target, timeout=1800, join=False, daemon=True, args=None, kwargs=None):
        super(TimedThread, self).__init__()
        self._join = join
        self.timeout = timeout
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.timedout = False
        self.finished = threading.Event()
        self.result = None

        # thread setup
        self.setDaemon(daemon)
        self.start()

    def start(self):
        super(TimedThread, self).start()

        if self._join:
            self.join(self.timeout)

            if self.is_alive():
                self.timedout = True
                self.cancel()

    def cancel(self):
        self.finished.set()

    def run(self):
        if not self.finished.is_set():
            self.result = self.target(*self.args, **self.kwargs)
