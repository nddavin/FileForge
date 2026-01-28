from file_processor.services.extractor import Extractor


def test_extractor_initialization():
    extractor = Extractor()
    assert "email" in extractor.patterns
    assert "phone" in extractor.patterns


def test_extract_emails():
    extractor = Extractor()
    text = "Contact us at test@example.com or support@company.org"

    result = extractor.extract_text(text)
    assert "emails" in result
    assert "test@example.com" in result["emails"]
    assert "support@company.org" in result["emails"]


def test_extract_phones():
    extractor = Extractor()
    text = "Call 555-123-4567 or (555) 987-6543"

    result = extractor.extract_text(text)
    assert "phones" in result
    assert "555-123-4567" in result["phones"]


def test_extract_ssn():
    extractor = Extractor()
    text = "SSN: 123-45-6789"

    result = extractor.extract_text(text)
    assert "ssns" in result
    assert "123-45-6789" in result["ssns"]


def test_extract_credit_cards():
    extractor = Extractor()
    text = "Card: 1234-5678-9012-3456"

    result = extractor.extract_text(text)
    assert "credit_cards" in result
    assert "1234-5678-9012-3456" in result["credit_cards"]


def test_word_and_character_count():
    extractor = Extractor()
    text = "This is a test document."

    result = extractor.extract_text(text)
    assert result["word_count"] == 5
    assert result["character_count"] == len(text)


def test_extract_metadata_document():
    extractor = Extractor()
    file_info = {"type": "document", "size": 5000, "extension": "pdf"}

    result = extractor.extract_metadata(file_info)
    assert "extracted_data" in result
    assert result["extracted_data"]["has_text"] is True


def test_extract_metadata_image():
    extractor = Extractor()
    file_info = {"type": "image", "width": 1920, "height": 1080, "extension": "jpg"}

    result = extractor.extract_metadata(file_info)
    assert "extracted_data" in result
    assert "resolution" in result["extracted_data"]
