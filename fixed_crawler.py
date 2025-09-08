import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
from datetime import datetime

class FixedCompetitionRatioCrawler:
    def __init__(self, url):
        self.url = url
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
    
    def fetch_page(self):
        """웹페이지를 가져옵니다."""
        try:
            response = self.session.get(self.url)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"페이지 요청 중 오류 발생: {e}")
            return None
    
    def find_admission_type_in_context(self, element):
        """요소의 컨텍스트에서 전형 타입을 찾습니다."""
        # 전형별 패턴 정의
        admission_patterns = {
            '학생부교과(교과전형)': ['교과전형'],
            '학생부교과(지역교과전형)': ['지역교과전형'],
            '학생부교과(가톨릭지도자추천전형)': ['가톨릭지도자추천전형'],
            '학생부교과(특성화고전형)': ['특성화고전형'],
            '학생부교과(기회균형전형)': ['기회균형전형'],
            '학생부교과(지역기회균형전형)': ['지역기회균형전형'],
            '학생부종합(종합전형)': ['종합전형'],
            '학생부종합(지역종합전형)': ['지역종합전형'],
            '학생부종합(SW전형)': ['SW전형'],
            '학생부교과(농어촌)': ['농어촌'],
            '학생부교과(기회균형선발전형)': ['기회균형선발전형'],
            '학생부교과(성인학습자)': ['성인학습자'],
            '학생부교과(특성화고졸재직자)': ['특성화고졸재직자']
        }
        
        # 현재 테이블의 이전 형제 요소들에서 전형 정보 찾기
        context_text = ""
        
        # 이전 형제들 확인
        prev_elements = []
        current = element
        for _ in range(10):  # 최대 10개 이전 요소 확인
            current = current.find_previous_sibling()
            if current:
                prev_elements.append(current.get_text())
            else:
                break
        
        context_text = " ".join(reversed(prev_elements))
        
        # 부모 요소도 확인
        parent = element.parent
        if parent:
            context_text += " " + parent.get_text()
        
        # 패턴 매칭
        for admission_type, patterns in admission_patterns.items():
            if any(pattern in context_text for pattern in patterns):
                return admission_type
        
        return '미분류'
    
    def parse_competition_data(self, html_content):
        """HTML에서 경쟁률 데이터를 파싱합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        competition_data = []
        
        # 모든 테이블 찾기
        tables = soup.find_all('table')
        
        print(f"총 {len(tables)}개의 테이블을 찾았습니다.")
        
        for table_idx, table in enumerate(tables):
            print(f"\n테이블 {table_idx + 1} 분석 중...")
            
            # 현재 테이블의 전형 타입 확인
            current_admission_type = self.find_admission_type_in_context(table)
            print(f"감지된 전형: {current_admission_type}")
            
            rows = table.find_all('tr')
            print(f"테이블 행 수: {len(rows)}")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:  # 단과대학, 모집단위, 모집인원, 지원인원, 경쟁률
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # 소프트웨어융합대학 확인
                    if len(cell_texts) > 0 and '소프트웨어융합대학' in cell_texts[0]:
                        college = cell_texts[0]
                        department_raw = cell_texts[1] if len(cell_texts) > 1 else ''
                        
                        # 대상 학과인지 확인
                        is_target_department = any(target in department_raw for target in self.target_departments)
                        
                        # 디버깅: 모든 소프트웨어융합대학 행 출력
                        print(f"    발견된 행: {department_raw} (대상학과: {is_target_department})")
                        
                        # 통합모집인 경우도 수집
                        if is_target_department or '단과대학통합모집' in department_raw:
                            try:
                                recruitment_count = self.extract_number(cell_texts[2]) if len(cell_texts) > 2 else 0
                                applicant_count = self.extract_number(cell_texts[3]) if len(cell_texts) > 3 else 0
                                
                                # 경쟁률 계산
                                if recruitment_count > 0:
                                    competition_ratio = applicant_count / recruitment_count
                                else:
                                    competition_ratio = 0.0
                                
                                # 학과명 정리
                                clean_department = self.clean_department_name(department_raw)
                                
                                data_item = {
                                    'college': college,
                                    'department': clean_department,
                                    'admission_type': current_admission_type,
                                    'recruitment_count': recruitment_count,
                                    'applicant_count': applicant_count,
                                    'competition_ratio': competition_ratio
                                }
                                
                                competition_data.append(data_item)
                                
                                print(f"  데이터 수집: {clean_department} | {current_admission_type} | "
                                      f"모집:{recruitment_count} 지원:{applicant_count} 경쟁률:{competition_ratio:.3f}")
                                
                            except (ValueError, IndexError) as e:
                                print(f"  데이터 파싱 오류: {e} - {cell_texts}")
        
        return competition_data
    
    def clean_department_name(self, department):
        """학과명을 정리합니다."""
        # 불필요한 텍스트 제거
        department = department.replace('교직', '').replace('RIS사업', '')
        department = department.strip()
        
        # 표준 학과명으로 변환
        if '컴퓨터소프트웨어' in department:
            return '컴퓨터소프트웨어학부'
        elif 'AI빅데이터공학' in department:
            return 'AI빅데이터공학과'
        elif '소프트웨어융합' in department:
            return '소프트웨어융합학과'
        
        return department
    
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
    
    def crawl(self):
        """크롤링을 실행합니다."""
        print("=== 수정된 크롤링 시작 ===")
        print(f"URL: {self.url}")
        
        # 웹페이지 가져오기
        html_content = self.fetch_page()
        if not html_content:
            print("웹페이지를 가져올 수 없습니다.")
            return
        
        # 데이터 파싱
        print("\n데이터 파싱 중...")
        competition_data = self.parse_competition_data(html_content)
        
        if not competition_data:
            print("수집된 데이터가 없습니다.")
            return
        
        print(f"\n=== 수집 결과 요약 ===")
        print(f"총 {len(competition_data)}개 데이터 수집")
        
        # 전형별 통계
        admission_stats = {}
        for data in competition_data:
            adm_type = data['admission_type']
            if adm_type not in admission_stats:
                admission_stats[adm_type] = 0
            admission_stats[adm_type] += 1
        
        print("\n전형별 수집 현황:")
        for adm_type, count in admission_stats.items():
            print(f"  {adm_type}: {count}개")
        
        # 데이터베이스에 저장
        print("\n데이터베이스 저장 중...")
        self.save_to_database(competition_data)
        
        print("\n=== 크롤링 완료 ===")

if __name__ == "__main__":
    from database_setup import create_database
    
    # 데이터베이스 생성
    create_database()
    
    # 크롤링 실행 (대구가톨릭대학교)
    url = "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10460911.html"
    crawler = FixedCompetitionRatioCrawler(url)
    crawler.crawl()