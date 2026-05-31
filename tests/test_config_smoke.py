import config


def test_join_key_is_composite():
    assert config.JOIN_KEYS == ["loan_identifier", "acquisition_quarter"]


def test_score_variant_is_a_known_column():
    assert config.SCORE_VARIANT in config.VS4_SCORE_COLUMNS


def test_prepay_is_not_a_default_code():
    assert config.PREPAY_ZB_CODES.isdisjoint(config.DEFAULT_ZB_CODES)
