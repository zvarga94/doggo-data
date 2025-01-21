import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd

d_columns = {
    "státusz": "status",  # Status
    "befogadás dátuma": "admission_date",  # Admission date
    "elvihető (előreláthatóan)": "adoptable_date",  # Expected adoptable date
    "kutya fajtája": "breed",  # Dog breed
    "kora": "age",  # Age
    "ivar": "gender",  # Gender (male/female)
    "szín": "color",  # Color
    "szőr": "coat",  # Coat (type/length)
    "javasolt tartás": "recommended_environment",  # Recommended environment (e.g., indoor/outdoor)
    "embereket szereti": "people_friendly",  # Friendly with people
    "looking_for_owner": "looking_for_owner",  # Actively seeking an owner
    "found_owner": "found_owner",  # Has found an owner
    "uid": "uid",  # Unique identifier
    "page_url": "page_url",  # Page URL
    "downloaded_urls": "downloaded_urls",  # Downloaded image URLs
    "description": "description",  # Description of the dog
    "méret": "size",  # Size
    "szívféregteszt": "heartworm_test",  # Heartworm test result
}

if __name__ == "__main__":
    path_json = Path("scraped_data/dogs_data_raw.json")

    with path_json.open("r", encoding="utf-8") as f:
        dogs_data = json.load(f)

    df = pd.DataFrame(dogs_data)

    # separators = ["Státusz", "Befogadás dátuma", "Elvihető(előreláthatóan)", "Kutya fajtája", "Kora", "Ivar", "Szín", "Szor", "Javasolt tartás", "Embereket szereti"]
    target_fields = ["data", "trait", "behavior"]

    l_clean = []

    to_keep = ["uid", "page_url", "downloaded_urls", "description"]

    delimiters = [
        "Státusz",
        "Befogadás dátuma",
        "Elvihető (előreláthatóan)",
        "Kutya fajtája",
        "Kora",
        "Ivar",
        "Méret",
        "Szín",
        "Szőr",
        "Javasolt tartás",
        "Embereket szereti",
        "Szívféregteszt",
    ]
    # pattern = "|".join(map(re.escape, keys))
    delimiters = [d.strip().lower() for d in delimiters]
    # pattern = f"\\b({'|'.join(map(re.escape, delimiters))})\\b"
    pattern = f"({'|'.join(map(re.escape, delimiters))})"
    for d in dogs_data:
        d__ = dict()
        for t in target_fields:
            if d[t] is not None:
                split_result = re.split(pattern, d[t].lower())
                values = [
                    s.strip()
                    for i, s in enumerate(split_result)
                    if i % 2 == 0 and s.strip()
                ]  # Non-delimiter parts
                delimiters = [
                    s for i, s in enumerate(split_result) if i % 2 == 1 and s.strip()
                ]  # Delimiters

                _d = {k: v for k, v in zip(delimiters, values)}
                d__.update(_d)

        s = dogs_data[0]["table"].split("\n")
        s = s[1:]
        s = [
            i.replace("Gazdit keres", "looking_for_owner").replace(
                "Gazdira talált", "found_owner"
            )
            for i in s
        ]
        s = [x.split(" ") for x in s]
        d2 = {i[1]: i[0] for i in s}

        d__.update(d2)
        d__.update({k: d[k] for k in to_keep})

        if d__["kutya fajtája"] == "husky":
            print

        l_clean.append(deepcopy(d__))

    print
    df = pd.DataFrame(l_clean)

    df = df.rename(columns=d_columns)

    print(df.columns)

    df["adoptable_date"] = df["adoptable_date"].str.split("után bármikor").str[0]
    df["age"] = df["age"].apply(
        lambda x: (
            int(re.findall(r"\b\d+\b", x)[0]) / 12
            if "hónapos" in x
            else int(re.findall(r"\b\d+\b", x)[0])
        )
    )

    print(df.head())
    # for separator in separators:
    #     df[separator] = df["data"].apply(lambda x: x.split(separator)[1].split("\n")[0].strip())
