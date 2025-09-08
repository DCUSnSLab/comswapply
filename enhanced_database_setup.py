import sqlite3
from datetime import datetime

def create_enhanced_database():
    """다중 대학교 지원과 시간별 추적이 가능한 향상된 데이터베이스를 생성합니다."""
    conn = sqlite3.connect('competition_ratio_enhanced.db')
    cursor = conn.cursor()
    
    # 대학교 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT UNIQUE,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 단과대학 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colleges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (university_id) REFERENCES universities (id),
            UNIQUE(university_id, name)
        )
    ''')
    
    # 학과 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_department BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            UNIQUE(college_id, name)
        )
    ''')
    
    # 입시 전형 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admission_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 경쟁률 데이터 테이블 (시간별 스냅샷)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id INTEGER NOT NULL,
            college_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            admission_type_id INTEGER NOT NULL,
            recruitment_count INTEGER NOT NULL DEFAULT 0,
            applicant_count INTEGER NOT NULL DEFAULT 0,
            competition_ratio REAL GENERATED ALWAYS AS (
                CASE 
                    WHEN recruitment_count > 0 THEN CAST(applicant_count AS REAL) / recruitment_count
                    ELSE 0.0
                END
            ) STORED,
            snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            crawl_session_id TEXT,
            FOREIGN KEY (university_id) REFERENCES universities (id),
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (admission_type_id) REFERENCES admission_types (id)
        )
    ''')
    
    # 크롤링 세션 로그 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_sessions (
            id TEXT PRIMARY KEY,
            university_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'RUNNING',
            records_collected INTEGER DEFAULT 0,
            error_message TEXT,
            FOREIGN KEY (university_id) REFERENCES universities (id)
        )
    ''')
    
    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_time ON competition_snapshots(snapshot_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_dept_time ON competition_snapshots(department_id, snapshot_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_session ON competition_snapshots(crawl_session_id)')
    
    conn.commit()
    conn.close()
    print("향상된 데이터베이스가 성공적으로 생성되었습니다.")

def initialize_base_data():
    """기본 대학교 및 전형 데이터를 초기화합니다."""
    conn = sqlite3.connect('competition_ratio_enhanced.db')
    cursor = conn.cursor()
    
    # 대학교 정보 초기화
    universities = [
        ('가톨릭관동대학교', 'CKU', 'https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10460911.html'),
        ('대구대학교', 'DGU', 'https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10440731.html'),
        ('영남대학교', 'YNU', 'https://ratio.uwayapply.com/Sl5KOmJKZiUmOiZKLWZUZg=='),
        ('계명대학교', 'KMU', 'https://ratio.uwayapply.com/Sl5KOk05SmYlJjomSi1mVGY=')
    ]
    
    for name, code, url in universities:
        cursor.execute('''
            INSERT OR IGNORE INTO universities (name, code, url) 
            VALUES (?, ?, ?)
        ''', (name, code, url))
    
    # 전형 정보 초기화
    admission_types = [
        ('학생부교과(교과전형)', '학생부교과'),
        ('학생부교과(지역교과전형)', '학생부교과'),
        ('학생부교과(가톨릭지도자추천전형)', '학생부교과'),
        ('학생부교과(특성화고전형)', '학생부교과'),
        ('학생부교과(기회균형전형)', '학생부교과'),
        ('학생부교과(지역기회균형전형)', '학생부교과'),
        ('학생부종합(종합전형)', '학생부종합'),
        ('학생부종합(지역종합전형)', '학생부종합'),
        ('학생부종합(SW전형)', '학생부종합'),
        ('학생부교과(농어촌)', '학생부교과'),
        ('학생부교과(기회균형선발전형)', '학생부교과'),
        ('학생부교과(성인학습자)', '학생부교과'),
        ('학생부교과(특성화고졸재직자)', '학생부교과')
    ]
    
    for name, category in admission_types:
        cursor.execute('''
            INSERT OR IGNORE INTO admission_types (name, category) 
            VALUES (?, ?)
        ''', (name, category))
    
    conn.commit()
    conn.close()
    print("기본 데이터가 초기화되었습니다.")

def setup_target_departments():
    """각 대학교별 타겟 학과를 설정합니다."""
    conn = sqlite3.connect('competition_ratio_enhanced.db')
    cursor = conn.cursor()
    
    # 대학교별 타겟 학과 정보
    target_departments = {
        'CKU': {  # 가톨릭관동대학교
            '소프트웨어융합대학': [
                '컴퓨터소프트웨어학부',
                'AI빅데이터공학과', 
                '소프트웨어융합학과'
            ]
        },
        'DGU': {  # 대구대학교
            # 단과대학명은 크롤링 시 확인 필요
            '공과대학': [
                '컴퓨터정보공학부'
            ]
        },
        'YNU': {  # 영남대학교
            '디지털융합대학': [
                # 크롤링 시 전체 학과 수집
            ]
        },
        'KMU': {  # 계명대학교
            # 단과대학명은 크롤링 시 확인 필요
            '공과대학': [
                '컴퓨터공학과',
                '게임소프트웨어학과',
                '모빌리티소프트웨어학과'
            ]
        }
    }
    
    # 각 대학교별로 단과대학과 학과 정보 설정
    for univ_code, colleges in target_departments.items():
        # 대학교 ID 조회
        cursor.execute('SELECT id FROM universities WHERE code = ?', (univ_code,))
        univ_result = cursor.fetchone()
        if not univ_result:
            continue
        
        university_id = univ_result[0]
        
        for college_name, departments in colleges.items():
            # 단과대학 추가
            cursor.execute('''
                INSERT OR IGNORE INTO colleges (university_id, name) 
                VALUES (?, ?)
            ''', (university_id, college_name))
            
            # 단과대학 ID 조회
            cursor.execute('''
                SELECT id FROM colleges 
                WHERE university_id = ? AND name = ?
            ''', (university_id, college_name))
            college_result = cursor.fetchone()
            if not college_result:
                continue
            
            college_id = college_result[0]
            
            # 학과 추가
            for dept_name in departments:
                cursor.execute('''
                    INSERT OR IGNORE INTO departments (college_id, name, target_department) 
                    VALUES (?, ?, TRUE)
                ''', (college_id, dept_name))
    
    conn.commit()
    conn.close()
    print("타겟 학과 설정이 완료되었습니다.")

if __name__ == "__main__":
    create_enhanced_database()
    initialize_base_data()
    setup_target_departments()