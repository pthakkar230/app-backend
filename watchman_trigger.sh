#!/usr/bin/env bash

START_TIME=`date +"%s"`



watchman -j <<-EOT
["trigger", "/workspaces", {
  "name": "test_trigger",
  "expression": ["allof",
    ["match", "*.*"],
    ["since", $START_TIME, "ctime"]
  ],
  "command": ["venv/bin/python", "run_watchman.py", "$DJANGO_SETTINGS_MODULE"],
  "chdir": "`pwd`",
  "stdin": ["name", "exists"]
}]
EOT
