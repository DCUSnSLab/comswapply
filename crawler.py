import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
from datetime import datetime

class CompetitionRatioCrawler:
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
        
        # 수집 대상 전형 정의
        self.target_admission_types = [
            '학생부교과(교과전형)',
            '학생부교과(지역교과전형)',
            '학생부교과(가톨릭지도자추천전형)',
            '학생부교과(특성화고전형)',
            '학생부교과(기회균형전형)',
            '학생부교과(지역기회균형전형)',
            '학생부종합(종합전형)',
            '학생부종합(지역종합전형)',
            '학생부종합(SW전형)',
            '학생부교과(농어촌)',
            '학생부교과(기회균형선발전형)',
            '학생부교과(성인학습자)',
            '학생부교과(특성화고졸재직자)'
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
    
    def parse_competition_data(self, html_content):
        """HTML에서 경쟁률 데이터를 파싱합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        competition_data = []
        
        # 전형별로 구분되는 섹션들을 찾기
        # 전체 HTML에서 전형 이름을 찾기 위한 패턴
        admission_type_patterns = {
            '학생부교과(교과전형)': ['학생부교과', '교과전형'],
            '학생부교과(지역교과전형)': ['지역교과'],
            '학생부교과(가톨릭지도자추천전형)': ['가톨릭지도자추천'],
            '학생부교과(특성화고전형)': ['특성화고전형'],
            '학생부교과(기회균형전형)': ['기회균형전형'],
            '학생부교과(지역기회균형전형)': ['지역기회균형'],
            '학생부종합(종합전형)': ['학생부종합', '종합전형'],
            '학생부종합(지역종합전형)': ['지역종합'],
            '학생부종합(SW전형)': ['SW전형'],
            '학생부교과(농어촌)': ['농어촌'],
            '학생부교과(기회균형선발전형)': ['기회균형선발'],
            '학생부교과(성인학습자)': ['성인학습자'],
            '학생부교과(특성화고졸재직자)': ['특성화고졸재직자']
        }
        
        # 현재 전형 추적
        current_admission_type = '미분류'
        
        # HTML 전체 텍스트에서 전형 정보 찾기
        html_text = soup.get_text()
        for admission_type, patterns in admission_type_patterns.items():
            if any(pattern in html_text for pattern in patterns):
                current_admission_type = admission_type
                break
        
        # 테이블 찾기
        tables = soup.find_all('table')
        
        for table in tables:
            # 테이블 전후의 텍스트에서 전형 정보 찾기
            table_context = ""
            prev_sibling = table.find_previous_sibling()
            if prev_sibling:
                table_context += prev_sibling.get_text()
            
            # 테이블 내용에서 전형 정보 확인
            for admission_type, patterns in admission_type_patterns.items():
                if any(pattern in table_context for pattern in patterns):
                    current_admission_type = admission_type
                    break
            
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # 소프트웨어융합대학 확인
                    if len(cell_texts) > 0 and '소프트웨어융합대학' in cell_texts[0]:
                        college = cell_texts[0]
                        
                        if len(cell_texts) >= 5:  # 단과대학, 모집단위, 모집인원, 지원인원, 경쟁률
                            department = cell_texts[1]
                            
                            # 대상 학과인지 확인 (더 유연한 매칭)
                            is_target_department = (
                                '컴퓨터소프트웨어' in department or 
                                'AI빅데이터공학' in department or 
                                '소프트웨어융합' in department
                            )
                            
                            if is_target_department:
                                try:
                                    recruitment_count = self.extract_number(cell_texts[2])
                                    applicant_count = self.extract_number(cell_texts[3])
                                    
                                    # 경쟁률 계산
                                    if recruitment_count > 0:
                                        competition_ratio = applicant_count / recruitment_count
                                    else:
                                        competition_ratio = 0.0
                                    
                                    # 학과명 정리
                                    clean_department = self.clean_department_name(department)
                                    
                                    competition_data.append({
                                        'college': college,
                                        'department': clean_department,
                                        'admission_type': current_admission_type,
                                        'recruitment_count': recruitment_count,
                                        'applicant_count': applicant_count,
                                        'competition_ratio': competition_ratio
                                    })
                                    
                                except (ValueError, IndexError) as e:
                                    print(f"데이터 파싱 오류: {e} - {cell_texts}")
                                    continue
        
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
        print("크롤링 시작...")
        
        # 웹페이지 가져오기
        html_content = self.fetch_page()
        if not html_content:
            print("웹페이지를 가져올 수 없습니다.")
            return
        
        # 데이터 파싱
        print("데이터 파싱 중...")
        competition_data = self.parse_competition_data(html_content)
        
        if not competition_data:
            print("수집된 데이터가 없습니다.")
            return
        
        # 수집된 데이터 출력
        print(f"\n수집된 데이터 ({len(competition_data)}개):")
        for data in competition_data:
            print(f"- {data['college']} | {data['department']} | {data['admission_type']} | "
                  f"모집: {data['recruitment_count']} | 지원: {data['applicant_count']} | "
                  f"경쟁률: {data['competition_ratio']:.2f}:1")
        
        # 데이터베이스에 저장
        self.save_to_database(competition_data)
        print("\n크롤링이 완료되었습니다.")

if __name__ == "__main__":
    from database_setup import create_database
    
    # 데이터베이스 생성
    create_database()
    
    # 크롤링 실행
    url = "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10460911.html"
    crawler = CompetitionRatioCrawler(url)
    crawler.crawl()