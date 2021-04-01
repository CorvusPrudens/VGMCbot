import json

with open('players.json', 'r') as file:
    data = json.load(file)

for key in data:
    if 'fishing' in data[key]['games']:
        try:
            stats = data[key]['fishing']['stats']
        except KeyError:
            data[key]['fishing']['stats'] = {}

with open('players_patched.json', 'w') as file:
    json.dump(data, file, indent=2)

print('patched!')
