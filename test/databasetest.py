import unittest
import database
import sqlite3

class DatabaseTest:
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