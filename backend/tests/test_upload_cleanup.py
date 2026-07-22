import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

import main


def _pdf(name: str, content: bytes = b"%PDF-1.4 test") -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(content))


def _stub_pdf_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "extract_text", lambda _path: "text")
    monkeypatch.setattr(main, "extract_tables", lambda _path: [])
    monkeypatch.setattr(main, "extract_financial_data", lambda _path: {})


def test_analyze_company_removes_temporary_pdf_after_success(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    _stub_pdf_parsing(monkeypatch)
    monkeypatch.setattr(main, "build_company_profile", lambda _parsed: {"ok": True})
    upload = _pdf("company.pdf")

    result = asyncio.run(main.analyze_company(upload))

    assert result == {"ok": True}
    assert list(tmp_path.iterdir()) == []
    assert upload.file.closed


def test_analyze_company_removes_temporary_pdf_after_failure(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main, "extract_text", lambda _path: (_ for _ in ()).throw(ValueError("bad PDF"))
    )
    upload = _pdf("broken.pdf")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.analyze_company(upload))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []
    assert upload.file.closed


def test_company_diff_removes_both_temporary_pdfs_after_success(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    _stub_pdf_parsing(monkeypatch)
    monkeypatch.setattr(main, "build_company_diff", lambda _left, _right: {"ok": True})
    left, right = _pdf("left.pdf"), _pdf("right.pdf")

    result = asyncio.run(main.company_diff(left, right))

    assert result == {"ok": True}
    assert list(tmp_path.iterdir()) == []
    assert left.file.closed
    assert right.file.closed


def test_company_diff_removes_both_temporary_pdfs_after_partial_failure(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    calls = iter(["left text", ValueError("bad right PDF")])

    def extract_text(_path):
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(main, "extract_text", extract_text)
    monkeypatch.setattr(main, "extract_tables", lambda _path: [])
    monkeypatch.setattr(main, "extract_financial_data", lambda _path: {})
    left, right = _pdf("left.pdf"), _pdf("right.pdf")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.company_diff(left, right))

    assert exc_info.value.status_code == 400
    assert list(tmp_path.iterdir()) == []
    assert left.file.closed
    assert right.file.closed


@pytest.mark.parametrize(
    ("content", "expected_status"),
    [
        (b"", 400),
        (b"x" * (main.MAX_UPLOAD_SIZE + 1), 413),
    ],
)
def test_analyze_company_rejects_invalid_pdf_size_before_parsing(
    content: bytes, expected_status: int, tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_text",
        lambda _path: pytest.fail("invalid PDF size reached the parser"),
    )
    upload = _pdf("company.pdf", content)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.analyze_company(upload))

    assert exc_info.value.status_code == expected_status
    assert list(tmp_path.iterdir()) == []
    assert upload.file.closed


@pytest.mark.parametrize(
    ("content", "expected_status"),
    [
        (b"", 400),
        (b"x" * (main.MAX_UPLOAD_SIZE + 1), 413),
    ],
)
def test_company_diff_rejects_invalid_pdf_size_and_closes_both_inputs(
    content: bytes, expected_status: int, tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_text",
        lambda _path: pytest.fail("invalid PDF size reached the parser"),
    )
    left, right = _pdf("left.pdf"), _pdf("right.pdf", content)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(main.company_diff(left, right))

    assert exc_info.value.status_code == expected_status
    assert list(tmp_path.iterdir()) == []
    assert left.file.closed
    assert right.file.closed
