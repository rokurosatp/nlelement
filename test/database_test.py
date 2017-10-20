import os
import sys
import unittest
import sqlite3
# ライブラリがルートにある構成の問題で、相対インポートが機能しなくなるのを防ぐための処理
mod_path = os.path.split(os.path.abspath(sys.argv[0]))[0]
sys.path.remove("")
sys.path.append(os.path.join(mod_path, ".."))
# ここから、テストするモジュールを取り込む
from nlelement import database

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
        
if __name__ == "__main__":
    unittest.main()