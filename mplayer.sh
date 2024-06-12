#!/bin/bash

THISDIR="$(dirname "$(realpath "$0")")"
PYTHONPATH="${THISDIR}:${PYTHONPATH}"
python3 -m mplayer "${@}"
