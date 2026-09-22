"""Contrato de modelado V3."""

CLASES = [
    "No Tóxico",
    "Lenguaje Ofensivo",
    "Discurso de Odio",
    "Amenazas/Violencia",
]

MAX_LEN = 128
TEXT_COLUMN = "texto_modelo"
DEFAULT_SEED = 42
DEFAULT_MODEL = "pysentimiento/robertuito-base-cased"

REFERENCE_TEST_F1_MACRO = 0.8499
REFERENCE_METRIC_TOLERANCE = 0.01

# SHA-256 de los splits congelados (rama v3 @ 95d3ba6).
REFERENCE_SHA256: dict[str, str] = {
    "train.csv": "e755a91814ab4f3bf29bd3aaa38806bd7712fb4c45cf90b78612ffc4054b9453",
    "val.csv": "33d89bf3686c302e9f8896abe68f7d4fc2468690abcd5142c538e9934bb1a4c3",
    "test.csv": "3239eb4ca59720e1a7aaa574ad38bad53db18c54f5e1424b381f68d1d0b2f1d6",
    "test_adversarial.csv": "9b9e428105c66ece32b3935ea89ce5dbaafe80c6133fce694fa221fa8f830a46",
    "lexicon_emojis.csv": "8ab9bf7afbbb72929d2c1c42844e22814a85b3cce9691c053fa63a4a1553a732",
}

EXPECTED_ROWS = {"val.csv": 459, "test.csv": 460}
