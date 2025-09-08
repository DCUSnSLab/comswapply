import requests
from bs4 import BeautifulSoup
import re

class DGUDebugCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.url = "https://addon.jinhakapply.com/RatioV1/RatioH/Ratio10440731.html"
        
        # 대구대학교 타겟 정보
        self.target_college = 'IT·공과대학'
        self.target_department = '컴퓨터정보공학부'
        self.target_majors = ['컴퓨터공학전공', '컴퓨터소프트웨어전공', '사이버보안전공']
    
    def fetch_page(self):
        """웹페이지를 가져옵니다."""
        try:
            response = self.session.get(self.url)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"페이지 요청 중 오류 발생: {e}")
            return None
    
    def extract_number(self, text):
        """텍스트에서 숫자를 추출합니다."""
        numbers = re.findall(r'\d+', text.replace(',', ''))
        return int(numbers[0]) if numbers else 0
    
    def debug_find_target_data(self, html_content):
        """대구대학교 컴퓨터정보공학부 데이터를 찾기 위한 디버그 함수"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("=== 대구대학교 데이터 찾기 디버그 ===")
        print(f"대상 단과대학: {self.target_college}")
        print(f"대상 학부: {self.target_department}")
        print(f"대상 전공: {self.target_majors}")
        print()
        
        # 모든 테이블 찾기
        tables = soup.find_all('table')
        print(f"총 {len(tables)}개의 테이블을 찾았습니다.")
        
        found_data = []
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- 테이블 {table_idx + 1} 분석 ---")
            rows = table.find_all('tr')
            print(f"행 수: {len(rows)}")
            
            # 전형 정보 찾기
            admission_type = self.find_admission_type_in_context(table)
            print(f"감지된 전형: {admission_type}")
            
            it_college_found = False
            computer_dept_found = False
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # IT·공과대학 찾기
                    if any(self.target_college in cell for cell in cell_texts):
                        it_college_found = True
                        print(f"  ✅ {self.target_college} 발견 (행 {row_idx + 1}): {cell_texts}")
                    
                    # 컴퓨터정보공학부 찾기
                    if any(self.target_department in cell for cell in cell_texts):
                        computer_dept_found = True
                        print(f"  ✅ {self.target_department} 발견 (행 {row_idx + 1}): {cell_texts}")
                        
                        if len(cell_texts) >= 5:
                            try:
                                college = cell_texts[0]
                                department = cell_texts[1]
                                recruitment = self.extract_number(cell_texts[2])
                                applicant = self.extract_number(cell_texts[3])
                                ratio = applicant / recruitment if recruitment > 0 else 0.0
                                
                                found_data.append({
                                    'college': college,
                                    'department': department,
                                    'admission_type': admission_type,
                                    'recruitment_count': recruitment,
                                    'applicant_count': applicant,
                                    'competition_ratio': ratio
                                })
                                
                                print(f"    📊 데이터 수집: {department} | {admission_type}")
                                print(f"        모집: {recruitment}명, 지원: {applicant}명, 경쟁률: {ratio:.3f}:1")
                                
                            except (ValueError, IndexError) as e:
                                print(f"    ❌ 데이터 파싱 오류: {e}")
                    
                    # 세부 전공들 찾기
                    for major in self.target_majors:
                        if any(major in cell for cell in cell_texts):
                            print(f"  ✅ {major} 발견 (행 {row_idx + 1}): {cell_texts}")
                            
                            if len(cell_texts) >= 5:
                                try:
                                    college = cell_texts[0] if cell_texts[0] else self.target_college
                                    department = f"{self.target_department}({major})"
                                    recruitment = self.extract_number(cell_texts[2])
                                    applicant = self.extract_number(cell_texts[3])
                                    ratio = applicant / recruitment if recruitment > 0 else 0.0
                                    
                                    found_data.append({
                                        'college': college,
                                        'department': department,
                                        'admission_type': admission_type,
                                        'recruitment_count': recruitment,
                                        'applicant_count': applicant,
                                        'competition_ratio': ratio
                                    })
                                    
                                    print(f"    📊 데이터 수집: {department} | {admission_type}")
                                    print(f"        모집: {recruitment}명, 지원: {applicant}명, 경쟁률: {ratio:.3f}:1")
                                    
                                except (ValueError, IndexError) as e:
                                    print(f"    ❌ 데이터 파싱 오류: {e}")
            
            if not it_college_found and not computer_dept_found:
                print(f"  ❌ 테이블 {table_idx + 1}에서 관련 데이터 없음")
        
        print(f"\n=== 최종 결과 ===")
        print(f"총 {len(found_data)}개의 데이터를 찾았습니다.")
        
        if found_data:
            print("\n수집된 데이터:")
            for idx, data in enumerate(found_data, 1):
                print(f"{idx}. {data['college']} > {data['department']}")
                print(f"   전형: {data['admission_type']}")
                print(f"   모집: {data['recruitment_count']}명, 지원: {data['applicant_count']}명")
                print(f"   경쟁률: {data['competition_ratio']:.3f}:1")
                print()
        else:
            print("❌ 수집된 데이터가 없습니다!")
            
        return found_data
    
    def find_admission_type_in_context(self, element):
        """요소의 컨텍스트에서 전형 타입을 찾습니다."""
        admission_patterns = {
            '학생부교과(교과전형)': ['교과전형', '학생부교과'],
            '학생부교과(지역교과전형)': ['지역교과전형'],
            '학생부종합(종합전형)': ['종합전형', '학생부종합'],
            '학생부종합(지역종합전형)': ['지역종합전형'],
            '실기/실적': ['실기', '실적'],
            '장애인등대상자': ['장애인'],
        }
        
        context_text = ""
        current = element
        for _ in range(10):
            current = current.find_previous_sibling()
            if current:
                context_text += " " + current.get_text()
            else:
                break
        
        parent = element.parent
        if parent:
            context_text += " " + parent.get_text()
        
        for admission_type, patterns in admission_patterns.items():
            if any(pattern in context_text for pattern in patterns):
                return admission_type
        
        return '일반전형'
    
    def run_debug(self):
        """디버그 크롤링을 실행합니다."""
        print("대구대학교 컴퓨터정보공학부 디버그 크롤링 시작")
        print(f"URL: {self.url}")
        print()
        
        html_content = self.fetch_page()
        if not html_content:
            print("❌ 웹페이지를 가져올 수 없습니다.")
            return
        
        found_data = self.debug_find_target_data(html_content)
        
        if found_data:
            print("✅ 디버그 완료 - 데이터 발견!")
        else:
            print("❌ 디버그 완료 - 데이터를 찾을 수 없습니다.")

if __name__ == "__main__":
    crawler = DGUDebugCrawler()
    crawler.run_debug()