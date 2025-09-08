import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import argparse
from tabulate import tabulate

class ComprehensiveDataViewer:
    def __init__(self, db_path='competition_ratio_enhanced.db'):
        self.db_path = db_path
        
    def get_all_universities_overview(self):
        """전체 대학교 개요를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.name as university_name,
            u.code as university_code,
            COUNT(DISTINCT c.id) as college_count,
            COUNT(DISTINCT d.id) as department_count,
            COUNT(DISTINCT cs.id) as total_snapshots,
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
        return df
    
    def get_latest_competition_data(self, hours_back=24):
        """최신 경쟁률 데이터를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        WITH latest_snapshots AS (
            SELECT 
                university_id, department_id, admission_type_id,
                MAX(snapshot_time) as latest_time
            FROM competition_snapshots 
            WHERE snapshot_time >= datetime('now', '-{} hours')
            GROUP BY university_id, department_id, admission_type_id
        )
        SELECT 
            u.name as university_name,
            u.code as university_code,
            c.name as college_name,
            d.name as department_name,
            at.name as admission_type,
            cs.recruitment_count,
            cs.applicant_count,
            cs.competition_ratio,
            cs.snapshot_time,
            CASE 
                WHEN cs.competition_ratio > 1.0 THEN '🔥'
                WHEN cs.competition_ratio > 0.5 THEN '📈'
                WHEN cs.competition_ratio > 0.1 THEN '📊'
                ELSE '💤'
            END as status_icon
        FROM competition_snapshots cs
        JOIN latest_snapshots ls ON (
            cs.university_id = ls.university_id 
            AND cs.department_id = ls.department_id
            AND cs.admission_type_id = ls.admission_type_id
            AND cs.snapshot_time = ls.latest_time
        )
        JOIN universities u ON cs.university_id = u.id
        JOIN colleges c ON cs.college_id = c.id
        JOIN departments d ON cs.department_id = d.id
        JOIN admission_types at ON cs.admission_type_id = at.id
        ORDER BY u.name, d.name, at.name
        """.format(hours_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['snapshot_time'] = pd.to_datetime(df['snapshot_time'])
        
        return df
    
    def get_university_summary_stats(self):
        """대학교별 요약 통계를 조회합니다."""
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
            u.code as university_code,
            COUNT(*) as programs_count,
            SUM(ld.recruitment_count) as total_recruitment,
            SUM(ld.applicant_count) as total_applicants,
            AVG(ld.competition_ratio) as avg_competition_ratio,
            MAX(ld.competition_ratio) as max_competition_ratio,
            MIN(ld.competition_ratio) as min_competition_ratio
        FROM latest_data ld
        JOIN universities u ON ld.university_id = u.id
        WHERE ld.rn = 1
        GROUP BY u.id, u.name, u.code
        ORDER BY total_applicants DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_top_competitive_programs(self, limit=10):
        """가장 경쟁이 치열한 프로그램들을 조회합니다."""
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
            ld.snapshot_time,
            CASE 
                WHEN ld.competition_ratio >= 2.0 THEN '🔥🔥🔥'
                WHEN ld.competition_ratio >= 1.5 THEN '🔥🔥'
                WHEN ld.competition_ratio >= 1.0 THEN '🔥'
                ELSE '📊'
            END as heat_level
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
        
        if not df.empty:
            df['snapshot_time'] = pd.to_datetime(df['snapshot_time'])
        
        return df
    
    def get_crawling_session_status(self, limit=20):
        """최근 크롤링 세션 상태를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.name as university_name,
            cs.start_time,
            cs.end_time,
            cs.status,
            cs.records_collected,
            cs.error_message,
            CASE 
                WHEN cs.status = 'COMPLETED' THEN '✅'
                WHEN cs.status = 'FAILED' THEN '❌'
                WHEN cs.status = 'RUNNING' THEN '🔄'
                ELSE '❓'
            END as status_icon,
            ROUND(
                (julianday(cs.end_time) - julianday(cs.start_time)) * 24 * 60, 2
            ) as duration_minutes
        FROM crawl_sessions cs
        JOIN universities u ON cs.university_id = u.id
        ORDER BY cs.start_time DESC
        LIMIT {}
        """.format(limit)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_trend_data(self, hours_back=24):
        """시간별 추세 데이터를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            u.name as university_name,
            d.name as department_name,
            cs.snapshot_time,
            SUM(cs.applicant_count) as total_applicants,
            AVG(cs.competition_ratio) as avg_competition_ratio
        FROM competition_snapshots cs
        JOIN universities u ON cs.university_id = u.id
        JOIN departments d ON cs.department_id = d.id
        WHERE cs.snapshot_time >= datetime('now', '-{} hours')
        GROUP BY u.name, d.name, cs.snapshot_time
        ORDER BY cs.snapshot_time DESC, u.name, d.name
        """.format(hours_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['snapshot_time'] = pd.to_datetime(df['snapshot_time'])
        
        return df
    
    def print_universities_overview(self):
        """대학교 개요를 출력합니다."""
        df = self.get_all_universities_overview()
        
        print("🏛️  대학교 전체 개요")
        print("=" * 80)
        
        if df.empty:
            print("등록된 대학교가 없습니다.")
            return
        
        headers = ["대학교명", "코드", "단과대학", "학과", "총 스냅샷", "최근 크롤링"]
        table_data = []
        
        for _, row in df.iterrows():
            latest_crawl = "없음" if pd.isna(row['latest_crawl']) else row['latest_crawl']
            table_data.append([
                row['university_name'],
                row['university_code'],
                f"{row['college_count']}개",
                f"{row['department_count']}개", 
                f"{row['total_snapshots']:,}개",
                latest_crawl
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
    
    def print_latest_competition_data(self, hours_back=24):
        """최신 경쟁률 데이터를 출력합니다."""
        df = self.get_latest_competition_data(hours_back)
        
        print(f"📊 최신 경쟁률 현황 (최근 {hours_back}시간)")
        print("=" * 100)
        
        if df.empty:
            print("최신 경쟁률 데이터가 없습니다.")
            return
        
        for univ_name in df['university_name'].unique():
            univ_data = df[df['university_name'] == univ_name]
            print(f"\n🎓 {univ_name}")
            print("-" * 60)
            
            headers = ["상태", "학과", "전형", "모집", "지원", "경쟁률", "업데이트"]
            table_data = []
            
            for _, row in univ_data.iterrows():
                table_data.append([
                    row['status_icon'],
                    row['department_name'],
                    row['admission_type'],
                    f"{row['recruitment_count']}명",
                    f"{row['applicant_count']}명",
                    f"{row['competition_ratio']:.3f}:1",
                    row['snapshot_time'].strftime('%m-%d %H:%M')
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt="simple"))
    
    def print_university_summary_stats(self):
        """대학교별 요약 통계를 출력합니다."""
        df = self.get_university_summary_stats()
        
        print("📈 대학교별 요약 통계")
        print("=" * 80)
        
        if df.empty:
            print("통계 데이터가 없습니다.")
            return
        
        headers = ["대학교", "프로그램수", "총모집", "총지원", "평균경쟁률", "최고경쟁률"]
        table_data = []
        
        for _, row in df.iterrows():
            table_data.append([
                f"{row['university_name']}\n({row['university_code']})",
                f"{row['programs_count']}개",
                f"{int(row['total_recruitment']):,}명",
                f"{int(row['total_applicants']):,}명",
                f"{row['avg_competition_ratio']:.3f}:1",
                f"{row['max_competition_ratio']:.3f}:1"
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
    
    def print_top_competitive_programs(self, limit=10):
        """가장 경쟁이 치열한 프로그램들을 출력합니다."""
        df = self.get_top_competitive_programs(limit)
        
        print(f"🔥 TOP {limit} 경쟁률 높은 프로그램")
        print("=" * 80)
        
        if df.empty:
            print("경쟁률 데이터가 없습니다.")
            return
        
        headers = ["순위", "열기", "대학교", "학과", "전형", "모집", "지원", "경쟁률"]
        table_data = []
        
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            table_data.append([
                f"#{idx}",
                row['heat_level'],
                row['university_name'],
                row['department_name'],
                row['admission_type'],
                f"{row['recruitment_count']}명",
                f"{row['applicant_count']}명",
                f"{row['competition_ratio']:.3f}:1"
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
    
    def print_crawling_status(self, limit=10):
        """크롤링 세션 상태를 출력합니다."""
        df = self.get_crawling_session_status(limit)
        
        print(f"🔄 최근 {limit}개 크롤링 세션 상태")
        print("=" * 80)
        
        if df.empty:
            print("크롤링 세션 데이터가 없습니다.")
            return
        
        headers = ["상태", "대학교", "시작시간", "소요시간(분)", "수집건수", "에러"]
        table_data = []
        
        for _, row in df.iterrows():
            error_msg = row['error_message'][:30] + "..." if row['error_message'] and len(row['error_message']) > 30 else (row['error_message'] or "")
            
            table_data.append([
                row['status_icon'],
                row['university_name'],
                row['start_time'],
                f"{row['duration_minutes']:.1f}분" if row['duration_minutes'] else "진행중",
                f"{row['records_collected']}건",
                error_msg
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        print()
    
    def print_trend_summary(self, hours_back=24):
        """추세 요약을 출력합니다."""
        df = self.get_trend_data(hours_back)
        
        print(f"📊 추세 요약 (최근 {hours_back}시간)")
        print("=" * 80)
        
        if df.empty:
            print("추세 데이터가 없습니다.")
            return
        
        # 대학교별 최신 vs 이전 비교
        summary_data = []
        
        for univ_name in df['university_name'].unique():
            univ_data = df[df['university_name'] == univ_name].sort_values('snapshot_time')
            
            if len(univ_data) >= 2:
                latest = univ_data.iloc[-1]
                previous = univ_data.iloc[0]
                
                applicant_change = latest['total_applicants'] - previous['total_applicants']
                ratio_change = latest['avg_competition_ratio'] - previous['avg_competition_ratio']
                
                trend_icon = "📈" if applicant_change > 0 else "📉" if applicant_change < 0 else "➡️"
                
                summary_data.append({
                    'university': univ_name,
                    'trend': trend_icon,
                    'applicant_change': applicant_change,
                    'ratio_change': ratio_change,
                    'latest_applicants': latest['total_applicants'],
                    'latest_ratio': latest['avg_competition_ratio']
                })
        
        if summary_data:
            headers = ["대학교", "추세", "지원자변화", "경쟁률변화", "현재지원자", "현재경쟁률"]
            table_data = []
            
            for data in summary_data:
                table_data.append([
                    data['university'],
                    data['trend'],
                    f"{data['applicant_change']:+.0f}명",
                    f"{data['ratio_change']:+.3f}",
                    f"{data['latest_applicants']:.0f}명",
                    f"{data['latest_ratio']:.3f}:1"
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print()
    
    def generate_comprehensive_report(self, hours_back=24, top_programs=10):
        """종합 리포트를 생성합니다."""
        print("🎓 대학교 경쟁률 종합 현황 리포트")
        print("=" * 100)
        print(f"리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"데이터 기준: 최근 {hours_back}시간")
        print()
        
        # 1. 대학교 개요
        self.print_universities_overview()
        
        # 2. 대학교별 요약 통계
        self.print_university_summary_stats()
        
        # 3. TOP 경쟁 프로그램
        self.print_top_competitive_programs(top_programs)
        
        # 4. 최신 경쟁률 현황
        self.print_latest_competition_data(hours_back)
        
        # 5. 추세 요약
        self.print_trend_summary(hours_back)
        
        # 6. 크롤링 상태
        self.print_crawling_status()
    
    def save_report_to_file(self, filename=None, hours_back=24, top_programs=10):
        """리포트를 파일로 저장합니다."""
        if filename is None:
            filename = f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        import sys
        from io import StringIO
        
        # stdout을 임시로 리디렉트
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            self.generate_comprehensive_report(hours_back, top_programs)
            report_content = captured_output.getvalue()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"리포트가 {filename}에 저장되었습니다.", file=old_stdout)
            
        finally:
            sys.stdout = old_stdout
        
        return filename

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='전체 대학교 데이터 종합 조회')
    parser.add_argument('--hours', type=int, default=24, help='조회할 시간 범위 (시간)')
    parser.add_argument('--top', type=int, default=10, help='TOP 경쟁 프로그램 수')
    parser.add_argument('--save', help='리포트 저장 파일명')
    parser.add_argument('--db', default='competition_ratio_enhanced.db', help='데이터베이스 파일 경로')
    
    args = parser.parse_args()
    
    viewer = ComprehensiveDataViewer(args.db)
    
    if args.save:
        viewer.save_report_to_file(args.save, args.hours, args.top)
    else:
        viewer.generate_comprehensive_report(args.hours, args.top)

if __name__ == "__main__":
    main()