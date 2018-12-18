# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: diff
    type: stdout
    short_description: Replace play output with summary of changes based on --diff.
    version_added: 2.5
    description:
        - Rather than printing output for each task, print a summary of changes based on --diff output.
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout in ansible.cfg
'''

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

    self.results = {}

  def v2_on_file_diff(self, result):
    """When the playbook ran in diff mode, collect results"""

    host = result._host.get_name()

    if host not in self.results:
      self.results.update( { host : { "changed": "false" } } )

    # contains only {"changed": true, "censored": "the output has been hidden due to the fact that 'no_log: true' was specified for this result"} for no_log tasks
    # I'm not clear how you can get the path to the file that was modified by no-log without running with -vvvv so _dump_result contains invocation keys?
    if 'censored' in result._result:
      no_log_results = {
        "censorship!": "censored"
      }

      self.results[host].update( { "changed" : result._result['changed'] } )
      self.results[host].update(no_log_results)

    if 'diff' in result._result:
      diff = {}
      diff_contents = result._result['diff']

      """Construct a dict with the target changed as the dict name, and the before and after state as keys/value pairs."""

      for item in diff_contents:

        if 'before' in item:
          before = item['before']
        else:
          before = ''

        if 'after' in item:
          after = item['after']
        else:
          after = ''

        changeset = {
          item['after_header']: {
            'before': before,
            'after': after
          }
        }

        diff.update(changeset)

      self.results[host].update(diff)

  def v2_playbook_on_stats(self, stats):
    """Display info about changes"""

    output = {
      'changes': self.results
    }
    self._display.display(json.dumps(output, cls=AnsibleJSONEncoder, indent=4, sort_keys=True))
