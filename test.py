import BIBIGOproject.Myproject.settings as settings
import os
import sqlite3
con = sqlite3.connect(os.path.join(settings.BASE_DIR,'db.sqlite3'))
cur = con.cursor()
print(cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())

print(cur.execute("SELECT * FROM product_table_carrefour ;").fetchall())
cur.execute("INSERT INTO product_table_carrefour (name, price, img, link, cat) VALUES ('nametest', 100, 'imgtest', 'linktest', 'cattest')")
print(cur.execute("SELECT * FROM product_table_carrefour ;").fetchall())
con.commit()
con.close()