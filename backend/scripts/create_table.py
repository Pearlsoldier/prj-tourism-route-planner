import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from DB.tour_locations import PostgresCredentials, PostgresClient, DatabaseService
from sql.postgresql import QueryBuilder
import asyncio

if __name__ == "__main__":

    async def main():
        table_name = "locations"
        sql_handler = QueryBuilder()
        create_table = sql_handler.create_parent_table(table_name=table_name)
        # drop_table = sql_handler.drop_table(table_name=table_name)

        print("=== データベース接続 ===\n")

        try:
            db_service = DatabaseService()

            # 接続テスト
            if await db_service.test_connection():
                print("\n🚀 データベース準備完了！")
                await db_service.execute_query(create_table)
            else:
                print("\n❌ データベース接続に失敗しました")

        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            print("\n確認事項:")
            print("1. .envファイルに接続情報が設定されているか")

    asyncio.run(main())
