from app.main import app


def test_app_starts_with_expected_title():
    expected_title = "Kai Mortgage Income Engine"

    actual_title = app.title

    assert actual_title == expected_title
