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
    dogs_data: List,
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


def refine_dataframe(
    df: pd.DataFrame,
    column_mapping: Dict,
    d_translation: Dict,
) -> pd.DataFrame:
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

    df = df.replace(d_translation)

    return df


def transform_raw_data():
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
        "Macskákkal barátságos",
        "Szívféregteszt",
    ]

    column_translation = {
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
        "szuka kutyákkal barátságos": "friendly_with_female_dogs",
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

    color_translation = {
        "barna": "brown",
        "világosbarna": "light brown",
        "fekete-cser": "black-tan",
        "fekete": "black",
        "szálkás": "wire-haired",
        "barna-fehér": "brown-white",
        "fekete-fehér": "black-white",
        "trikolor": "tricolor",
        "fekete-barna": "black-brown",
        "ordas": "wolf-gray",
        "szürke": "gray",
        "rövid": "short",
        "fehér": "white",
        "közepes": "medium",
        "pöttyös": "spotted",
        "só-bors": "salt-and-pepper",
        "hosszú": "long",
        "vörös-fehér": "red-white",
        "rajzos": "patterned",
        "vörös": "red",
        "foltos": "patchy",
        "fekete-szürke": "black-gray",
        "csíkos": "striped",
    }

    coat_translation = {
        "rövid": "short",
        "negatív": "negative",
        "szálkás": "wire-haired",
        "hosszú": "long",
        "közepes": "medium",
        "pozitív": "positive",
        "zsinóros": "corded",
    }

    living_environment_translation = {
        "lakásban": "in an apartment",
        "lakásban és kertben": "in an apartment and garden",
    }

    size_translation = {
        "kicsi (5-10 kg)": "small (5-10 kg)",
        "közepes (10-25 kg)": "medium (10-25 kg)",
        "nagy (25-40 kg)": "large (25-40 kg)",
        "apró (5 kg-ig)": "tiny (up to 5 kg)",
    }

    common_words_translation = {
        "gazdira talált": "found_owner",
        "gazdit keres": "looking_for_owner",
        "kan": "male",
        "szuka": "female",
        "igen": "yes",
        "nem": "no",
        "nan": None,
        "negatív": "negative",
        "pozitív": "positive",
    }

    global_translations = {
        **common_words_translation,
        **breed_translation,
        **color_translation,
        **coat_translation,
        **living_environment_translation,
        **size_translation,
    }

    with Path(json_path).open("r", encoding="utf-8") as f:
        dogs_data = json.load(f)

    if not isinstance(dogs_data, list):
        raise ValueError("Expected a list of dog entries in the JSON file.")

    cleaned_delimiters = clean_delimiters(delimiters)
    delimiter_regex = compile_regex(cleaned_delimiters)

    cleaned_dog_data = process_dog_data(
        dogs_data,
        delimiter_regex,
        target_fields,
        to_keep,
    )

    df = pd.DataFrame(cleaned_dog_data)
    df = refine_dataframe(df, column_translation, global_translations)

    df.to_json("scraped_data/dogs_data_clean.json", orient="records", force_ascii=False)


if __name__ == "__main__":
    """
    Main execution block for reading raw dog data from JSON, cleaning and normalizing
    fields (e.g., breed, color, age), and saving the processed results back to JSON.
    Specifically, it:
      1. Reads raw dog data from 'scraped_data/dogs_data_raw.json'.
      2. Cleans delimiters and compiles a regex for splitting text into fields.
      3. Processes each dog's data, applying table parsing and field translations.
      4. Converts the cleaned records into a pandas DataFrame, refines column names,
         and normalizes values (e.g., converting 'hónapos' to months).
      5. Writes the final cleaned dataset to 'scraped_data/dogs_data_clean.json'.
    """
    transform_raw_data()
