# myapp/management/commands/clean_prices_sql.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Clean price field from text to numeric in database'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # 檢查無效值
            cursor.execute("SELECT id, price FROM myapp_product WHERE price IS NOT NULL AND price NOT REGEXP '^[0-9.,]+$' LIMIT 5")
            invalid = cursor.fetchall()
            if invalid:
                self.stdout.write("Invalid prices found:")
                for row in invalid:
                    self.stdout.write(f"ID: {row[0]}, Price: {row[1]}")

            # 轉換價格（移除逗號並設為 REAL）
            cursor.execute("""
                UPDATE myapp_product
                SET price = CAST(REPLACE(price, ',', '') AS REAL)
                WHERE price IS NOT NULL AND price REGEXP '^[0-9.,]+$'
            """)
            updated = cursor.rowcount

            # 將無效值設為 NULL
            cursor.execute("""
                UPDATE myapp_product
                SET price = NULL
                WHERE price IS NOT NULL AND price NOT REGEXP '^[0-9.,]+$'
            """)
            nullified = cursor.rowcount

            self.stdout.write(self.style.SUCCESS(f"Updated {updated} prices, set {nullified} invalid prices to NULL"))