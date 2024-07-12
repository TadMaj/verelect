import sqlite3
import sys
import collections
import csv

municipality_missmatch = []

def open_database(name):
    conn = sqlite3.connect(name)
    return conn
def close_database(conn):
    conn.close()

def generate_510b(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT kieskring, gemeente, stembureauId, affid, candid, votes FROM rucandvotecounts WHERE formid = '510b'")
    data = cursor.fetchall()
    kieskring = collections.defaultdict(list)

    pbar = tqdm(data)
    pbar.set_description("Processing 510b kieskring data")
    for k, g, s, a, c, v in pbar:
        kieskring[k].append((g, s, a, c, v))

    pbar = tqdm(kieskring.keys())
    pbar.set_description("Processing 510b gemeente data")
    for k in pbar:
        kieskring_data = kieskring[k]
        kieskring[k] = collections.defaultdict(list)
        for data in kieskring_data:
            g, s, a, c, v = data
            kieskring[k][g].append((s, a, c, v))

    pbar = tqdm(kieskring.keys())
    pbar.set_description("Processing 510b stembureau data")
    for k in pbar:
        for g in kieskring[k].keys():
            gemeente_data = kieskring[k][g]
            kieskring[k][g] = collections.defaultdict(list)
            for data in gemeente_data:
                s, a, c, v = data
                kieskring[k][g][s].append((a, c, v)) 

    pbar = tqdm(kieskring.keys())
    pbar.set_description("Processing 510b vote data")
    for k in pbar:
        for g in kieskring[k].keys():
            for s in kieskring[k][g].keys():
                stenbureau_data = kieskring[k][g][s]
                kieskring[k][g][s] = collections.defaultdict(int)
                for data in stenbureau_data:
                    a, c, v = data
                    kieskring[k][g][s][(a, c)] += v
        
    return kieskring

def generate_510c(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT kieskring, gemeente, affid, candid, votes FROM rucandvotecounts WHERE formid = '510c'")
    data = cursor.fetchall()

    kieskring = collections.defaultdict(list)

    pbar = tqdm(data)
    pbar.set_description("Processing 510c kieskring data")
    for k, g, a, c, v in pbar:
        kieskring[k].append((g, a, c, v))

    pbar = tqdm(kieskring.keys())
    pbar.set_description("Processing 510c gemeente data")
    for k in pbar:
        kieskring_data = kieskring[k]
        kieskring[k] = collections.defaultdict(list)
        for data in kieskring_data:
            g, a, c, v = data
            kieskring[k][g].append((a, c, v))

    pbar = tqdm(kieskring.keys())
    pbar.set_description("Processing 510c vote data")
    for k in pbar:
        for g in kieskring[k].keys():
                stenbureau_data = kieskring[k][g]
                kieskring[k][g] = collections.defaultdict(int)
                for data in stenbureau_data:
                    a, c, v = data
                    kieskring[k][g][(a, c)] = v
    return kieskring

def generate_510c_csv(error_data):
    if (len(error_data) == 0) and (len(municipality_missmatch) == 0):
        return
    with open('errors_510c.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        field = ["District", "Municipality", "Affiliation, Candidate", "510c value", "510b calculated value"]
        writer.writerow(field)
        for data in error_data:
            writer.writerow(data)
    with open('municipality_missmatch.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        field = ["510b", "510c"]
        writer.writerow(field)
        for data in municipality_missmatch:
            writer.writerow(data)

def validate_510c(election_510b, election_510c):
    error_data = []
    errors = 0
    print("Validating 510c")
    assert election_510b.keys() == election_510c.keys()
    print("Kieskring keys match")
    for k in election_510b.keys():
        if (election_510b[k].keys() != election_510c[k].keys()):
            municipality_missmatch.append((",".join(election_510b[k].keys()), ",".join(election_510c[k].keys())))
    print("Gemeente keys match")

    pbar = tqdm(election_510b.keys())
    pbar.set_description("Validating 510c results")
    for k in pbar:
        for g in election_510b[k].keys():
            expected_values = election_510c[k][g]
            actual_values = election_510b[k][g]
            calculated_values = collections.defaultdict(int)
            for key in actual_values.keys():
                data = actual_values[key]
                for d in data.keys():
                    calculated_values[d] += data[d]
            for key in expected_values.keys():
                if (expected_values[key] != calculated_values[key]):
                    print("510c {} {} {} results do not match".format(k, g, key))
                    print("Expected: ", expected_values[key])
                    print("Calculated: ", calculated_values[key])
                    errors = errors + 1
                    error_data.append((k, g, key, expected_values[key], calculated_values[key]))
    print("errors: ", errors)
    generate_510c_csv(error_data)
                
db = open_database(sys.argv[1])
election_510b = generate_510b(db)
election_510c = generate_510c(db)

validate_510c(election_510b, election_510c)

df = pd.DataFrame(columns=["District", "Municipality", "Polling Station", "Affiliation", "Candidate", "Status", "Votes"])

for district in election_510b:
    for municipality in election_510b[district]:
        for polling_station in election_510b[district][municipality]:
            for (affiliation, candidate) in election_510b[district][municipality][polling_station]:
                new_row = pd.DataFrame({"District": district, "Municipality": municipality, "Polling Station": polling_station, "Affiliation": affiliation, "Candidate": candidate, "Status": "NA", "Votes": election_510b[district][municipality][polling_station][(affiliation, candidate)]}, index=[0])
                df = pd.concat([df, new_row], ignore_index=True)

df.to_csv(sys.argv[2], index=False)

close_database(db)