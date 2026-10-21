"""The package's public names are what it exports."""

import wicket


def test_every_public_name_exists():
    assert all(hasattr(wicket, name) for name in wicket.__all__)
