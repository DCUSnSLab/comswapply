import schedule
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from multi_university_crawler import MultiUniversityCrawler
from enhanced_database_setup import create_enhanced_database, initialize_base_data, setup_target_departments

class CrawlingScheduler:
    def __init__(self, interval_minutes=10):
        self.interval_minutes = interval_minutes
        self.crawler = MultiUniversityCrawler()
        self.running = True
        
        # 시그널 핸들러 설정 (Ctrl+C로 종료)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 처리 (프로그램 종료)"""
        print(f"\\n종료 신호 수신 (신호: {signum})")
        self.stop()
        sys.exit(0)
    
    def crawl_job(self):
        """크롤링 작업 실행"""
        if not self.running:
            return
        
        print(f"\\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 정기 크롤링 시작")
        
        try:
            self.crawler.crawl_all_universities()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 정기 크롤링 완료\\n")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 크롤링 중 오류 발생: {e}\\n")
    
    def setup_schedule(self):
        """스케줄 설정"""
        # 매 interval_minutes분마다 크롤링 실행
        schedule.every(self.interval_minutes).minutes.do(self.crawl_job)
        
        # 시작 시 즉시 한 번 실행
        print(f"초기 크롤링 실행...")
        self.crawl_job()
        
        next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
        print(f"다음 크롤링 예정 시간: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"크롤링 간격: {self.interval_minutes}분")
        print("종료하려면 Ctrl+C를 누르세요.\\n")
    
    def run(self):
        """스케줄러 실행"""
        print("=== 대학교 경쟁률 자동 크롤링 스케줄러 시작 ===")
        
        self.setup_schedule()
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        print("스케줄러 중지됨")

class ManualCrawler:
    """수동 크롤링을 위한 클래스"""
    
    def __init__(self):
        self.crawler = MultiUniversityCrawler()
    
    def run_once(self):
        """단일 크롤링 실행"""
        print("=== 수동 크롤링 실행 ===")
        self.crawler.crawl_all_universities()
    
    def run_specific_university(self, university_code):
        """특정 대학교만 크롤링"""
        print(f"=== {university_code} 대학교 크롤링 실행 ===")
        success = self.crawler.crawl_university(university_code)
        if success:
            print(f"{university_code} 크롤링 완료")
        else:
            print(f"{university_code} 크롤링 실패")

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='대학교 경쟁률 크롤링 도구')
    parser.add_argument('--mode', choices=['schedule', 'once', 'university'], 
                       default='schedule', help='실행 모드')
    parser.add_argument('--interval', type=int, default=10, 
                       help='스케줄링 간격 (분, 기본값: 10)')
    parser.add_argument('--university', choices=['CKU', 'DGU', 'YNU', 'KMU'], 
                       help='특정 대학교 코드 (university 모드에서 사용)')
    parser.add_argument('--init-db', action='store_true', 
                       help='데이터베이스 초기화')
    
    args = parser.parse_args()
    
    # 데이터베이스 초기화
    if args.init_db:
        print("데이터베이스 초기화 중...")
        create_enhanced_database()
        initialize_base_data()
        setup_target_departments()
        print("데이터베이스 초기화 완료")
        return
    
    if args.mode == 'schedule':
        # 스케줄 모드
        scheduler = CrawlingScheduler(interval_minutes=args.interval)
        scheduler.run()
        
    elif args.mode == 'once':
        # 단일 실행 모드
        manual_crawler = ManualCrawler()
        manual_crawler.run_once()
        
    elif args.mode == 'university':
        # 특정 대학교 모드
        if not args.university:
            print("--university 옵션을 지정해주세요. (CKU, DGU, YNU, KMU 중 하나)")
            return
        
        manual_crawler = ManualCrawler()
        manual_crawler.run_specific_university(args.university)

if __name__ == "__main__":
    main()