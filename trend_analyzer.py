import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'NanumGothic', 'Malgun Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class TrendAnalyzer:
    def __init__(self, db_path='competition_ratio_enhanced.db'):
        self.db_path = db_path
        
    def get_time_series_data(self, university_code=None, department_name=None, 
                           admission_type=None, hours_back=24):
        """시간별 경쟁률 변화 데이터를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        # 기본 쿼리
        query = """
        SELECT 
            cs.snapshot_time,
            u.name as university_name,
            u.code as university_code,
            c.name as college_name,
            d.name as department_name,
            at.name as admission_type,
            cs.recruitment_count,
            cs.applicant_count,
            cs.competition_ratio
        FROM competition_snapshots cs
        JOIN universities u ON cs.university_id = u.id
        JOIN colleges c ON cs.college_id = c.id
        JOIN departments d ON cs.department_id = d.id
        JOIN admission_types at ON cs.admission_type_id = at.id
        WHERE cs.snapshot_time >= datetime('now', '-{} hours')
        """.format(hours_back)
        
        # 조건 추가
        params = []
        if university_code:
            query += " AND u.code = ?"
            params.append(university_code)
        if department_name:
            query += " AND d.name = ?"
            params.append(department_name)
        if admission_type:
            query += " AND at.name = ?"
            params.append(admission_type)
            
        query += " ORDER BY cs.snapshot_time ASC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['snapshot_time'] = pd.to_datetime(df['snapshot_time'])
        
        return df
    
    def get_latest_stats(self):
        """최신 통계를 조회합니다."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        WITH latest_snapshots AS (
            SELECT 
                university_id, department_id, admission_type_id,
                MAX(snapshot_time) as latest_time
            FROM competition_snapshots 
            GROUP BY university_id, department_id, admission_type_id
        )
        SELECT 
            u.name as university_name,
            u.code as university_code,
            d.name as department_name,
            at.name as admission_type,
            cs.recruitment_count,
            cs.applicant_count,
            cs.competition_ratio,
            cs.snapshot_time
        FROM competition_snapshots cs
        JOIN latest_snapshots ls ON (
            cs.university_id = ls.university_id 
            AND cs.department_id = ls.department_id
            AND cs.admission_type_id = ls.admission_type_id
            AND cs.snapshot_time = ls.latest_time
        )
        JOIN universities u ON cs.university_id = u.id
        JOIN departments d ON cs.department_id = d.id
        JOIN admission_types at ON cs.admission_type_id = at.id
        ORDER BY u.name, d.name, at.name
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def plot_competition_trend(self, university_code=None, department_name=None, 
                              hours_back=24, save_path=None):
        """경쟁률 추세를 시각화합니다."""
        df = self.get_time_series_data(university_code, department_name, hours_back=hours_back)
        
        if df.empty:
            print("시각화할 데이터가 없습니다.")
            return None
        
        # 그룹별로 데이터 분리
        groups = df.groupby(['university_code', 'department_name', 'admission_type'])
        
        plt.figure(figsize=(15, 8))
        
        colors = plt.cm.Set3(range(len(groups)))
        
        for i, ((univ, dept, adm_type), group) in enumerate(groups):
            label = f"{univ}-{dept}-{adm_type}"
            plt.plot(group['snapshot_time'], group['competition_ratio'], 
                    marker='o', label=label, color=colors[i], linewidth=2, markersize=4)
        
        plt.title(f'경쟁률 변화 추이 (최근 {hours_back}시간)', fontsize=16, fontweight='bold')
        plt.xlabel('시간', fontsize=12)
        plt.ylabel('경쟁률', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # x축 시간 포맷
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프가 {save_path}에 저장되었습니다.")
        
        plt.show()
        return plt.gcf()
    
    def plot_applicant_trend(self, university_code=None, department_name=None, 
                           hours_back=24, save_path=None):
        """지원자 수 변화 추세를 시각화합니다."""
        df = self.get_time_series_data(university_code, department_name, hours_back=hours_back)
        
        if df.empty:
            print("시각화할 데이터가 없습니다.")
            return None
        
        groups = df.groupby(['university_code', 'department_name', 'admission_type'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        colors = plt.cm.Set3(range(len(groups)))
        
        # 지원자 수 추이
        for i, ((univ, dept, adm_type), group) in enumerate(groups):
            label = f"{univ}-{dept}-{adm_type}"
            ax1.plot(group['snapshot_time'], group['applicant_count'], 
                    marker='o', label=label, color=colors[i], linewidth=2, markersize=4)
        
        ax1.set_title(f'지원자 수 변화 추이 (최근 {hours_back}시간)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('지원자 수', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 경쟁률 추이
        for i, ((univ, dept, adm_type), group) in enumerate(groups):
            ax2.plot(group['snapshot_time'], group['competition_ratio'], 
                    marker='s', color=colors[i], linewidth=2, markersize=4)
        
        ax2.set_title('경쟁률 변화 추이', fontsize=14, fontweight='bold')
        ax2.set_xlabel('시간', fontsize=12)
        ax2.set_ylabel('경쟁률', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # x축 시간 포맷
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"그래프가 {save_path}에 저장되었습니다.")
        
        plt.show()
        return fig
    
    def create_interactive_dashboard(self, hours_back=24, save_html=None):
        """인터랙티브 대시보드를 생성합니다."""
        df = self.get_time_series_data(hours_back=hours_back)
        
        if df.empty:
            print("시각화할 데이터가 없습니다.")
            return None
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('경쟁률 변화', '지원자 수 변화', '대학별 현재 경쟁률', '전형별 지원자 분포'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        # 색상 팔레트
        colors = px.colors.qualitative.Set3
        
        # 1. 경쟁률 변화 추이
        groups = df.groupby(['university_code', 'department_name', 'admission_type'])
        for i, ((univ, dept, adm_type), group) in enumerate(groups):
            fig.add_trace(
                go.Scatter(
                    x=group['snapshot_time'],
                    y=group['competition_ratio'],
                    mode='lines+markers',
                    name=f"{univ}-{dept}",
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='%{y:.3f}:1<br>%{x}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # 2. 지원자 수 변화
        for i, ((univ, dept, adm_type), group) in enumerate(groups):
            fig.add_trace(
                go.Scatter(
                    x=group['snapshot_time'],
                    y=group['applicant_count'],
                    mode='lines+markers',
                    name=f"{univ}-{dept}",
                    line=dict(color=colors[i % len(colors)]),
                    showlegend=False,
                    hovertemplate='%{y}명<br>%{x}<extra></extra>'
                ),
                row=1, col=2
            )
        
        # 3. 대학별 현재 경쟁률 (최신 데이터)
        latest_df = self.get_latest_stats()
        if not latest_df.empty:
            fig.add_trace(
                go.Bar(
                    x=latest_df['department_name'],
                    y=latest_df['competition_ratio'],
                    text=[f"{x:.2f}:1" for x in latest_df['competition_ratio']],
                    textposition='auto',
                    showlegend=False,
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
        
        # 4. 전형별 지원자 분포
        if not latest_df.empty:
            admission_stats = latest_df.groupby('admission_type')['applicant_count'].sum().reset_index()
            fig.add_trace(
                go.Pie(
                    labels=admission_stats['admission_type'],
                    values=admission_stats['applicant_count'],
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 레이아웃 업데이트
        fig.update_layout(
            height=800,
            title_text=f"대학교 경쟁률 종합 대시보드 (최근 {hours_back}시간)",
            title_x=0.5,
            showlegend=True
        )
        
        # x축, y축 레이블 추가
        fig.update_xaxes(title_text="시간", row=1, col=1)
        fig.update_xaxes(title_text="시간", row=1, col=2)
        fig.update_xaxes(title_text="학과", row=2, col=1)
        
        fig.update_yaxes(title_text="경쟁률", row=1, col=1)
        fig.update_yaxes(title_text="지원자 수", row=1, col=2)
        fig.update_yaxes(title_text="경쟁률", row=2, col=1)
        
        if save_html:
            fig.write_html(save_html)
            print(f"인터랙티브 대시보드가 {save_html}에 저장되었습니다.")
        
        fig.show()
        return fig
    
    def generate_trend_report(self, hours_back=24, save_path=None):
        """추세 분석 리포트를 생성합니다."""
        df = self.get_time_series_data(hours_back=hours_back)
        latest_df = self.get_latest_stats()
        
        report = []
        report.append("=" * 80)
        report.append("대학교 경쟁률 추세 분석 리포트")
        report.append("=" * 80)
        report.append(f"분석 기간: 최근 {hours_back}시간")
        report.append(f"리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if df.empty:
            report.append("분석할 데이터가 없습니다.")
        else:
            # 전체 통계
            total_snapshots = len(df)
            universities = df['university_name'].nunique()
            departments = df['department_name'].nunique()
            
            report.append(f"📊 전체 통계")
            report.append(f"   데이터 스냅샷: {total_snapshots:,}개")
            report.append(f"   대학교 수: {universities}개")
            report.append(f"   학과 수: {departments}개")
            report.append("")
            
            # 대학별 현재 상황
            if not latest_df.empty:
                report.append("🏛️ 대학별 현재 경쟁률 현황")
                for univ in latest_df['university_name'].unique():
                    univ_data = latest_df[latest_df['university_name'] == univ]
                    report.append(f"   {univ}")
                    
                    for _, row in univ_data.iterrows():
                        report.append(f"     - {row['department_name']} ({row['admission_type']})")
                        report.append(f"       모집: {row['recruitment_count']}명, 지원: {row['applicant_count']}명")
                        report.append(f"       경쟁률: {row['competition_ratio']:.3f}:1")
                    report.append("")
            
            # 변화 추이 분석
            report.append("📈 변화 추이 분석")
            groups = df.groupby(['university_code', 'department_name', 'admission_type'])
            
            for (univ, dept, adm_type), group in groups:
                if len(group) >= 2:
                    first_ratio = group.iloc[0]['competition_ratio']
                    last_ratio = group.iloc[-1]['competition_ratio']
                    first_applicants = group.iloc[0]['applicant_count']
                    last_applicants = group.iloc[-1]['applicant_count']
                    
                    ratio_change = last_ratio - first_ratio
                    applicant_change = last_applicants - first_applicants
                    
                    trend = "🔴" if ratio_change > 0.01 else "🟡" if ratio_change > -0.01 else "🟢"
                    
                    report.append(f"   {trend} {univ} - {dept} ({adm_type})")
                    report.append(f"     경쟁률 변화: {first_ratio:.3f}:1 → {last_ratio:.3f}:1 ({ratio_change:+.3f})")
                    report.append(f"     지원자 변화: {first_applicants}명 → {last_applicants}명 ({applicant_change:+d})")
                    report.append("")
        
        report_text = "\\n".join(report)
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"리포트가 {save_path}에 저장되었습니다.")
        
        print(report_text)
        return report_text

def main():
    """메인 함수 - 사용 예시"""
    analyzer = TrendAnalyzer()
    
    print("=== 대학교 경쟁률 추세 분석 ===")
    
    # 1. 추세 분석 리포트 생성
    analyzer.generate_trend_report(hours_back=24, save_path="trend_report.txt")
    
    # 2. 경쟁률 추세 그래프
    print("\\n경쟁률 추세 그래프 생성 중...")
    analyzer.plot_competition_trend(hours_back=24, save_path="competition_trend.png")
    
    # 3. 지원자 수 추세 그래프
    print("지원자 수 추세 그래프 생성 중...")
    analyzer.plot_applicant_trend(hours_back=24, save_path="applicant_trend.png")
    
    # 4. 인터랙티브 대시보드
    print("인터랙티브 대시보드 생성 중...")
    analyzer.create_interactive_dashboard(hours_back=24, save_html="dashboard.html")

if __name__ == "__main__":
    main()