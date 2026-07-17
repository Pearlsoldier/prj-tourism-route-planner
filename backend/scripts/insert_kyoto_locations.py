import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from DB.tour_locations import PostgresCredentials, PostgresClient, DatabaseService
from sql.postgresql import QueryBuilder
import asyncio

# (location_name, address, longitude, latitude)
KYOTO_HIGASHIYAMA_LOCATIONS = [
    ("八坂神社", "京都府京都市東山区祇園町北側625", 135.7785464, 35.003691),
    ("高台寺", "京都府京都市東山区高台寺下河原町526", 135.7807644, 35.0016963),
    (
        "建仁寺",
        "京都府京都市東山区大和大路通四条下る小松町584",
        135.7739072,
        35.0010773,
    ),
    ("安井金比羅宮", "京都府京都市東山区弁天町70", 135.7761173, 35.0000574),
    ("清水寺", "京都府京都市東山区清水1-294", 135.7848819, 34.9948282),
    (
        "知恩院",
        "京都府京都市東山区新橋通大和大路東入林下町400",
        135.7836848,
        35.0060737,
    ),
    ("青蓮院", "京都府京都市東山区粟田口三条坊町69-1", 135.7830984, 35.0074036),
    ("南禅寺", "京都府京都市左京区南禅寺福地町86", 135.7943954, 35.0114336),
    ("永観堂（禅林寺）", "京都府京都市左京区永観堂町48", 135.7954022, 35.014173),
    ("銀閣寺", "京都府京都市左京区銀閣寺町2", 135.7980318, 35.0268561),
]

if __name__ == "__main__":

    async def main():
        db_service = DatabaseService()
        sql_builder = QueryBuilder()
        insert_query = sql_builder.insert_location()

        print(f"=== {len(KYOTO_HIGASHIYAMA_LOCATIONS)}件のデータを投入します ===\n")

        success_count = 0


        print("=== データベース接続 ===\n")


        for location_name, address, longitude, latitude in KYOTO_HIGASHIYAMA_LOCATIONS:
            try:
                await db_service.execute_query(
                    insert_query,
                    (location_name, address, longitude, latitude),
                )
                print(f"✅ 登録成功: {location_name}")
                success_count += 1
            except Exception as e:
                print(f"❌ 登録失敗: {location_name} - {e}")

        print(f"\n=== 完了: {success_count}/{len(KYOTO_HIGASHIYAMA_LOCATIONS)}件 登録 ===")


    asyncio.run(main())
