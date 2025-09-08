#!/usr/bin/env python3
"""
간단한 대학교 경쟁률 조회 도구
사용법: python3 simple_viewer.py [옵션]
"""

import sqlite3
import pandas as pd
from datetime import datetime
import argparse

class SimpleViewer:
    def __init__(self, db_path='competition_ratio_enhanced.db'):
        self.db_path = db_path
    
    def check_database(self):
        """데이터베이스 연결 상태를 확인합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM universities")
            university_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM competition_snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"📊 데이터베이스 상태: {university_count}개 대학교, {snapshot_count}개 스냅샷")
            return True
            
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def show_current_competition(self):
        """현재 경쟁률을 간단히 보여줍니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        WITH latest_data AS (
            SELECT 
                cs.university_id,
                cs.department_id,
                cs.admission_type_id,
                cs.recruitment_count,
                cs.applicant_count,
                cs.competition_ratio,
                cs.snapshot_time,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.university_id, cs.department_id, cs.admission_type_id 
                    ORDER BY cs.snapshot_time DESC
                ) as rn
            FROM competition_snapshots cs
        )
        SELECT 
            u.name as university_name,
            d.name as department_name,
            at.name as admission_type,
            ld.recruitment_count,
            ld.applicant_count,
            ld.competition_ratio,
            ld.snapshot_time
        FROM latest_data ld
        JOIN universities u ON ld.university_id = u.id
        JOIN departments d ON ld.department_id = d.id
        JOIN admission_types at ON ld.admission_type_id = at.id
        WHERE ld.rn = 1
        ORDER BY ld.competition_ratio DESC, u.name, d.name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("❌ 경쟁률 데이터가 없습니다.")
            return
        
        print("\n🎯 현재 경쟁률 현황")
        print("=" * 80)
        
        current_univ = ""
        for _, row in df.iterrows():
            if current_univ != row['university_name']:
                current_univ = row['university_name']
                print(f"\n🏛️  {current_univ}")
                print("-" * 50)
            
            # 경쟁률에 따른 아이콘
            if row['competition_ratio'] > 1.0:
                icon = "🔥"
            elif row['competition_ratio'] > 0.5:
                icon = "📈"
            elif row['competition_ratio'] > 0.1:
                icon = "📊"
            else:
                icon = "💤"
            
            dept_short = row['department_name'][:10] + "..." if len(row['department_name']) > 13 else row['department_name']
            adm_short = row['admission_type'].replace('학생부', '').replace('(', '').replace(')', '')[:8]
            
            print(f"  {icon} {dept_short:<15} {adm_short:<10} | "
                  f"모집:{row['recruitment_count']:>3}명 지원:{row['applicant_count']:>3}명 "
                  f"경쟁률:{row['competition_ratio']:>6.2f}:1")
    
    def show_university_list(self):
        """등록된 대학교 목록을 보여줍니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.name as university_name,
            u.code as university_code,
            COUNT(DISTINCT d.id) as department_count,
            COUNT(DISTINCT cs.id) as snapshot_count,
            MAX(cs.snapshot_time) as latest_crawl
        FROM universities u
        LEFT JOIN colleges c ON u.id = c.university_id
        LEFT JOIN departments d ON c.id = d.college_id
        LEFT JOIN competition_snapshots cs ON u.id = cs.university_id
        GROUP BY u.id, u.name, u.code
        ORDER BY u.name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("\n🏛️  등록된 대학교")
        print("=" * 60)
        
        for _, row in df.iterrows():
            latest = "없음" if pd.isna(row['latest_crawl']) else row['latest_crawl'][:16]
            status = "✅" if row['snapshot_count'] > 0 else "❌"
            
            print(f"{status} {row['university_name']:<12} ({row['university_code']}) | "
                  f"학과:{row['department_count']}개 스냅샷:{row['snapshot_count']:>3}개 | "
                  f"최근:{latest}")
    
    def show_top_competition(self, limit=5):
        """경쟁률 TOP 순위를 보여줍니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        WITH latest_data AS (
            SELECT 
                cs.university_id,
                cs.department_id, 
                cs.admission_type_id,
                cs.recruitment_count,
                cs.applicant_count,
                cs.competition_ratio,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.university_id, cs.department_id, cs.admission_type_id 
                    ORDER BY cs.snapshot_time DESC
                ) as rn
            FROM competition_snapshots cs
        )
        SELECT 
            u.name as university_name,
            d.name as department_name,
            at.name as admission_type,
            ld.recruitment_count,
            ld.applicant_count,
            ld.competition_ratio
        FROM latest_data ld
        JOIN universities u ON ld.university_id = u.id
        JOIN departments d ON ld.department_id = d.id  
        JOIN admission_types at ON ld.admission_type_id = at.id
        WHERE ld.rn = 1 AND ld.competition_ratio > 0
        ORDER BY ld.competition_ratio DESC
        LIMIT {}
        """.format(limit)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"\n🏆 경쟁률 TOP {limit}")
        print("=" * 70)
        
        if df.empty:
            print("경쟁률 데이터가 없습니다.")
            return
        
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            if row['competition_ratio'] >= 1.0:
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏅"
            else:
                medal = "📊"
                
            univ_short = row['university_name'][:6] + ".." if len(row['university_name']) > 8 else row['university_name']
            dept_short = row['department_name'][:12] + ".." if len(row['department_name']) > 14 else row['department_name']
            
            print(f"{medal} #{idx:<2} {univ_short:<10} {dept_short:<15} | "
                  f"모집:{row['recruitment_count']:>3}명 지원:{row['applicant_count']:>3}명 "
                  f"경쟁률:{row['competition_ratio']:>6.2f}:1")
    
    def show_recent_activity(self, limit=5):
        """최근 크롤링 활동을 보여줍니다.""" 
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.name as university_name,
            cs.start_time,
            cs.status,
            cs.records_collected,
            cs.error_message
        FROM crawl_sessions cs
        JOIN universities u ON cs.university_id = u.id
        ORDER BY cs.start_time DESC
        LIMIT {}
        """.format(limit)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"\n🔄 최근 크롤링 활동")
        print("=" * 60)
        
        if df.empty:
            print("크롤링 기록이 없습니다.")
            return
        
        for _, row in df.iterrows():
            status_icon = "✅" if row['status'] == 'COMPLETED' else "❌" if row['status'] == 'FAILED' else "🔄"
            time_str = row['start_time'][:16] if row['start_time'] else "시간없음"
            
            univ_short = row['university_name'][:8] + ".." if len(row['university_name']) > 10 else row['university_name']
            
            error_info = ""
            if row['error_message']:
                error_info = f" | 오류: {row['error_message'][:20]}..."
            
            print(f"{status_icon} {time_str} | {univ_short:<12} | {row['records_collected']}건 수집{error_info}")
    
    def show_quick_summary(self):
        """빠른 요약 정보를 보여줍니다."""
        print("\n" + "="*80)
        print("🎓 대학교 경쟁률 빠른 조회")
        print(f"📅 조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not self.check_database():
            return
        
        self.show_university_list()
        self.show_top_competition()
        self.show_current_competition()
        self.show_recent_activity()
        
        print("\n" + "="*80)
        print("💡 더 자세한 정보: python3 comprehensive_viewer.py")
        print("🔄 자동 크롤링: python3 scheduler.py --mode schedule")
        print("📊 추세 분석: python3 trend_analyzer.py")
        print("="*80)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='간단한 대학교 경쟁률 조회')
    parser.add_argument('--db', default='competition_ratio_enhanced.db', help='데이터베이스 파일')
    parser.add_argument('--top', type=int, default=5, help='TOP 순위 개수')
    parser.add_argument('--recent', type=int, default=5, help='최근 활동 개수')
    parser.add_argument('--summary', action='store_true', help='전체 요약 보기')
    parser.add_argument('--list', action='store_true', help='대학교 목록만 보기')
    parser.add_argument('--competition', action='store_true', help='현재 경쟁률만 보기')
    
    args = parser.parse_args()
    
    viewer = SimpleViewer(args.db)
    
    if args.list:
        viewer.show_university_list()
    elif args.competition:
        viewer.show_current_competition()
    elif args.summary or not any([args.list, args.competition]):
        viewer.show_quick_summary()

if __name__ == "__main__":
    main()