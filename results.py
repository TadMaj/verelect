import pandas as pd
import os
import json

main_data = pd.read_csv("./csv/repre2023.csv")
source = "./ocr_data/results"
main_data.insert(6, "Detected", 0)
main_data.insert(7, "Status", pd.NA)
main_data = main_data[main_data["Status"].isna()]

def results():
    for data in os.listdir(source):
        data_path = os.path.join(source, data)
        json_data = json.load(open(data_path))
        
        data = data.split(".")[0]
        if data.count("-") > 3:
            m = data.split("-")[0][5:] + "-" + data.split("-")[1] + "-" + data.split("-")[2]
            data = data[len(data.split("-")[0])+2+len(data.split("-")[1]):]
        elif data.count("-") > 2:
            m = data.split("-")[0][5:] + "-" + data.split("-")[1]
            data = data[len(data.split("-")[0])+1:]

        else:
            m = data.split("-")[0][5:]
        ps = int(data.split("-")[1])
        party = int(data.split("-")[2][5:])
        
        print("Found results: ", len(json_data.items()))

        for (key, value) in json_data.items():
            if value == "":
                value = 0
            if key == "":
                continue
            #remove non digits from key
            key = ''.join(filter(str.isdigit, key))
            #write status
            main_data['Detected'] = main_data['Detected'].mask((((main_data['Municipality'] == m) & (main_data['Stembureau'] == ps)) & (main_data["Party"] == party)) & (main_data["Candidate"] == int(key)), value)

    main_data['Status'] = main_data.apply(lambda row: "Matches" if str(row['Total']) == str(row['Detected']) else "Missmatch", axis=1)
    main_data.to_csv("./output.csv", index=False)