"""Regression checks for durable local stats."""
from unittest.mock import patch

import pytest

from pomo_pet.core.stats import StatsStore


def test_stats_save_does_not_truncate_previous_data(tmp_path):
    store = StatsStore(tmp_path / 'stats.json')
    store.record_session(25, 5)
    before = store.path.read_text()
    with patch('pomo_pet.core.persistence.os.replace', side_effect=OSError('disk error')):
        with pytest.raises(OSError):
            store.record_session(25, 5)
    assert store.path.read_text() == before
    assert StatsStore(store.path).stats.total_sessions == 1
