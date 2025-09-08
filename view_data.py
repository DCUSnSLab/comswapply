import sqlite3
import pandas as pd

def view_stored_data():
    """저장된 데이터를 조회합니다."""
    conn = sqlite3.connect('competition_ratio.db')
    
    # 데이터 조회
    query = """
    SELECT * FROM competition_data
    ORDER BY department, admission_type
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("저장된 경쟁률 데이터:")
    print("=" * 100)
    for _, row in df.iterrows():
        print(f"학과: {row['department']}")
        print(f"전형: {row['admission_type']}")
        print(f"모집인원: {row['recruitment_count']}, 지원인원: {row['applicant_count']}")
        print(f"경쟁률: {row['competition_ratio']:.2f}:1")
        print(f"수집일시: {row['crawl_date']}")
        print("-" * 50)
    
    print(f"\n총 {len(df)}개의 레코드가 저장되어 있습니다.")

if __name__ == "__main__":
    view_stored_data()