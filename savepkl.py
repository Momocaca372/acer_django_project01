import crawl_controler
import pickle
import json

if __name__ == '__main__':
    all_products = (
        # crawl_controler.Crawl.carrefour() 
        # + crawl_controler.Crawl.costco() 
         crawl_controler.Crawl.poyabuy()
        # + crawl_controler.Crawl.savesafe()
        ) # 從爬蟲控制器獲取商品資料
    with open("product.pkl", "wb") as f:
        pickle.dump(all_products, f) 
        
    with open("product.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=4, ensure_ascii=False)    