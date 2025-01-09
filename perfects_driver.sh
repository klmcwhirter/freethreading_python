#!/bin/bash

MAX_N=1_000_000
NUM_WORKERS=10

# cycle through matrix of options

for p in python3.14.0a3 python3.14.0a3t
do
  for em in '' '-p' '-s' '-t'
  do
    for v in '' '-v'
    do
      echo
      echo "pause for 5 secs to coalesce ..."
      echo
      sleep 5

      cmd="uv run ${p} perfects.py -n ${MAX_N} -w ${NUM_WORKERS} ${v} ${em}"
      echo ${cmd}
      ${cmd}
    done
  done
done 2>&1 | tee perfects_driver.out
