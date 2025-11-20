#!/usr/bin/env python3
"""
Debug script to see raw telnet responses from 7D2D server.
This helps update the regex patterns in the action files.
"""
import telnetlib
import json
import time
import re

# Load config
with open('bot/options/module_telnet.json', 'r') as f:
    config = json.load(f)

HOST = config['host']
PORT = config['port']
PASSWORD = config['password']

print(f"Connecting to {HOST}:{PORT}...")

# Connect
tn = telnetlib.Telnet(HOST, PORT, timeout=5)

# Wait for password prompt
response = tn.read_until(b"Please enter password:", timeout=3)
print("Got password prompt")

# Send password
tn.write(PASSWORD.encode('ascii') + b"\r\n")

# Wait for welcome message
time.sleep(1)
welcome = tn.read_very_eager().decode('utf-8')
print("Connected!\n")

# Commands to test
commands = [
    'admin list',
    'lp',
    'gettime',
    'getgamepref',
    'getgamestat',
    'listents'
]

for cmd in commands:
    print(f"\n{'='*80}")
    print(f"COMMAND: {cmd}")
    print('='*80)

    # Send command
    tn.write(cmd.encode('ascii') + b"\r\n")

    # Wait a bit for response
    time.sleep(2)

    # Read response
    response = tn.read_very_eager().decode('utf-8')

    print("RAW RESPONSE:")
    print(repr(response))  # Show with escape characters
    print("\nFORMATTED:")
    print(response)
    print()

tn.write(b"exit\r\n")
tn.close()

print("\n" + "="*80)
print("Done! Use these responses to update the regex patterns.")
print("="*80)
