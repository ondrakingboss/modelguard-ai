import asyncio
from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi import HTTPException, UploadFile
from openpyxl import Workbook

import main


def _upload(name: str, content: bytes) -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(content))


def _xlsx_bytes() -> bytes:
    output = BytesIO()
    workbook = Workbook()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def _incomplete_xlsx_bytes() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("unrelated.txt", "not a workbook")
    return output.getvalue()


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("company.pdf", b"%PDF-1.7 test"),
        ("model.xlsx", _xlsx_bytes()),
    ],
)
def test_valid_upload_signatures_pass_and_reset_stream(
    name: str, content: bytes,
) -> None:
    upload = _upload(name, content)

    main._validate_upload(upload, f".{name.rsplit('.', 1)[1]}")

    assert upload.file.tell() == 0


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("renamed.pdf", b"plain text"),
        ("renamed.xlsx", b"plain text"),
        ("incomplete.xlsx", _incomplete_xlsx_bytes()),
    ],
)
def test_invalid_upload_signatures_are_rejected(name: str, content: bytes) -> None:
    upload = _upload(name, content)

    with pytest.raises(HTTPException) as exc_info:
        main._validate_upload(upload, f".{name.rsplit('.', 1)[1]}")

    assert exc_info.value.status_code == 400
    assert "file contents" in exc_info.value.detail
    assert upload.file.tell() == 0


def test_renamed_pdf_never_reaches_parser_and_is_closed(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_text",
        lambda _path: pytest.fail("invalid PDF reached the parser"),
    )
    upload = _upload("renamed.pdf", b"plain text")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.analyze_company(upload))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []
    assert upload.file.closed


def test_invalid_second_pdf_closes_both_comparison_uploads(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_text",
        lambda _path: pytest.fail("invalid comparison PDF reached the parser"),
    )
    left = _upload("left.pdf", b"%PDF-1.7 valid")
    right = _upload("right.pdf", b"plain text")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.company_diff(left, right))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []
    assert left.file.closed
    assert right.file.closed


def test_renamed_xlsx_never_reaches_parser_and_is_closed(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "parse_excel_file",
        lambda _path: pytest.fail("invalid XLSX reached the parser"),
    )
    upload = _upload("renamed.xlsx", b"plain text")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.upload(upload))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []
    assert upload.file.closed
