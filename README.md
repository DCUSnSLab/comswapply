# 다중 대학교 경쟁률 크롤링 및 추세 분석 시스템

다중 대학교의 입시 경쟁률을 실시간으로 수집하고 시간별 변화 추이를 분석하는 향상된 Python 시스템입니다.

## 🎯 주요 기능

### 🕷️ 다중 대학교 크롤링
- **4개 대학교 동시 지원**: 가톨릭관동대, 대구대, 영남대, 계명대
- **실시간 데이터 수집**: 10분마다 자동 크롤링 (설정 가능)
- **스마트 파싱**: 사이트별 맞춤 파싱 로직
- **오류 복구**: 크롤링 실패 시 자동 재시도 및 로깅

### 📊 시간별 추세 분석
- **실시간 추적**: 지원자 수와 경쟁률 변화를 10분 단위로 추적
- **시각화**: matplotlib, plotly를 활용한 다양한 그래프
- **인터랙티브 대시보드**: 웹 기반 실시간 모니터링
- **추세 리포트**: 자동화된 분석 리포트 생성

### 🗄️ 고도화된 데이터베이스
- **정규화된 스키마**: 대학교, 학과, 전형별 체계적 관리  
- **시간별 스냅샷**: 모든 변화를 타임스탬프와 함께 저장
- **크롤링 세션 추적**: 각 크롤링의 성공/실패 로그 관리
- **MySQL 지원**: 향후 대용량 데이터 처리 준비

## 🎓 수집 대상 대학교

| 대학교 | 타겟 학과 | URL 유형 |
|--------|-----------|----------|
| **가톨릭관동대학교** | 컴퓨터소프트웨어학부, AI빅데이터공학과, 소프트웨어융합학과 | addon.jinhakapply |
| **대구대학교** | 컴퓨터정보공학부 | addon.jinhakapply |
| **영남대학교** | 디지털융합대학 전 학과 | uwayapply |
| **계명대학교** | 컴퓨터공학과, 게임소프트웨어학과, 모빌리티소프트웨어학과 | uwayapply |

## 📋 수집 전형 유형

- **학생부교과**: 교과전형, 지역교과전형, 가톨릭지도자추천전형, 특성화고전형, 기회균형전형, 지역기회균형전형, 농어촌, 기회균형선발전형, 성인학습자, 특성화고졸재직자
- **학생부종합**: 종합전형, 지역종합전형, SW전형

## 🔧 설치 및 설정

### 1. 필요한 패키지 설치

```bash
pip install requests beautifulsoup4 pandas lxml schedule matplotlib seaborn plotly
```

### 2. 데이터베이스 초기화

```bash
python3 scheduler.py --init-db
```

### 3. 실행 방법

#### 🔄 자동 스케줄링 (권장)
```bash
# 10분마다 자동 크롤링
python3 scheduler.py --mode schedule --interval 10

# 5분마다 자동 크롤링  
python3 scheduler.py --mode schedule --interval 5
```

#### 🎯 수동 실행
```bash
# 전체 대학교 1회 크롤링
python3 scheduler.py --mode once

# 특정 대학교만 크롤링
python3 scheduler.py --mode university --university CKU
python3 scheduler.py --mode university --university DGU
```

#### 📈 추세 분석 및 시각화
```bash
# 추세 분석 실행
python3 trend_analyzer.py
```

## 📁 향상된 파일 구조

```
├── enhanced_database_setup.py    # 향상된 DB 스키마 및 초기화
├── multi_university_crawler.py   # 다중 대학교 크롤링 엔진
├── scheduler.py                  # 자동 스케줄링 시스템
├── trend_analyzer.py            # 추세 분석 및 시각화
├── query_utils.py              # 데이터 조회 유틸리티 (업데이트됨)
├── competition_ratio_enhanced.db # 향상된 SQLite 데이터베이스
├── dashboard.html              # 인터랙티브 웹 대시보드
├── trend_report.txt           # 자동 생성 추세 리포트
└── *.png                     # 추세 그래프 이미지
```

## 🗃️ 향상된 데이터베이스 스키마

### 핵심 테이블 구조

```sql
-- 대학교 정보
CREATE TABLE universities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT UNIQUE,
    url TEXT
);

-- 경쟁률 스냅샷 (시간별 추적)
CREATE TABLE competition_snapshots (
    id INTEGER PRIMARY KEY,
    university_id INTEGER,
    college_id INTEGER, 
    department_id INTEGER,
    admission_type_id INTEGER,
    recruitment_count INTEGER,
    applicant_count INTEGER,
    competition_ratio REAL,  -- 자동 계산
    snapshot_time TIMESTAMP,
    crawl_session_id TEXT
);

-- 크롤링 세션 로그
CREATE TABLE crawl_sessions (
    id TEXT PRIMARY KEY,
    university_id INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT,
    records_collected INTEGER,
    error_message TEXT
);
```

