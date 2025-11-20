#!/usr/bin/env python3
"""
Comprehensive telnet command tester for 7D2D server
Tests all bot commands and validates regex patterns
"""
import telnetlib
import json
import time
import re
from pathlib import Path

# Load config
config_path = Path(__file__).parent / 'bot' / 'options' / 'module_telnet.json'
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    # Manual config if file doesn't exist
    config = {
        'host': input('Server IP: '),
        'port': int(input('Server Port: ')),
        'password': input('Telnet Password: ')
    }

print(f"\n{'='*80}")
print(f"Connecting to {config['host']}:{config['port']}")
print(f"{'='*80}\n")

# Connect
tn = telnetlib.Telnet(config['host'], config['port'], timeout=10)

# Wait for password prompt
time.sleep(0.5)
output = tn.read_very_eager().decode('ascii', errors='ignore')
print('[CONNECTION] Established')

# Send password
tn.write((config['password'] + '\n').encode('ascii'))
time.sleep(0.5)
output = tn.read_very_eager().decode('ascii', errors='ignore')
print('[AUTH] Authenticated\n')

# Test commands with their expected regex patterns
commands = [
    {
        'name': 'admin list',
        'command': 'admin list',
        'regex': r"Executing\scommand\s\'admin list\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
                 r"(?P<raw_adminlist>(?:Defined User Permissions\:.*?(?=Defined Group Permissions|$)))",
        'wait': 1,
        'description': 'Get admin list'
    },
    {
        'name': 'lp (getplayers)',
        'command': 'lp',
        'regex': r"Executing\scommand\s\'lp\'\sby\sTelnet\sfrom\s"
                 r"(?P<called_by>.*?)\r?\n"
                 r"(?P<raw_playerdata>[\s\S]*?)"
                 r"Total\sof\s(?P<player_count>\d{1,2})\sin\sthe\sgame",
        'wait': 1,
        'description': 'Get player list'
    },
    {
        'name': 'gettime',
        'command': 'gettime',
        'regex': r"Day\s(?P<day>\d{1,5}),\s(?P<hour>\d{1,2}):(?P<minute>\d{1,2})",
        'wait': 1,
        'description': 'Get game time'
    },
    {
        'name': 'listents (getentities)',
        'command': 'listents',
        'regex': r"Executing\scommand\s\'listents\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
                 r"(?P<raw_entity_data>[\s\S]*?)"
                 r"Total\sof\s(?P<entity_count>\d{1,3})\sin\sthe\sgame",
        'wait': 1,
        'description': 'Get entity list'
    },
    {
        'name': 'getgamepref',
        'command': 'getgamepref',
        'regex': r"Executing\scommand\s\'getgamepref\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
                 r"(?P<raw_gameprefs>(?:GamePref\..*?\r?\n)+)",
        'wait': 2,
        'description': 'Get game preferences'
    },
    {
        'name': 'getgamestat',
        'command': 'getgamestat',
        'regex': r"Executing\scommand\s\'getgamestat\'\sby\sTelnet\sfrom\s(?P<called_by>.*?)\r?\n"
                 r"(?P<raw_gamestats>(?:GameStat\..*?\r?\n)+)",
        'wait': 2,
        'description': 'Get game statistics'
    },
    {
        'name': 'version',
        'command': 'version',
        'regex': None,  # Just check raw output
        'wait': 1,
        'description': 'Get server version'
    },
    {
        'name': 'help',
        'command': 'help',
        'regex': None,  # Just check raw output
        'wait': 2,
        'description': 'Get available commands'
    }
]

results = {
    'passed': [],
    'failed': [],
    'no_regex': []
}

for test in commands:
    print(f"\n{'='*80}")
    print(f"TEST: {test['name']}")
    print(f"Description: {test['description']}")
    print(f"{'='*80}")

    # Send command
    print(f"\n>>> Sending: {test['command']}")
    tn.write((test['command'] + '\n').encode('ascii'))

    # Wait for response
    time.sleep(test['wait'])
    output = tn.read_very_eager().decode('ascii', errors='ignore')

    # Show raw output
    print(f"\n--- RAW OUTPUT (repr) ---")
    print(repr(output))
    print(f"\n--- RAW OUTPUT (formatted) ---")
    print(output)

    # Test regex if provided
    if test['regex']:
        print(f"\n--- REGEX TEST ---")
        print(f"Pattern: {test['regex'][:100]}...")

        matches = list(re.finditer(test['regex'], output, re.MULTILINE | re.DOTALL))

        if matches:
            print(f"✓ REGEX MATCHED! ({len(matches)} match(es))")
            for i, match in enumerate(matches, 1):
                print(f"\nMatch {i}:")
                for group_name, group_value in match.groupdict().items():
                    value_preview = repr(group_value)[:100]
                    print(f"  {group_name}: {value_preview}")
            results['passed'].append(test['name'])
        else:
            print(f"✗ REGEX FAILED - NO MATCH!")
            results['failed'].append(test['name'])
    else:
        print(f"\n--- NO REGEX TEST (raw output only) ---")
        results['no_regex'].append(test['name'])

    print(f"\n{'='*80}\n")
    time.sleep(0.5)  # Small delay between commands

# Close connection
tn.close()

# Summary
print(f"\n\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"✓ Passed:  {len(results['passed'])} - {', '.join(results['passed']) if results['passed'] else 'none'}")
print(f"✗ Failed:  {len(results['failed'])} - {', '.join(results['failed']) if results['failed'] else 'none'}")
print(f"- No test: {len(results['no_regex'])} - {', '.join(results['no_regex']) if results['no_regex'] else 'none'}")
print(f"{'='*80}\n")

if results['failed']:
    print("⚠️  SOME TESTS FAILED - Regex patterns need to be fixed!")
    exit(1)
else:
    print("✓ All regex tests passed!")
    exit(0)
