import pathlib
import sys
import unittest
import sqlite3
# ライブラリがルートにある構成の問題で、相対インポートが機能しなくなるのを防ぐための処理
mod_path = pathlib.Path(__file__).parent
root_path = mod_path.parent
if "" in sys.path:
    sys.path.remove("")
elif str(root_path) in sys.path:
    sys.path.remove(str(root_path))
    print(root_path)
else:
    raise RuntimeError(str(sys.path+[str(root_path)]))
sys.path.append(str(root_path.parent))
# ここから、テストするモジュールを取り込む
from nlelement import database
from nlelement.test import testsamplemaker

class DatabaseTest(unittest.TestCase):
    def test_external_sql_syntax(self):
        connector = sqlite3.connect(":memory:")
        connector.executescript(
            database.__get_sqlcode__("Tables.sql")
        )
        connector.executescript(
            database.__get_sqlcode__("Indices.sql")
        )
        connector.executescript(
            database.__get_sqlcode__("UpdateView.sql")
        )
        connector.executescript(
            database.__get_sqlcode__("ClearTables.sql")
        )
        connector.executescript(
            database.__get_sqlcode__("GetHeadPointCount.sql")
        )
        connector.commit()
        connector.close()
        

class DatabaseWriterTest(unittest.TestCase):
    def test_normal_document(self):
        samples = testsamplemaker.NlElementSampleMaker()
        saver = database.DatabaseWriter(":memory:")
        saver.add_documents([samples.sample1()])

if __name__ == "__main__":
    unittest.main()