## 📊 시각화 및 분석 기능

### 1. 실시간 추세 그래프
- 시간별 경쟁률 변화
- 지원자 수 증감 추이  
- 대학별/학과별 비교

### 2. 인터랙티브 대시보드
- 웹 기반 실시간 모니터링
- 줌/팬 가능한 차트
- 호버 정보 제공

### 3. 자동 리포트 생성
- 일일/주간 추세 요약
- 급격한 변화 감지
- 경쟁률 순위 분석

## 🚀 사용 예시

### 실시간 모니터링 시작
```python
from scheduler import CrawlingScheduler

# 5분마다 자동 크롤링 시작
scheduler = CrawlingScheduler(interval_minutes=5)
scheduler.run()  # Ctrl+C로 중지 가능
```

### 추세 분석
```python
from trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()

# 최근 24시간 데이터로 추세 그래프 생성
analyzer.plot_competition_trend(hours_back=24, save_path="trend.png")

# 인터랙티브 대시보드 생성
analyzer.create_interactive_dashboard(save_html="dashboard.html")

# 자동 리포트 생성
analyzer.generate_trend_report(save_path="report.txt")
```

### 특정 대학교 분석
```python
# 가톨릭관동대학교만 분석
analyzer.plot_competition_trend(
    university_code="CKU", 
    hours_back=12,
    save_path="cku_trend.png"
)
```

## ⚡ 고급 기능

### 1. 자동 알림 (확장 예정)
- 경쟁률 급변 시 이메일/슬랙 알림
- 특정 임계값 도달 시 알림
- 일일 요약 리포트 발송

### 2. 웹 인터페이스 (확장 예정)  
- Flask/Django 기반 웹 앱
- 실시간 대시보드
- 사용자 맞춤 알림 설정

### 3. 머신러닝 분석 (확장 예정)
- 경쟁률 예측 모델
- 지원 패턴 분석
- 이상치 탐지

## ⚙️ 설정 옵션

### 스케줄러 설정
```bash
# 사용법: python3 scheduler.py [옵션]
--mode {schedule,once,university}  # 실행 모드
--interval MINUTES                 # 크롤링 간격 (분)
--university {CKU,DGU,YNU,KMU}    # 특정 대학교 선택
--init-db                         # 데이터베이스 초기화
```

### 분석기 설정
```python
# TrendAnalyzer 옵션
hours_back=24        # 분석 기간 (시간)
university_code=None # 특정 대학교 필터
department_name=None # 특정 학과 필터
save_path=None      # 결과 저장 경로
```

## 🔍 모니터링 및 로깅

- **크롤링 상태**: 각 세션의 성공/실패 추적
- **오류 로깅**: 상세한 오류 메시지와 스택 트레이스
- **성능 모니터링**: 크롤링 소요 시간 및 처리량 추적
- **데이터 검증**: 수집된 데이터의 일관성 검사

## 🚨 주의사항

1. **서버 부하**: 크롤링 간격을 너무 짧게 설정하지 마세요 (최소 5분 권장)
2. **법적 준수**: 각 대학교의 robots.txt와 이용약관을 확인하세요
3. **데이터 백업**: 중요한 분석 결과는 정기적으로 백업하세요
4. **리소스 관리**: 장기간 실행 시 메모리 사용량을 모니터링하세요

## 🛠️ 문제 해결

### 크롤링 실패
```bash
# 로그 확인
python3 -c "
import sqlite3
conn = sqlite3.connect('competition_ratio_enhanced.db')
df = pd.read_sql('SELECT * FROM crawl_sessions ORDER BY start_time DESC LIMIT 10', conn)
print(df)
"
```

### 데이터베이스 재초기화
```bash
rm competition_ratio_enhanced.db
python3 scheduler.py --init-db
```

## 📈 확장 계획

- [ ] 더 많은 대학교 추가
- [ ] 실시간 웹 대시보드 구축
- [ ] 모바일 알림 연동
- [ ] AWS/클라우드 배포
- [ ] 예측 모델링 추가
- [ ] API 서버 구축

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 상업적 사용 시 각 대학교의 데이터 사용 정책을 확인하세요.