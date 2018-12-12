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

## Example successful end state

Something along these lines

```
host1:
---
Files changed:
/Users/nbailey/git/utility/callback/tests/test_file
/Users/nbailey/git/utility/callback/tests/another_test_file

--- before: /Users/nbailey/git/utility/callback/tests/test_file (content)
+++ after: /Users/nbailey/git/utility/callback/tests/test_file (content)
@@ -1 +1 @@
-Now it's version B
+This is version A

--- before: /Users/nbailey/git/utility/callback/tests/another_test_file (content)
+++ after: /Users/nbailey/git/utility/callback/tests/another_test_file (content)
@@ -1 +1 @@
-Now it's version B
+This is version A

host2:
---
Files changed:
/Users/nbailey/git/utility/callback/tests/test_file

--- before: /Users/nbailey/git/utility/callback/tests/test_file (content)
+++ after: /Users/nbailey/git/utility/callback/tests/test_file (content)
@@ -1 +1 @@
-Now it's version B

```

## Reference

Callback plugins seem to be the right place to do this:
- https://docs.ansible.com/ansible/2.6/plugins/callback.html
- https://docs.ansible.com/ansible/2.6/dev_guide/developing_plugins.html#callback-plugins

This link has some good simple starting points: https://dev.to/jrop/creating-an-alerting-callback-plugin-in-ansible---part-i-1h0n

There’s an on_file_diff class we can override: https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py#L334

## What's in this repo?

The starting point is a little test sandbox with the following:

host_vars for localhost

```
test_file_first:
  path: ~/git/utility/callback/tests/test_file
  contents: "This is version A"

test_file_second:
  path: ~/git/utility/callback/tests/test_file
  contents: "Now it's version B"
```

A playbook to lineinfile them one over the other:
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

a callback_plugin directory adjacent to the playbook, with the callback plugin in progress. This can currently grab diffs when run in diff mode, and collect them in a list.

```
$ ansible-playbook -i hosts template.yml --diff
{
    "plays": [
        [
            {
                "after": "This is version A\n",
                "after_header": "/Users/nbailey/git/utility/callback/tests/test_file (content)",
                "before": "",
                "before_header": "/Users/nbailey/git/utility/callback/tests/test_file (content)"
            },
            {
                "after_header": "/Users/nbailey/git/utility/callback/tests/test_file (file attributes)",
                "before_header": "/Users/nbailey/git/utility/callback/tests/test_file (file attributes)"
            }
        ],
        [
            {
                "after": "Now it's version B\n",
                "after_header": "/Users/nbailey/git/utility/callback/tests/test_file (content)",
                "before": "This is version A\n",
                "before_header": "/Users/nbailey/git/utility/callback/tests/test_file (content)"
            },
            {
                "after_header": "/Users/nbailey/git/utility/callback/tests/test_file (file attributes)",
                "before_header": "/Users/nbailey/git/utility/callback/tests/test_file (file attributes)"
            }
        ]
    ]
}
```

## To be done

Next: Grab task names and format output so it displays changes in order by named task

Then: Support running against as many hosts as are in inventory

Then: See if there's a way to enable the plugin only when running in check mode

Think about workflow:

- should this be a plugin that replaces stdout, or prepends results to the top, or should we write the normal play output to a log file and then cat it at the end of the job for further info?
- Can I make this more graceful by disabling it when diff mode is not enabled? (right now, it'll just place all playbook output with an empty list when there's no diff results to be had)


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
