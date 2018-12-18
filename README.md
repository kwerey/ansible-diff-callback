# Objective

I want to use Ansible to manage changes to monitoring configuration effectively in a CI/CD context.

One pain point we experience is that manual changes get made in order to act on urgent break/fix issues, and then don't get backported into our nice version control driven config management.

In order to make those manual changes apparent and be super clear when pushing any given set changes will break something, I'd like to set up jobs that runs a playbook with `--check --diff` flags, and gives a concise report of what would be affected by pushing a given update with Ansible.

I'd like to provide an at-a-glance view that will summaries "this job will add this 6 lines of JSON to that config file and remove these 2 lines from that one" by collecting and aggregating the diff output for each task.

Value proposition:

- Checking there aren't any other stray changes merged into version control but not deployed yet
- Checking there haven't been manual changes made that will be overridden - in other words, no unknown consequences!
- As a concise audit log of when changes were pushed.
- As a final typo-proofreading opportunity for the person pushing the update

## Current state

Right now, output looks like this

```
$ ansible-playbook -i hosts template.yml --diff
changes:
  test-host-1:
    /Users/nbailey/git/utility/callback/tests/test_file (content):
      after: |-
        Now it's version F
      before: |-
        This is version C
    changed: 'false'
    redacted:
      redacted_change: 'the output has been hidden due to the fact that ''no_log: true'' was specified for this result'
  test-host-2:
    /Users/nbailey/git/utility/callback/tests/host2file (content):
      after: |-
        But it's changed to version 2!!
      before: |-
        Now it's version 1
    changed: 'false'
    redacted:
      redacted_change: 'the output has been hidden due to the fact that ''no_log: true'' was specified for this result'
```

## What's in this repo?

The starting point is a little test sandbox with hosts that have inventory to swap a file between states:

```
test_file_first:
  path: ~/git/utility/callback/tests/test_file
  contents: "This is version A"

test_file_second:
  path: ~/git/utility/callback/tests/test_file
  contents: "Now it's version B"
```

And playbook to lineinfile those one over the other:
---

```
- name: Write a file with one set of contents, then another.
  hosts: localhost

  tasks:

  - name: Version A
    lineinfile:
      path: "{{ test_file_first.path }}"
      state: present
      create: yes
      line: "{{ test_file_first.contents }}"
      regexp: ".*version.*"
    register: a

  - name: Version B
    lineinfile:
      path: "{{ test_file_second.path }}"
      state: present
      create: yes
      line: "{{ test_file_second.contents }}"
      regexp: ".*version.*"
```

a callback_plugin directory adjacent to the playbook, with the callback plugin in progress. This removes normal playbook output and overrides the 'on file diff' class and constructs a data structure showing diffs for each host.


## To be done

### Next

Validate how this looks in a couple of different situations (multiline files, new files/directories, deletions)

### Also

- Colourized diff lines? like this https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py#L179

- Think about workflow:

  - should this be a plugin that replaces stdout, or prepends results to the top, or should we write the normal play output to a log file and then cat it at the end of the job for further info?
  - Can I make this more graceful by disabling it when diff mode is not enabled? (right now, it'll just place all playbook output with an empty list when there's no diff results to be had)
  - see if there's a way to enable the plugin only when running in check mode?

  => Current thinking, it doesn't seem to be easily to gracefully return the stdout callback to default. I'll just set Jenkins up to only enable this for individual plays.

## Reference

Callback plugins seem to be the right place to do this:
- https://docs.ansible.com/ansible/2.6/plugins/callback.html
- https://docs.ansible.com/ansible/2.6/dev_guide/developing_plugins.html#callback-plugins

This link has some good simple starting points: https://dev.to/jrop/creating-an-alerting-callback-plugin-in-ansible---part-i-1h0n

There’s an on_file_diff class we can override: https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py#L334

## Misc things learned

You can validate plugins are loaded by running your playbook with -vvvv and looking for the following line:

```
Loading callback plugin <name> of type <type>, v2.0 from /<path-to-plugin>/<pluginname>.pyc
```

If you want to replace the normal Ansible stdout with output from your own plugin you need to also add the stdout_callback setting to ansible.cfg.

```
[defaults]
stdout_callback = diff
```
