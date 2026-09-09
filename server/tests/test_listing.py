from app.catalog.listing import child_folder_name, child_folder_names


def test_child_folder_name_at_root() -> None:
    assert child_folder_name("Drums", "") == "Drums"
    assert child_folder_name("Drums/Kicks", "") == "Drums"
    assert child_folder_name("", "") is None


def test_child_folder_name_nested() -> None:
    assert child_folder_name("Drums/Kicks", "Drums") == "Kicks"
    assert child_folder_name("Drums/Kicks/sub", "Drums") == "Kicks"
    assert child_folder_name("Drums", "Drums") is None
    assert child_folder_name("Loops", "Drums") is None


def test_child_folder_names_are_unique_and_sorted() -> None:
    parents = ["Drums/Kicks", "Drums/Snares", "Drums/Kicks", "Loops/Foley"]
    assert child_folder_names(parents, "") == ["Drums", "Loops"]
    assert child_folder_names(parents, "Drums") == ["Kicks", "Snares"]
    assert child_folder_names(parents, "Loops") == ["Foley"]
    assert child_folder_names(parents, "Missing") == []
