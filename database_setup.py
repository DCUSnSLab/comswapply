import sqlite3
from datetime import datetime

def create_database():
    """경쟁률 데이터를 저장할 SQLite 데이터베이스와 테이블을 생성합니다."""
    conn = sqlite3.connect('competition_ratio.db')
    cursor = conn.cursor()
    
    # 경쟁률 데이터 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college TEXT NOT NULL,
            department TEXT NOT NULL,
            admission_type TEXT NOT NULL,
            recruitment_count INTEGER,
            applicant_count INTEGER,
            competition_ratio REAL,
            crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(college, department, admission_type, crawl_date)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("데이터베이스가 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    create_database()