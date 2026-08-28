"""Tests for Study Material File Validation and Sanitization (Phases 1-3, 20)."""

import io
import unittest

import fitz  # PyMuPDF

from src.academic_rag.ingestion.validator import sanitize_filename, validate_pdf_file


def _create_sample_pdf_bytes(text: str = "Sample valid scientific textbook content.") -> bytes:
    """Helper to create valid PDF bytes in-memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def _create_scanned_pdf_bytes() -> bytes:
    """Helper to create a PDF with an image/empty page (no extractable text)."""
    doc = fitz.open()
    doc.new_page()  # Blank page with 0 text
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


class TestStudyMaterialValidation(unittest.TestCase):
    """Validation test suite for uploaded PDF study material."""

    def test_sanitize_filename(self):
        """Test sanitization of potentially unsafe or weird filenames."""
        self.assertEqual(sanitize_filename("valid_notes.pdf"), "valid_notes.pdf")
        self.assertEqual(
            sanitize_filename("../../etc/passwd.pdf"), "passwd.pdf"
        )
        self.assertEqual(
            sanitize_filename("Physics Reference & Notes (Class 10)!.pdf"),
            "Physics Reference _ Notes (Class 10)_.pdf",
        )
        self.assertEqual(sanitize_filename(""), "uploaded_material.pdf")

    def test_valid_text_pdf_accepted(self):
        """Test that standard valid text PDF is accepted."""
        content = (
            "Chapter 12: Electricity. Ohm's Law states that electric current is proportional "
            "to potential difference V = IR at constant temperature."
        )
        pdf_bytes = _create_sample_pdf_bytes(content)
        result = validate_pdf_file(pdf_bytes, "Physics_Notes.pdf")

        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.detected_pages, 1)
        self.assertFalse(result.is_scanned_pdf)
        self.assertGreater(result.file_size_bytes, 0)

    def test_non_pdf_rejected(self):
        """Test rejection of non-PDF file formats."""
        fake_data = b"This is a text file"
        result_txt = validate_pdf_file(fake_data, "notes.txt")
        self.assertFalse(result_txt.is_valid)
        self.assertIn("Unsupported file type", result_txt.error_message)

        result_docx = validate_pdf_file(fake_data, "document.docx")
        self.assertFalse(result_docx.is_valid)

        result_png = validate_pdf_file(fake_data, "diagram.png")
        self.assertFalse(result_png.is_valid)

    def test_empty_file_rejected(self):
        """Test rejection of zero-byte files."""
        result = validate_pdf_file(b"", "empty.pdf")
        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.error_message.lower())

    def test_oversized_file_rejected(self):
        """Test rejection of files exceeding max upload size."""
        # 100 bytes data tested with max_size_bytes=50
        fake_data = b"X" * 100
        result = validate_pdf_file(fake_data, "large.pdf", max_size_bytes=50)
        self.assertFalse(result.is_valid)
        self.assertIn("exceeds maximum allowed size", result.error_message)

    def test_corrupted_pdf_rejected(self):
        """Test rejection of corrupted/invalid PDF streams."""
        corrupt_data = b"%PDF-1.4 Fake header but definitely corrupted content inside"
        result = validate_pdf_file(corrupt_data, "corrupt.pdf")
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid or corrupted PDF", result.error_message)

    def test_scanned_zero_text_pdf_detected(self):
        """Test detection and polite rejection of scanned/image-only PDFs (OCR required)."""
        scanned_bytes = _create_scanned_pdf_bytes()
        result = validate_pdf_file(scanned_bytes, "scanned_book.pdf", min_chars_per_page=20)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.is_scanned_pdf)
        self.assertIn("OCR required", result.error_message)


if __name__ == "__main__":
    unittest.main()
