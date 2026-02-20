#!/bin/bash

# Script to check rider logins

if [ $# -lt 1 ]; then
    echo "Usage: ./check_rider_login.sh <phone> [passcode]"
    exit 1
fi

PHONE=$1
PASSCODE=${2:-}

# Run the Python script to check rider login
if [ -z "$PASSCODE" ]; then
    python3 /home/packnet777/R1/check_rider_login.py "$PHONE"
else
    python3 /home/packnet777/R1/check_rider_login.py "$PHONE" "$PASSCODE"
fi
