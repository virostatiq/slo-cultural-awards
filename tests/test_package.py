from kulturne_nagrade import DATA_DIR


def test_data_dir_exists():
    assert DATA_DIR.is_dir()
