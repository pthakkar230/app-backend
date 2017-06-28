#!/usr/bin/env bash

# TODO: 99% sure stdout and stderr can be removed for deployment

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
  "stdin": ["name", "exists"],
   "stdout": ">>/Users/jgriebel/3blades-forks/app-backend/watchman_out.log",
  "stderr": ">>/Users/jgriebel/3blades-forks/app-backend/watchman_out.log"
}]
EOT
