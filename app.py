import streamlit as st

# PWA 설정을 위한 HTML 주입
st.markdown(
    """
    <link rel="manifest" href="/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
      }
    </script>
    """,
    unsafe_allow_html=True
)

# ... 기존 코드 시작 (st.set_page_config 등)
import streamlit as st

# 종합소득세 및 보험료 계산 함수
def get_personal_biz_tax(profit):
    if profit <= 0: return 0
    if profit <= 14000000: tax = profit * 0.06
    elif profit <= 50000000: tax = profit * 0.15 - 1260000
    elif profit <= 88000000: tax = profit * 0.24 - 5760000
    elif profit <= 150000000: tax = profit * 0.35 - 15440000
    elif profit <= 300000000: tax = profit * 0.38 - 19940000
    elif profit <= 500000000: tax = profit * 0.40 - 25940000
    elif profit <= 1000000000: tax = profit * 0.42 - 35940000
    else: tax = profit * 0.45 - 65940000
    return (tax * 1.1) + (profit * 0.09) # 종소세+지방세+본인보험료 9%

# 웹 페이지 설정
st.set_page_config(page_title="맨홀 정산 시스템 v2.3", layout="wide")
st.title("🏗️ 맨홀 정산 시스템 (통합 상세 버전)")

# [1] 본사 설정
with st.sidebar:
    st.header("[1] 본사 설정")
    total_m = st.number_input("총 맨홀 개수", value=600)
    hq_p = st.number_input("수주 단가", value=500000)
    mat_p = st.number_input("개당 재료비", value=50000)
    u_tax_i = st.number_input("직원 소득세율(%)", value=3.0) / 100

# [2] 하청/직영 팀 입력
col1, col2 = st.columns(2)

with col1:
    st.header("[2] 하청 팀 (B2B)")
    b2b_data = []
    for i in range(5):
        with st.expander(f"하청 {i+1}팀 설정"):
            lp = st.number_input(f"{i+1}팀 팀장 단가", value=0, key=f"lp{i}")
            mp = st.number_input(f"{i+1}팀 팀원 단가", value=0, key=f"mp{i}")
            if lp > 0: b2b_data.append({'id': i+1, 'lp': lp, 'mp': mp})

with col2:
    st.header("[3] 본사 직영 팀")
    dir_data = []
    for i in range(5):
        with st.expander(f"직영 {i+1}팀 설정"):
            p1 = st.number_input(f"직영{i+1}조원1 단가", value=0, key=f"p1{i}")
            t1 = st.selectbox(f"조원1 타입", ["프리", "직원"], key=f"t1{i}")
            p2 = st.number_input(f"직영{i+1}조원2 단가", value=0, key=f"p2{i}")
            t2 = st.selectbox(f"조원2 타입", ["프리", "직원"], key=f"t2{i}")
            if p1 > 0: dir_data.append({'id': i+1, 'p1': p1, 't1': t1, 'p2': p2, 't2': t2})

# [4] 계산하기
if st.button("📊 정산 실행 및 리포트 생성", use_container_width=True):
    total_teams = len(b2b_data) + len(dir_data)
    if total_teams == 0:
        st.error("활성화된 팀이 없습니다.")
    else:
        m_per_team = total_m / total_teams
        hq_total_sales = hq_p * total_m
        hq_total_mat = mat_p * total_m
        
        # 근로자 공제 요율 (4대보험 + 소득세)
        emp_ded_rate = 0.045 + 0.03545 + (0.03545 * 0.1295) + 0.009 + u_tax_i + (u_tax_i * 0.1)
        
        total_hq_payout = 0
        report = f"[2025-11-18 정산 보고서]\n"
        report += f"총 맨홀: {total_m}개 / 팀당 배정: {m_per_team:.1f}개\n\n"
        
        # [A] 하청 팀 정산 내역 추가
        report += "■ 하청 팀(B2B) 내역\n"
        for team in b2b_data:
            l_pre = team['lp'] * m_per_team
            m_pre = team['mp'] * m_per_team
            total_hq_payout += (l_pre + m_pre)
            l_net = l_pre - get_personal_biz_tax(l_pre)
            m_net = m_pre * (1 - emp_ded_rate)
            report += f"- {team['id']}팀: 총지급 {l_pre+m_pre:,.0f}원\n"
            report += f"  (팀장세후: {l_net:,.0f} / 팀원세후: {m_net:,.0f})\n"
            
        # [B] 직영 팀 정산 내역 추가
        report += "\n■ 본사 직영 팀 내역\n"
        for team in dir_data:
            report += f"- 직영 {team['id']}팀 정산:\n"
            for p, t in [(team['p1'], team['t1']), (team['p2'], team['t2'])]:
                pre = p * m_per_team
                if t == "직원":
                    net = pre * (1 - emp_ded_rate)
                    hq_ins = pre * 0.104
                    total_hq_payout += (pre + hq_ins)
                else:
                    net = pre * (1 - 0.033)
                    total_hq_payout += pre
                report += f"  └ 조원: 세전 {pre:,.0f} / 세후 {net:,.0f} ({t})\n"
        
        # [C] 본사 재무 요약
        op_profit = hq_total_sales - hq_total_mat - total_hq_payout
        hq_tax = get_personal_biz_tax(op_profit)
        final_net = op_profit - hq_tax
        
        summary = f"\n{'='*40}\n"
        summary += f"1. 본사 총 매출: {hq_total_sales:,.0f}원\n"
        summary += f"2. 본사 총 비용: {hq_total_mat + total_hq_payout:,.0f}원\n"
        summary += f"3. 본사 영업이익(세전): {op_profit:,.0f}원\n"
        summary += f"4. 예상 세금/보험료: {hq_tax:,.0f}원\n"
        summary += f"5. 최종 순이익(세후): {final_net:,.0f}원\n"
        summary += f"최종 마진율: {(final_net/hq_total_sales*100):.1f}%\n"
        
        full_report = report + summary
        
        st.success(f"### 💰 사장님 최종 순이익: {final_net:,.0f}원")
        st.text_area("상세 리포트 결과 (복사 가능)", full_report, height=450)

        st.download_button("📥 보고서(.txt) 다운로드", full_report, file_name="정산보고서.txt")
