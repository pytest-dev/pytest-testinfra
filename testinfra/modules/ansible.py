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

from __future__ import absolute_import
from __future__ import unicode_literals


from testinfra.modules.base import InstanceModule


class Ansible(InstanceModule):
    """Run Ansible module functions

    This module is only available with the :ref:`ansible connection
    backend` connection backend.

    `Check mode
    <https://docs.ansible.com/ansible/playbooks_checkmode.html>`_ is
    enabled by default, you can disable it with `check=False`.

    >>> Ansible("apt", "name=nginx state=present")["changed"]
    False
    >>> Ansible("setup")["ansible_facts"]["ansible_lsb"]["codename"]
    'jessie'
    >>> Ansible("file", "path=/etc/passwd")["mode"]
    '0640'

    """

    def __call__(self, module_name, module_args=None, check=True, **kwargs):
        if not self._backend.HAS_RUN_ANSIBLE:
            raise RuntimeError((
                "Ansible module is only available with ansible "
                "connection backend"))
        return self._backend.run_ansible(
            module_name, module_args, check=check, **kwargs)

    def get_variables(self):
        """Returns a dict of ansible variables

        >>> Ansible.get_variables()
        {
            'inventory_hostname': 'localhost',
            'group_names': ['ungrouped'],
            'foo': 'bar',
        }

        """
        return self._backend.get_variables()

    def __repr__(self):
        return "<ansible>"
