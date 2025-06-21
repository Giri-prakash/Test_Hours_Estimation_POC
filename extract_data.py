import csv

transformer_id = input("Transformer ID: ")
transformer_row = None

with open('data/data.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        if transformer_id in row[0]:
            transformer_row = row
            break

transformer_specs = {
    'id': transformer_row[0],
    'mva': transformer_row[1],
    'bil': transformer_row[2],
    'yv/tv': transformer_row[3],
    'auto': transformer_row[4],
    'conservator': transformer_row[5]
}

for spec in transformer_specs:
    print(transformer_specs[spec])