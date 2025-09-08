import sqlite3
import pandas as pd

class CompetitionDataQuery:
    def __init__(self, db_path='competition_ratio.db'):
        self.db_path = db_path
    
    def get_data_by_department(self, department=None):
        """학과별로 데이터를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        if department:
            query = """
            SELECT * FROM competition_data 
            WHERE department = ?
            ORDER BY admission_type, crawl_date DESC
            """
            df = pd.read_sql_query(query, conn, params=[department])
        else:
            query = """
            SELECT * FROM competition_data 
            ORDER BY department, admission_type, crawl_date DESC
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_data_by_admission_type(self, admission_type):
        """전형별로 데이터를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT * FROM competition_data 
        WHERE admission_type = ?
        ORDER BY department, crawl_date DESC
        """
        df = pd.read_sql_query(query, conn, params=[admission_type])
        conn.close()
        return df
    
    def get_summary_stats(self):
        """요약 통계를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            department,
            admission_type,
            AVG(competition_ratio) as avg_ratio,
            MAX(competition_ratio) as max_ratio,
            MIN(competition_ratio) as min_ratio,
            SUM(recruitment_count) as total_recruitment,
            SUM(applicant_count) as total_applicants,
            COUNT(*) as record_count
        FROM competition_data 
        GROUP BY department, admission_type
        ORDER BY department, admission_type
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def print_department_summary(self, department=None):
        """학과 요약 정보를 출력합니다."""
        df = self.get_data_by_department(department)
        
        if df.empty:
            print("조회된 데이터가 없습니다.")
            return
        
        if department:
            print(f"\n=== {department} 경쟁률 현황 ===")
        else:
            print("\n=== 전체 학과 경쟁률 현황 ===")
        
        for _, row in df.iterrows():
            print(f"{row['department']} | {row['admission_type']}")
            print(f"  모집인원: {row['recruitment_count']:,}명")
            print(f"  지원인원: {row['applicant_count']:,}명")
            print(f"  경쟁률: {row['competition_ratio']:.2f}:1")
            print(f"  수집일시: {row['crawl_date']}")
            print("-" * 50)

    def get_overall_stats(self):
        """전체 통계를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            SUM(recruitment_count) as grand_total_recruitment,
            SUM(applicant_count) as grand_total_applicants,
            AVG(competition_ratio) as grand_avg_ratio,
            MAX(competition_ratio) as grand_max_ratio,
            MIN(competition_ratio) as grand_min_ratio,
            COUNT(DISTINCT department) as total_departments,
            COUNT(DISTINCT admission_type) as total_admission_types,
            COUNT(*) as total_records
        FROM competition_data
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0] if not df.empty else None
    
    def print_overall_summary(self):
        """전체 요약 정보를 출력합니다."""
        stats = self.get_overall_stats()
        if stats is None:
            print("통계 데이터가 없습니다.")
            return
        
        print("\n" + "=" * 60)
        print("전체 대학 경쟁률 통계 요약")
        print("=" * 60)
        print(f"📊 전체 모집인원: {int(stats['grand_total_recruitment']):,}명")
        print(f"📊 전체 지원인원: {int(stats['grand_total_applicants']):,}명")
        print(f"📊 전체 평균 경쟁률: {stats['grand_avg_ratio']:.3f}:1")
        print(f"📊 최고 경쟁률: {stats['grand_max_ratio']:.3f}:1")
        print(f"📊 최저 경쟁률: {stats['grand_min_ratio']:.3f}:1")
        print(f"📊 수집 학과 수: {int(stats['total_departments'])}개")
        print(f"📊 수집 전형 수: {int(stats['total_admission_types'])}개")
        print(f"📊 총 데이터 레코드: {int(stats['total_records'])}개")
        print("=" * 60)
    
    def get_department_stats(self):
        """학과별 통계를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            department,
            SUM(recruitment_count) as dept_total_recruitment,
            SUM(applicant_count) as dept_total_applicants,
            AVG(competition_ratio) as dept_avg_ratio,
            MAX(competition_ratio) as dept_max_ratio,
            MIN(competition_ratio) as dept_min_ratio,
            COUNT(DISTINCT admission_type) as dept_admission_types,
            COUNT(*) as dept_records
        FROM competition_data 
        GROUP BY department
        ORDER BY dept_total_recruitment DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def print_department_stats(self):
        """학과별 통계를 출력합니다."""
        dept_stats = self.get_department_stats()
        if dept_stats.empty:
            print("학과별 통계 데이터가 없습니다.")
            return
        
        print("\n" + "=" * 80)
        print("학과별 상세 통계")
        print("=" * 80)
        
        for _, row in dept_stats.iterrows():
            print(f"🏛️  {row['department']}")
            print(f"   모집인원: {int(row['dept_total_recruitment']):,}명")
            print(f"   지원인원: {int(row['dept_total_applicants']):,}명")
            print(f"   평균 경쟁률: {row['dept_avg_ratio']:.3f}:1")
            print(f"   최고 경쟁률: {row['dept_max_ratio']:.3f}:1")
            print(f"   최저 경쟁률: {row['dept_min_ratio']:.3f}:1")
            print(f"   전형 수: {int(row['dept_admission_types'])}개")
            print(f"   데이터 건수: {int(row['dept_records'])}건")
            print("-" * 70)
        print("=" * 80)

def main():
    """메인 함수 - 사용 예시"""
    query = CompetitionDataQuery()
    
    # 전체 통계 먼저 출력
    query.print_overall_summary()
    
    # 학과별 통계 출력
    query.print_department_stats()
    
    print("\n1. 전체 데이터 요약")
    query.print_department_summary()
    
    print("\n2. 컴퓨터소프트웨어학부 데이터")
    query.print_department_summary('컴퓨터소프트웨어학부')
    
    print("\n3. 학과별 전형별 상세 통계")
    stats_df = query.get_summary_stats()
    if not stats_df.empty:
        for _, row in stats_df.iterrows():
            print(f"📋 {row['department']} | {row['admission_type']}")
            print(f"   평균 경쟁률: {row['avg_ratio']:.3f}:1")
            print(f"   최고 경쟁률: {row['max_ratio']:.3f}:1")
            print(f"   최저 경쟁률: {row['min_ratio']:.3f}:1")
            print(f"   총 모집인원: {int(row['total_recruitment'])}명")
            print(f"   총 지원인원: {int(row['total_applicants'])}명")
            print(f"   데이터 건수: {int(row['record_count'])}건")
            print("-" * 50)

if __name__ == "__main__":
    main()