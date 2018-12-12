# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.plugins.callback import CallbackBase
from ansible.inventory.host import Host
from ansible.parsing.ajson import AnsibleJSONEncoder

class CallbackModule(CallbackBase):
  CALLBACK_VERSION = 2.0
  CALLBACK_TYPE = 'stdout'
  CALLBACK_NAME = 'diff'

  def __init__(self, display=None):
    super(CallbackModule, self).__init__(display)
    self.results = []

  def v2_on_file_diff(self, result):
    """When the playbook ran in diff mode, collect results"""

    if 'diff' in result._result:
      host = result._host.get_name()

      self.results.append(result._result['diff'])

  def v2_playbook_on_stats(self, stats):
    """Display info about playbook statistics"""

    output = {
      'plays': self.results,
    }
    # output = {
    #
    #     'stats': summary,
    #     'custom_stats': custom_stats,
    #     'global_custom_stats': global_custom_stats,
    # }

    self._display.display(json.dumps(output, cls=AnsibleJSONEncoder, indent=4, sort_keys=True))
