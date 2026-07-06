from pathlib import Path

from rdflib import Graph


def import_file(input_file: str, input_format: str | None = None) -> str:
    """Parse an SPDX file and return its contents serialized as Turtle."""
    path = Path(input_file)

    if not path.is_file():
        msg = f"File not found: {input_file}"
        raise FileNotFoundError(msg)

    if input_format is None:
        input_format = detect_format(path)

    # Create a graph for transforming data to turtle
    g = Graph()
    g.parse(path, format=input_format)
    ttl_data = g.serialize(format="turtle")

    # TODO: After turning data into turtle the function will send them into backend via triplestore library

    return ttl_data


def detect_format(path: Path) -> str:
    """Detect the RDF input format from the file extension."""
    suffixes = path.suffixes

    if path.suffix == ".jsonld" or suffixes[-2:] in [[".spdx", ".json"], [".spdx3", ".json"]]:
        return "json-ld"

    # Let's start only with json-ld firstly
    # if path.suffix in {".ttl", ".turtle"}:
    #     return "turtle"

    # if path.suffix == ".nt":
    #     return "nt"

    # if path.suffix in {".rdf", ".xml"}:
    #     return "xml"

    msg = f"Unsupported input format: {path.suffix}"
    raise ValueError(msg)
