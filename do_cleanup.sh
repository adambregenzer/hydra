#!/bin/bash
find ./ -name '*.pyc' -print0|xargs -0 rm -f
find ./ -name '*.py~' -print0|xargs -0 rm -f
