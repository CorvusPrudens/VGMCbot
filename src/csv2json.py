
import json

ledger = {}

with open('bank.csv', 'r') as file:
    for line in file:
        tokens = line.replace('\n', '').split(',')
        if len(line.replace('\n', '')) > 0:
            ledger[int(tokens[0])] = float(tokens[1])

with open('ledger.json', 'w') as file:
    json.dump(ledger, file, indent=2)
