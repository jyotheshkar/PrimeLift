"""Readers keep a complete CSV even when an export fails."""
import pandas as pd
import pytest
from primelift.data.generator import save_dataset

def test_success_replaces_whole_dataset(tmp_path):
    path = tmp_path / 'dataset.csv'
    path.write_text('old\n1\n')
    save_dataset(pd.DataFrame({'value': [2, 3]}), path)
    assert path.read_text() == 'value\n2\n3\n'
    assert list(tmp_path.iterdir()) == [path]

def test_failed_write_preserves_previous_dataset(tmp_path):
    path = tmp_path / 'dataset.csv'
    path.write_text('old\n1\n')
    class FailingDataset:
        def to_csv(self, handle, **kwargs):
            handle.write('partial')
            raise OSError('disk error fixture')
    with pytest.raises(OSError):
        save_dataset(FailingDataset(), path)
    assert path.read_text() == 'old\n1\n'
    assert list(tmp_path.iterdir()) == [path]
