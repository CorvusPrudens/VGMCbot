
import json

with open("curves.json", "r") as file:
    data = json.load(file)

with open("locations.json", "r") as file:
    outdata = json.load(file)

# for key in data:
#     data[key] = [round(x, 4) for x in data[key]]

for key in outdata:
    outdata[key]['curve'] = data[key]


with open("locations.json", "w") as file:
    file.write('{\n')
    for idx, key in enumerate(outdata):
        file.write('  "{}": {{\n'.format(key))
        for nestedIdx, nestedKey in enumerate(outdata[key]):
            file.write('    "{}": '.format(nestedKey))
            file.write(json.dumps(outdata[key][nestedKey], sort_keys=True))
            if (nestedIdx < len(outdata[key]) - 1):
                file.write(',\n')
        file.write('\n  }')
        if (idx < len(outdata) - 1):
            file.write(',\n')
    file.write('\n}')
