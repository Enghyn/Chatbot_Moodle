def test_package_importable():
    import bot_moodle

    assert bot_moodle.__name__ == "bot_moodle"
