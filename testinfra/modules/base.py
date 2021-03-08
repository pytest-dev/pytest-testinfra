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
import abc
import typing


class Module(metaclass=abc.ABCMeta):
    if typing.TYPE_CHECKING:
        import testinfra.host

        _host: testinfra.host.Host

    @classmethod
    def get_module(cls, _host):
        klass = cls.get_module_class(_host)
        return type(
            klass.__name__,
            (klass,),
            {"_host": _host},
        )

    @classmethod
    def get_module_class(cls, host):
        return cls

    @classmethod
    def run(cls, *args, **kwargs):
        return cls._host.run(*args, **kwargs)

    @classmethod
    def run_test(cls, *args, **kwargs):
        return cls._host.run_test(*args, **kwargs)

    @classmethod
    def run_expect(cls, *args, **kwargs):
        return cls._host.run_expect(*args, **kwargs)

    @classmethod
    def check_output(cls, *args, **kwargs):
        return cls._host.check_output(*args, **kwargs)

    @classmethod
    def find_command(cls, *args, **kwargs):
        return cls._host.find_command(*args, **kwargs)


class InstanceModule(Module):
    @classmethod
    def get_module(cls, _host):
        klass = super().get_module(_host)
        return klass()
