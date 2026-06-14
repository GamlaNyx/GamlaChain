import json
import tempfile
import os
from pathlib import Path
from gamla_chain.core.persistence import PersistenceManager


class TestPersistenceManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.pm = PersistenceManager(data_dir=self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_dict(self):
        data = {"key": "value", "num": 42}
        self.pm.save("test", data)
        loaded = self.pm.load("test")
        assert loaded == data

    def test_load_nonexistent_returns_none(self):
        assert self.pm.load("nonexistent") is None

    def test_save_creates_file(self):
        self.pm.save("mydata", {"a": 1})
        path = Path(self.tmpdir) / "mydata.json"
        assert path.exists()
        with open(path) as f:
            assert json.load(f) == {"a": 1}

    def test_save_and_load_list(self):
        data = [1, 2, 3, {"nested": True}]
        self.pm.save("listdata", data)
        assert self.pm.load("listdata") == data

    def test_data_dir_created_if_missing(self):
        new_dir = os.path.join(self.tmpdir, "subdir", "deep")
        pm = PersistenceManager(data_dir=new_dir)
        pm.save("x", {})
        assert Path(new_dir).exists()
