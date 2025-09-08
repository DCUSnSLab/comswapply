import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
from datetime import datetime

class AdvancedCompetitionRatioCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 수집 대상 학과 정의
        self.target_departments = [
            '컴퓨터소프트웨어학부',
            'AI빅데이터공학과',
            '소프트웨어융합학과'
        ]
        
        # 다양한 전형별 URL 패턴 (실제 사이트 구조에 맞게 조정 필요)
        self.admission_urls = {
            '학생부종합(SW전형)': "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10460911.html",
            # 추가 전형 URL들은 실제 사이트 구조 파악 후 추가
        }
    
    def fetch_page(self, url):
        """웹페이지를 가져옵니다."""
        try:
            response = self.session.get(url)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"페이지 요청 중 오류 발생 ({url}): {e}")
            return None
    
    def detect_admission_type_from_url_or_content(self, url, html_content):
        """URL이나 콘텐츠에서 전형 타입을 감지합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # URL 기반 전형 감지
        if 'sw' in url.lower():
            return '학생부종합(SW전형)'
        
        # 콘텐츠 기반 전형 감지
        admission_patterns = {
            '학생부종합(SW전형)': ['sw전형', 'sw 전형', '소프트웨어전형'],
            '학생부교과(교과전형)': ['교과전형', '학생부교과'],
            '학생부종합(종합전형)': ['종합전형', '학생부종합'],
            '학생부교과(지역교과전형)': ['지역교과'],
            '학생부종합(지역종합전형)': ['지역종합'],
        }
        
        for admission_type, patterns in admission_patterns.items():
            if any(pattern in page_text for pattern in patterns):
                return admission_type
        
        return '미분류'
    
    def parse_table_data(self, table, admission_type):
        """테이블에서 데이터를 파싱합니다."""
        competition_data = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # 헤더 행 건너뛰기
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 5:  # 단과대학, 모집단위, 모집인원, 지원인원, 경쟁률
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # 소프트웨어융합대학 확인
                if '소프트웨어융합대학' in cell_texts[0]:
                    college = cell_texts[0]
                    department_raw = cell_texts[1]
                    
                    # 대상 학과인지 확인
                    if self.is_target_department(department_raw):
                        try:
                            recruitment_count = self.extract_number(cell_texts[2])
                            applicant_count = self.extract_number(cell_texts[3])
                            
                            # 경쟁률 계산
                            if recruitment_count > 0:
                                competition_ratio = applicant_count / recruitment_count
                            else:
                                competition_ratio = 0.0
                            
                            # 학과명 정리
                            clean_department = self.clean_department_name(department_raw)
                            
                            competition_data.append({
                                'college': college,
                                'department': clean_department,
                                'admission_type': admission_type,
                                'recruitment_count': recruitment_count,
                                'applicant_count': applicant_count,
                                'competition_ratio': competition_ratio
                            })
                            
                        except (ValueError, IndexError) as e:
                            print(f"데이터 파싱 오류: {e} - {cell_texts}")
        
        return competition_data
    
    def is_target_department(self, department):
        """대상 학과인지 확인합니다."""
        return any(
            target in department for target in [
                '컴퓨터소프트웨어', 'AI빅데이터공학', '소프트웨어융합'
            ]
        )
    
    def clean_department_name(self, department):
        """학과명을 정리합니다."""
        # 불필요한 텍스트 제거
        clean_dept = re.sub(r'교직|RIS사업|\s+', ' ', department).strip()
        
        # 표준 학과명으로 변환
        if '컴퓨터소프트웨어' in clean_dept:
            return '컴퓨터소프트웨어학부'
        elif 'AI빅데이터공학' in clean_dept:
            return 'AI빅데이터공학과'
        elif '소프트웨어융합' in clean_dept:
            return '소프트웨어융합학과'
        
        return clean_dept
    
    def extract_number(self, text):
        """텍스트에서 숫자를 추출합니다."""
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def save_to_database(self, data):
        """데이터를 SQLite 데이터베이스에 저장합니다."""
        conn = sqlite3.connect('competition_ratio.db')
        cursor = conn.cursor()
        
        for item in data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO competition_data 
                    (college, department, admission_type, recruitment_count, 
                     applicant_count, competition_ratio, crawl_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['college'],
                    item['department'],
                    item['admission_type'],
                    item['recruitment_count'],
                    item['applicant_count'],
                    item['competition_ratio'],
                    datetime.now()
                ))
            except sqlite3.Error as e:
                print(f"데이터베이스 저장 오류: {e}")
        
        conn.commit()
        conn.close()
        print(f"{len(data)}개의 레코드가 저장되었습니다.")
    
    def crawl_all_admissions(self):
        """모든 전형의 경쟁률 데이터를 크롤링합니다."""
        print("고급 크롤링 시작...")
        all_data = []
        
        for admission_type, url in self.admission_urls.items():
            print(f"\n{admission_type} 크롤링 중...")
            
            html_content = self.fetch_page(url)
            if not html_content:
                continue
            
            # 전형 타입 감지
            detected_type = self.detect_admission_type_from_url_or_content(url, html_content)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                table_data = self.parse_table_data(table, detected_type)
                all_data.extend(table_data)
        
        # 수집된 데이터 출력
        if all_data:
            print(f"\n총 수집된 데이터 ({len(all_data)}개):")
            for data in all_data:
                print(f"- {data['department']} | {data['admission_type']} | "
                      f"모집: {data['recruitment_count']} | 지원: {data['applicant_count']} | "
                      f"경쟁률: {data['competition_ratio']:.2f}:1")
            
            # 데이터베이스에 저장
            self.save_to_database(all_data)
        else:
            print("수집된 데이터가 없습니다.")
        
        print("\n고급 크롤링이 완료되었습니다.")

if __name__ == "__main__":
    from database_setup import create_database
    
    # 데이터베이스 생성
    create_database()
    
    # 고급 크롤링 실행
    crawler = AdvancedCompetitionRatioCrawler()
    crawler.crawl_all_admissions()