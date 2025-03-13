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
        "食品、飲品": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,60,85,86,87,88,141,152,
                      153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,169,170,171,172,
                      173,174,175,176,177,178,179,180,181,182,183,187,188,189,190,191,192,193,194,
                      195,196,197,270,271,272],
        "3C、電器": [23,24,25,26,27,28,29,30,31,32,33,34,35,36,89,90,91,92,93,94,95,96,97,143,248,
                    249,250,251,252,253,254,255,256],
        "美妝、生活": [37,38,39,40,58,59,64,101,102,129,130,131,132,133,134,135,136,151,198,199,200,
                      201,202,203,204,205,206,207,208,209,210,211,212,222,224,229,230,231,232,233,234,235,236,
                      237,238,239,240,241,273],
        "藥品、保健": [41,42,98,99,100,137,184,185,186],
        "嬰兒、寵物": [43,44,45,46,48,103,142,226,227,242,243,244],
        "運動、休閒": [47,49,50,51,52,55,57,122,123,124,125,126,146,228,260,261,262,263,264,265,266,],
        "文具、玩具": [53,54,104,127,128,147,257,259,],
        "五金、雜貨": [56,67,115,116,144,145,149,168,217,218,219,223,258],
        "傢俱、廚具": [22,61,62,63,65,66,68,69,70,71,113,114,148,150,213,214,215,216,220,221,225,245,246,247],
        "衣服、飾品": [72,73,74,75,76,77,78,79,80,81,82,83,84,105,106,107,108,109,110,111,112,117,118,
                      119,120,121,138,139,140,267,268,269,274],
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