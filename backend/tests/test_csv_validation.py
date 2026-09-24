import io

import pytest
from fastapi import HTTPException, UploadFile

from main import MAX_ROWS, _normalize_customer_id_column, _read_and_validate_csv


def _upload(text: str, filename: str = "test.csv") -> UploadFile:
    return UploadFile(io.BytesIO(text.encode("utf-8")), filename=filename)


async def test_accepts_a_well_formed_csv():
    csv_text = "customer_id,total_spend\nC001,100\nC002,200\n"
    df, clean_text = await _read_and_validate_csv(_upload(csv_text))
    assert list(df["customer_id"]) == ["C001", "C002"]
    assert "customer_id" in clean_text


async def test_rejects_non_csv_filename():
    with pytest.raises(HTTPException) as exc:
        await _read_and_validate_csv(_upload("a,b\n1,2\n", filename="test.txt"))
    assert exc.value.status_code == 400


async def test_rejects_empty_file():
    with pytest.raises(HTTPException) as exc:
        await _read_and_validate_csv(_upload(""))
    assert exc.value.status_code == 400


async def test_rejects_too_many_rows():
    header = "customer_id,total_spend\n"
    rows = "\n".join(f"C{i},{i}" for i in range(MAX_ROWS + 5))
    with pytest.raises(HTTPException) as exc:
        await _read_and_validate_csv(_upload(header + rows + "\n"))
    assert exc.value.status_code == 400


async def test_rejects_file_with_no_data_rows():
    with pytest.raises(HTTPException) as exc:
        await _read_and_validate_csv(_upload("customer_id,total_spend\n"))
    assert exc.value.status_code == 400


def test_normalizes_existing_id_column_regardless_of_case():
    import pandas as pd

    df = pd.DataFrame({"Email": ["a@x.com", "b@x.com"], "spend": [1, 2]})
    normalized = _normalize_customer_id_column(df)
    assert list(normalized.columns)[0] == "customer_id"
    assert list(normalized["customer_id"]) == ["a@x.com", "b@x.com"]


def test_synthesizes_id_column_when_none_present():
    import pandas as pd

    df = pd.DataFrame({"spend": [1, 2, 3]})
    normalized = _normalize_customer_id_column(df)
    assert list(normalized["customer_id"]) == ["row_1", "row_2", "row_3"]
