import sqlite3
import pathlib
# 連接 SQLite 資料庫
# 此函式返回 SQLite 連線 (conn) 和游標 (cursor)
def get_db_connection():
    base_path = pathlib.Path(__file__).parent  # 獲取當前腳本所在目錄
    db_path = base_path / "BIBIGOproject" 
    conn = sqlite3.connect(db_path / "db.sqlite3")  # 連接 SQLite 資料庫
    cursor = conn.cursor()
    return conn, cursor

def re_category():
    conn, cursor = get_db_connection()
    
    update_mapping = {
        "食品、飲品": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 60, 85, 86, 87, 88, 141],
        "3C、電器": [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 89, 90, 91, 92, 93, 94, 95, 96, 97, 143],
        "美妝、生活": [37, 38, 39, 40, 58, 59, 101, 102, 129, 130, 131, 132, 133, 134, 135, 136, 151],
        "藥品、保健": [41, 42, 98, 99, 100, 137],
        "嬰兒、寵物": [43, 44, 45, 46, 48, 103, 142],
        "運動、休閒": [47, 49, 50, 51, 52, 55, 57, 122, 123, 124, 125, 126, 146],
        "文具、玩具": [53, 54, 104, 127, 128, 147],
        "五金、雜貨": [56, 61, 62, 67, 115, 116, 144, 145, 149],
        "傢俱、廚具": [63, 64, 65, 66, 68, 69, 70, 71, 113, 114, 148, 150],
        "衣服、飾品": [72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 105, 106, 107, 108, 109, 110, 111, 112, 117, 118, 119, 120, 121, 138, 139, 140],
    }

    sql = """
        UPDATE myapp_product 
        SET value = ? 
        WHERE category_id IN ({})
        AND (value IS NULL OR value = '')
    """
    
    for value, category_ids in update_mapping.items():
        cursor.execute(sql.format(",".join(["?"] * len(category_ids))), [value] + category_ids)

    conn.commit()
    conn.close()
    print("欄位更新完成！")

def delete():
    conn, cursor = get_db_connection()
    cursor.execute(
        "UPDATE myapp_product SET value = NULL"
    )
    conn.commit()
    conn.close()
    print("value欄位已經刪除！")
    
if __name__ == '__main__':
    re_category()
    # delete()