from file_processor.services.sorter import Sorter


def test_sorter_initialization():
    sorter = Sorter()
    assert len(sorter.default_rules) == 3
    assert sorter.default_rules[0]["name"] == "Documents"


def test_sort_document_file():
    sorter = Sorter()
    file_info = {"extension": "pdf", "size": 1024}

    category = sorter.sort_file(file_info)
    assert category == "documents"


def test_sort_image_file():
    sorter = Sorter()
    file_info = {"extension": "jpg", "size": 2048}

    category = sorter.sort_file(file_info)
    assert category == "images"


def test_sort_video_file():
    sorter = Sorter()
    file_info = {"extension": "mp4", "size": 1024000}

    category = sorter.sort_file(file_info)
    assert category == "videos"


def test_sort_misc_file():
    sorter = Sorter()
    file_info = {"extension": "xyz", "size": 512}

    category = sorter.sort_file(file_info)
    assert category == "misc"


def test_custom_rule():
    sorter = Sorter()
    custom_rules = [
        {
            "name": "Large Files",
            "condition": {"size": lambda x: x > 1000},
            "category": "large",
        }
    ]

    file_info = {"extension": "txt", "size": 2000}
    category = sorter.sort_file(file_info, custom_rules)
    assert category == "large"


def test_create_rule():
    sorter = Sorter()
    rule = sorter.create_rule("Test Rule", {"extension": ["test"]}, "test_category")

    assert rule["name"] == "Test Rule"
    assert rule["condition"] == {"extension": ["test"]}
    assert rule["category"] == "test_category"
