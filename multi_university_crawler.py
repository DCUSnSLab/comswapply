import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class MultiUniversityCrawler:
    def __init__(self, db_path='competition_ratio_enhanced.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 대학교별 크롤링 설정
        self.university_configs = {
            'CKU': {  # 가톨릭관동대학교
                'url': 'https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10460911.html',
                'parser': self.parse_addon_jinhakapply,
                'target_college': '소프트웨어융합대학',
                'target_departments': ['컴퓨터소프트웨어학부', 'AI빅데이터공학과', '소프트웨어융합학과']
            },
            'DGU': {  # 대구대학교
                'url': 'https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10440731.html',
                'parser': self.parse_addon_jinhakapply,
                'target_college': None,  # 크롤링 시 확인
                'target_departments': ['컴퓨터정보공학부']
            },
            'YNU': {  # 영남대학교
                'url': 'https://ratio.uwayapply.com/Sl5KOmJKZiUmOiZKLWZUZg==',
                'parser': self.parse_uwayapply,
                'target_college': '디지털융합대학',
                'target_departments': []  # 전체 학과 수집
            },
            'KMU': {  # 계명대학교
                'url': 'https://ratio.uwayapply.com/Sl5KOk05SmYlJjomSi1mVGY=',
                'parser': self.parse_uwayapply,
                'target_college': None,  # 크롤링 시 확인
                'target_departments': ['컴퓨터공학과', '게임소프트웨어', '모빌리티소프트웨어']
            }
        }
    
    def fetch_page(self, url: str) -> Optional[str]:
        """웹페이지를 가져옵니다."""
        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"페이지 요청 중 오류 발생 ({url}): {e}")
            return None
    
    def parse_addon_jinhakapply(self, html_content: str, university_code: str) -> List[Dict]:
        """addon.jinhakapply.com 사이트 파싱"""
        soup = BeautifulSoup(html_content, 'html.parser')
        competition_data = []
        
        # 전형별 패턴 정의
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
        
        config = self.university_configs[university_code]
        target_college = config['target_college']
        target_departments = config['target_departments']
        
        # 현재 전형 추적
        current_admission_type = '미분류'
        
        # HTML 전체에서 전형 정보 찾기
        html_text = soup.get_text()
        for admission_type, patterns in admission_type_patterns.items():
            if any(pattern in html_text for pattern in patterns):
                current_admission_type = admission_type
                break
        
        # 테이블 파싱
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # 헤더 건너뛰기
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # 대상 단과대학 확인
                    college_name = cell_texts[0]
                    if target_college and target_college not in college_name:
                        continue
                    
                    department_raw = cell_texts[1]
                    
                    # 대상 학과 확인
                    if target_departments:
                        is_target = any(target in department_raw for target in target_departments)
                        if not is_target:
                            continue
                    
                    try:
                        recruitment_count = self.extract_number(cell_texts[2])
                        applicant_count = self.extract_number(cell_texts[3])
                        
                        clean_department = self.clean_department_name(department_raw)
                        
                        competition_data.append({
                            'university_code': university_code,
                            'college': college_name,
                            'department': clean_department,
                            'admission_type': current_admission_type,
                            'recruitment_count': recruitment_count,
                            'applicant_count': applicant_count
                        })
                        
                    except (ValueError, IndexError) as e:
                        print(f"데이터 파싱 오류: {e} - {cell_texts}")
        
        return competition_data
    
    def parse_uwayapply(self, html_content: str, university_code: str) -> List[Dict]:
        """ratio.uwayapply.com 사이트 파싱 (영남대, 계명대)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        competition_data = []
        
        config = self.university_configs[university_code]
        target_college = config['target_college']
        target_departments = config['target_departments']
        
        # uwayapply 사이트의 HTML 구조에 맞게 파싱 로직 구현
        # 실제 사이트 구조 확인 후 구현 필요
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # 사이트별 구조에 맞게 조정 필요
                    if len(cell_texts) >= 5:
                        college_name = cell_texts[0]
                        department_raw = cell_texts[1]
                        
                        # 대상 단과대학 확인
                        if target_college and target_college not in college_name:
                            continue
                        
                        # 대상 학과 확인
                        if target_departments:
                            is_target = any(target in department_raw for target in target_departments)
                            if not is_target:
                                continue
                        elif university_code == 'YNU' and '디지털융합대학' in college_name:
                            # 영남대 디지털융합대학은 전체 학과 수집
                            pass
                        else:
                            continue
                        
                        try:
                            recruitment_count = self.extract_number(cell_texts[2])
                            applicant_count = self.extract_number(cell_texts[3])
                            
                            clean_department = self.clean_department_name(department_raw)
                            
                            competition_data.append({
                                'university_code': university_code,
                                'college': college_name,
                                'department': clean_department,
                                'admission_type': '일반전형',  # 기본값
                                'recruitment_count': recruitment_count,
                                'applicant_count': applicant_count
                            })
                            
                        except (ValueError, IndexError) as e:
                            print(f"데이터 파싱 오류: {e} - {cell_texts}")
        
        return competition_data
    
    def clean_department_name(self, department: str) -> str:
        """학과명을 정리합니다."""
        clean_dept = re.sub(r'교직|RIS사업|\s+', ' ', department).strip()
        
        # 표준 학과명으로 변환
        if '컴퓨터소프트웨어' in clean_dept:
            return '컴퓨터소프트웨어학부'
        elif 'AI빅데이터공학' in clean_dept:
            return 'AI빅데이터공학과'
        elif '소프트웨어융합' in clean_dept:
            return '소프트웨어융합학과'
        elif '컴퓨터정보공학' in clean_dept:
            return '컴퓨터정보공학부'
        elif '컴퓨터공학' in clean_dept:
            return '컴퓨터공학과'
        elif '게임소프트웨어' in clean_dept:
            return '게임소프트웨어학과'
        elif '모빌리티소프트웨어' in clean_dept:
            return '모빌리티소프트웨어학과'
        
        return clean_dept
    
    def extract_number(self, text: str) -> int:
        """텍스트에서 숫자를 추출합니다."""
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def get_or_create_ids(self, university_code: str, college_name: str, 
                         department_name: str, admission_type: str) -> Tuple[int, int, int, int]:
        """대학교, 단과대학, 학과, 전형 ID를 조회하거나 생성합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 대학교 ID 조회
        cursor.execute('SELECT id FROM universities WHERE code = ?', (university_code,))
        result = cursor.fetchone()
        university_id = result[0] if result else None
        
        if not university_id:
            print(f"대학교 코드 '{university_code}'를 찾을 수 없습니다.")
            conn.close()
            return None, None, None, None
        
        # 단과대학 ID 조회 또는 생성
        cursor.execute('''
            SELECT id FROM colleges 
            WHERE university_id = ? AND name = ?
        ''', (university_id, college_name))
        result = cursor.fetchone()
        
        if result:
            college_id = result[0]
        else:
            cursor.execute('''
                INSERT INTO colleges (university_id, name) 
                VALUES (?, ?)
            ''', (university_id, college_name))
            college_id = cursor.lastrowid
        
        # 학과 ID 조회 또는 생성
        cursor.execute('''
            SELECT id FROM departments 
            WHERE college_id = ? AND name = ?
        ''', (college_id, department_name))
        result = cursor.fetchone()
        
        if result:
            department_id = result[0]
        else:
            cursor.execute('''
                INSERT INTO departments (college_id, name, target_department) 
                VALUES (?, ?, TRUE)
            ''', (college_id, department_name))
            department_id = cursor.lastrowid
        
        # 전형 ID 조회 또는 생성
        cursor.execute('SELECT id FROM admission_types WHERE name = ?', (admission_type,))
        result = cursor.fetchone()
        
        if result:
            admission_type_id = result[0]
        else:
            cursor.execute('''
                INSERT INTO admission_types (name, category) 
                VALUES (?, ?)
            ''', (admission_type, '미분류'))
            admission_type_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return university_id, college_id, department_id, admission_type_id
    
    def save_competition_data(self, competition_data: List[Dict], session_id: str):
        """경쟁률 데이터를 데이터베이스에 저장합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for data in competition_data:
            ids = self.get_or_create_ids(
                data['university_code'],
                data['college'],
                data['department'],
                data['admission_type']
            )
            
            if any(id is None for id in ids):
                continue
            
            university_id, college_id, department_id, admission_type_id = ids
            
            try:
                cursor.execute('''
                    INSERT INTO competition_snapshots 
                    (university_id, college_id, department_id, admission_type_id,
                     recruitment_count, applicant_count, crawl_session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    university_id, college_id, department_id, admission_type_id,
                    data['recruitment_count'], data['applicant_count'], session_id
                ))
                saved_count += 1
                
            except sqlite3.Error as e:
                print(f"데이터 저장 오류: {e}")
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def crawl_university(self, university_code: str) -> bool:
        """특정 대학교의 경쟁률 데이터를 크롤링합니다."""
        config = self.university_configs.get(university_code)
        if not config:
            print(f"대학교 코드 '{university_code}' 설정을 찾을 수 없습니다.")
            return False
        
        # 크롤링 세션 시작
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 대학교 ID 조회
        cursor.execute('SELECT id FROM universities WHERE code = ?', (university_code,))
        result = cursor.fetchone()
        university_id = result[0] if result else None
        
        if not university_id:
            print(f"대학교 코드 '{university_code}'를 찾을 수 없습니다.")
            conn.close()
            return False
        
        # 크롤링 세션 로그 시작
        cursor.execute('''
            INSERT INTO crawl_sessions (id, university_id, status) 
            VALUES (?, ?, 'RUNNING')
        ''', (session_id, university_id))
        conn.commit()
        conn.close()
        
        try:
            print(f"{university_code} 대학교 크롤링 시작...")
            
            # 웹페이지 가져오기
            html_content = self.fetch_page(config['url'])
            if not html_content:
                self.update_session_status(session_id, 'FAILED', '웹페이지 로드 실패')
                return False
            
            # 데이터 파싱
            parser = config['parser']
            competition_data = parser(html_content, university_code)
            
            if not competition_data:
                self.update_session_status(session_id, 'COMPLETED', '수집된 데이터 없음')
                print(f"{university_code}: 수집된 데이터가 없습니다.")
                return True
            
            # 데이터 저장
            saved_count = self.save_competition_data(competition_data, session_id)
            
            # 세션 상태 업데이트
            self.update_session_status(session_id, 'COMPLETED', records_collected=saved_count)
            
            print(f"{university_code}: {saved_count}개 레코드 저장 완료")
            return True
            
        except Exception as e:
            self.update_session_status(session_id, 'FAILED', str(e))
            print(f"{university_code} 크롤링 중 오류: {e}")
            return False
    
    def update_session_status(self, session_id: str, status: str, error_message: str = None, records_collected: int = 0):
        """크롤링 세션 상태를 업데이트합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE crawl_sessions 
            SET end_time = CURRENT_TIMESTAMP, status = ?, 
                error_message = ?, records_collected = ?
            WHERE id = ?
        ''', (status, error_message, records_collected, session_id))
        
        conn.commit()
        conn.close()
    
    def crawl_all_universities(self):
        """모든 대학교의 경쟁률 데이터를 크롤링합니다."""
        print("=== 다중 대학교 경쟁률 크롤링 시작 ===")
        start_time = datetime.now()
        
        results = {}
        for university_code in self.university_configs.keys():
            results[university_code] = self.crawl_university(university_code)
            time.sleep(2)  # 요청 간 간격
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\\n=== 크롤링 결과 요약 ===")
        for university_code, success in results.items():
            status = "성공" if success else "실패"
            print(f"{university_code}: {status}")
        
        print(f"총 소요 시간: {duration:.1f}초")
        print("=== 크롤링 완료 ===")

if __name__ == "__main__":
    from enhanced_database_setup import create_enhanced_database, initialize_base_data, setup_target_departments
    
    # 데이터베이스 초기화
    create_enhanced_database()
    initialize_base_data()
    setup_target_departments()
    
    # 크롤링 실행
    crawler = MultiUniversityCrawler()
    crawler.crawl_all_universities()