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
import yaml
import string
import re

from ansible.plugins.callback import CallbackBase
from ansible.inventory.host import Host
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.parsing.yaml.dumper import AnsibleDumper

# From https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/yaml.py
def my_represent_scalar(self, tag, value, style=None):
    """Uses block style for multi-line strings"""
    if style is None:
        if should_use_block(value):
            style = '|'
            # we care more about readable than accuracy, so...
            # ...no trailing space
            value = value.rstrip()
            # ...and non-printable characters
            value = ''.join(x for x in value if x in string.printable)
            # ...tabs prevent blocks from expanding
            value = value.expandtabs()
            # ...and odd bits of whitespace
            value = re.sub(r'[\x0b\x0c\r]', '', value)
            # ...as does trailing space
            value = re.sub(r' +\n', '\n', value)
        else:
            style = self.default_style
    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node

# from http://stackoverflow.com/a/15423007/115478
def should_use_block(value):
    """Returns true if string should be in block format"""
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False

class CallbackModule(CallbackBase):
  CALLBACK_VERSION = 2.0
  CALLBACK_TYPE = 'stdout'
  CALLBACK_NAME = 'diff'

  def __init__(self, display=None):
    super(CallbackModule, self).__init__(display)

    yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar
    self.results = {}

  def v2_on_file_diff(self, result):
    """When the playbook ran in diff mode, collect results"""

    host = result._host.get_name()

    if host not in self.results:
      self.results.update( { host : { "changed": "false" } } )

    """If no_log is set, add a result to indicate that changes have been redacted"""
    # TODO: provide filepath or name of the task so there's context for what was no_log'd.
    if 'censored' in result._result:
      # Maybe something in result data can do that at this point:
      # self._display.display(yaml.dump(result._task._attributes['name']))
      no_log_results = {
        "redacted": {
          "redacted_change": result._result['censored']
        }
      }
      self.results[host].update(no_log_results)

    """If there is a diff, construct a dict from it with before and after"""
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

        if before != after:

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
    self._display.display(yaml.dump(output, allow_unicode=True, width=1000, Dumper=AnsibleDumper, default_flow_style=False))
