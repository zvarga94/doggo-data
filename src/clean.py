import json
import re
from copy import deepcopy
from pathlib import Path
from typing import List, Tuple, Dict

import pandas as pd


def clean_delimiters(delimiters: List) -> List:
    return [delimiter.strip().lower() for delimiter in delimiters]


def compile_regex(delimiters: List) -> re.Pattern:
    delimiters = sorted(delimiters, key=len, reverse=True)
    escaped_delimiters = [re.escape(delimiter) for delimiter in delimiters]
    delimiter_pattern = r"(" + r"|".join(escaped_delimiters) + r")"
    return re.compile(delimiter_pattern, re.IGNORECASE)


def split_text_with_delimiters(text: str, regex) -> Tuple:
    text = text.replace("\n", " ").strip().lower()
    split_result = regex.split(text)
    values = [s.strip() for i, s in enumerate(split_result) if i % 2 == 0 and s.strip()]
    delimiters = [
        s.strip() for i, s in enumerate(split_result) if i % 2 == 1 and s.strip()
    ]
    return values, delimiters


def parse_table_data(table_data: str) -> Dict:
    rows = table_data.split("\n")[1:]
    rows = [
        row.replace("Gazdit keres", "looking_for_owner").replace(
            "Gazdira talált", "found_owner"
        )
        for row in rows
    ]
    return {row.split(" ")[1]: row.split(" ")[0] for row in rows if " " in row}


def process_dog_data(
    dogs_data: Dict,
    regex: re.Pattern,
    target_fields: List,
    to_keep: List,
) -> List:
    cleaned_data = []

    for dog in dogs_data:
        dog_cleaned = {}

        for field in target_fields:
            if dog.get(field):
                values, delimiters = split_text_with_delimiters(dog[field], regex)
                dog_cleaned.update({k: v for k, v in zip(delimiters, values)})

        if "table" in dog:
            dog_cleaned.update(parse_table_data(dog["table"]))

        dog_cleaned.update({key: dog[key] for key in to_keep if key in dog})

        cleaned_data.append(deepcopy(dog_cleaned))

    return cleaned_data


breed_translation = {
    "keverék": "mixed breed",
    "tacskó keverék": "dachshund mix",
    "német juhász keverék": "German shepherd mix",
    "beagle keverék": "beagle mix",
    "csivava keverék": "chihuahua mix",
    "malamut keverék": "malamute mix",
    "basset hound keverék": "basset hound mix",
    "akita keverék": "akita mix",
    "golden retriever keverék": "golden retriever mix",
    "leonbergi keverék": "Leonberger mix",
    "puli keverék": "puli mix",
    "labrador retriever keverék": "labrador retriever mix",
    "ónémet juhász keverék": "old German shepherd mix",
    "foxterrier keverék": "fox terrier mix",
    "husky keverék": "husky mix",
}


def translate_df(df: pd.DataFrame) -> pd.DataFrame:

    d_words = {
        "gazdira talált": "found_owner",
        "gazdit keres": "looking_for_owner",
        "kan": "male",
        "szuka": "female",
    }

    df.replace(d_words, inplace=True)

    return df


def refine_dataframe(df: pd.DataFrame, column_mapping: Dict) -> pd.DataFrame:
    df = df.rename(columns=column_mapping)

    if "adoptable_date" in df.columns:
        df["adoptable_date"] = df["adoptable_date"].str.split("után bármikor").str[0]

    if "age" in df.columns:
        df["age"] = df["age"].apply(
            lambda x: (
                (
                    int(re.findall(r"\b\d+\b", x)[0]) / 12
                    if "hónapos" in x
                    else int(re.findall(r"\b\d+\b", x)[0])
                )
                if isinstance(x, str) and re.search(r"\b\d+\b", x)
                else None
            )
        )

    df = translate_df(df)

    return df


if __name__ == "__main__":
    json_path = "scraped_data/dogs_data_raw.json"

    target_fields = ["data", "trait", "behavior"]

    to_keep = ["uid", "page_url", "downloaded_urls", "description"]

    delimiters = [
        "Státusz",
        "Befogadás dátuma",
        "Elvihető (előreláthatóan)",
        "Kutya fajtája",
        "Kora",
        "Ivar",
        "Ivartalanított",
        "Méret",
        "Szín",
        "Szőr",
        "Javasolt tartás",
        "Embereket szereti",
        "Gyerekeket szereti",
        "Kan kutyákkal barátságos",
        "Szuka kutyákkal barátságos",
        "Kan kutyákkal barátságos",
        "Macskákkal barátságos",
        "Szívféregteszt",
    ]

    column_mapping = {
        "státusz": "status",
        "befogadás dátuma": "admission_date",
        "elvihető (előreláthatóan)": "adoptable_date",
        "kutya fajtája": "breed",
        "kora": "age",
        "ivar": "gender",
        "ivartalanított": "neutered",
        "szín": "color",
        "szőr": "coat",
        "javasolt tartás": "recommended_environment",
        "embereket szereti": "people_friendly",
        "gyerekeket szereti": "child_friendly",
        "kan kutyákkal barátságos": "friendly_with_male_dogs",
        "szuka kutyákkal barátságos:": "friendly_with_female_dogs",
        "macskákkal barátságos": "friendly_with_cats",
        "looking_for_owner": "looking_for_owner",
        "found_owner": "found_owner",
        "uid": "uid",
        "page_url": "page_url",
        "downloaded_urls": "downloaded_urls",
        "description": "description",
        "méret": "size",
        "szívféregteszt": "heartworm_test",
    }

    with Path(json_path).open("r", encoding="utf-8") as f:
        dogs_data = json.load(f)

    cleaned_delimiters = clean_delimiters(delimiters)
    delimiter_regex = compile_regex(cleaned_delimiters)

    cleaned_dog_data = process_dog_data(
        dogs_data, delimiter_regex, target_fields, to_keep
    )

    final_df = pd.DataFrame(cleaned_dog_data)
    final_df = refine_dataframe(final_df, column_mapping)

    print(final_df.head())
