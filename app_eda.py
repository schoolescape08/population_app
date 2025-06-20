import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population Trends 데이터셋**   
                - 설명: 2008–2023년 한국에서 지역별 인구수, 출생아수, 사망자수를 기록한 데이터  
                - 주요 변수:  
                  - `연도`: 연도 ex)2008 
                  - `지역`: 전국 또는 특정 지역 ex)대
                  - `인구`: 해당 연도와 해당 지역의 총 인구  
                  - `출생아수(명)`: 해당 연도와 지역의 출생아 수  
                  - `사망자수(명)`: 해당 연도와 지역의 사망자 수
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['연도'])

        # 1) 세종 지역 결측치 '-' → 0 치환, 주요 열 숫자형 변환
        mask_sejong = df['지역'] == '세종'
        df.loc[mask_sejong, :] = df.loc[mask_sejong, :].replace('-', 0)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)

        # 탭 구성
        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화"
        ])

        # 탭 0: 기초 통계
        with tabs[0]:
            st.header("🔍 Data Overview")
            # df.info()
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.subheader("DataFrame Info")
            st.text(buffer.getvalue())
            # df.describe()
            st.subheader("Summary Statistics")
            st.dataframe(df.describe())

        # 탭 1: 연도별 추이 & 2035 예측
        with tabs[1]:
            st.header("📈 Nationwide Population Trend & Prediction")
            df_nat = df[df['지역'] == '전국'].sort_values('연도')

            # 연도별 실제 인구 추이
            fig1, ax1 = plt.subplots()
            sns.lineplot(
                data=df_nat, x='연도', y='인구',
                marker='o', ax=ax1, label='Actual'
            )
            ax1.set_title('Population Trend')
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Population')
            st.pyplot(fig1)

            # 최근 3년 평균 인구 증감 = births - deaths 의 평균
            recent = df_nat.tail(3)
            avg_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = recent['연도'].iloc[-1]
            last_pop = recent['인구'].iloc[-1]

            years_pred = list(range(last_year + 1, 2036))
            pops_pred = [last_pop + avg_change * (y - last_year) for y in years_pred]
            df_pred = pd.DataFrame({'연도': years_pred, 'Population': pops_pred})

            # 실제 + 예측 추이
            fig2, ax2 = plt.subplots()
            sns.lineplot(
                data=df_nat, x='연도', y='인구',
                marker='o', ax=ax2, label='Actual'
            )
            sns.lineplot(
                data=df_pred, x='연도', y='Population',
                marker='o', ax=ax2, label='Predicted'
            )
            ax2.set_title('Population with 2035 Prediction')
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Population')
            st.pyplot(fig2)

        # 탭 2: 지역별 분석 (최근 5년 증감량 & 변화율)
        with tabs[2]:
            st.header("🌐 Regional 5-Year Change Analysis")
            # 영어 지역명 매핑 (필요에 따라 추가)
            region_map = {
                '세종': 'Sejong',
                '서울': 'Seoul',
                '부산': 'Busan',
                # ...
            }
            df['region_en'] = df['지역'].map(region_map).fillna(df['지역'])

            # 최근 5년간 인구 변화량
            latest_year = df['연도'].max()
            df_5yr = df[df['연도'].isin([latest_year-5, latest_year])]
            change5 = (df_5yr[df_5yr['연도'] == latest_year]
                       .set_index('region_en')['인구']
                     - df_5yr[df_5yr['연도'] == latest_year-5]
                       .set_index('region_en')['인구'])
            change5 = change5.drop(index='전국', errors='ignore').sort_values(ascending=False)
            change5_thousands = change5 / 1_000

            # 수평 막대 차트
            fig3, ax3 = plt.subplots(figsize=(8, len(change5_thousands)*0.3))
            sns.barplot(
                x=change5_thousands.values,
                y=change5_thousands.index,
                orient='h',
                ax=ax3
            )
            for i, v in enumerate(change5_thousands.values):
                ax3.text(v + 0.1, i, f"{v:.1f}", va='center')
            ax3.set_title('5-Year Population Change')
            ax3.set_xlabel('Change (thousands)')
            ax3.set_ylabel('')
            st.pyplot(fig3)
            st.markdown("""
            **해설:**  
            - 각 막대는 해당 지역의 최근 5년간 인구 증감량(천명 단위)을 나타낸다.  
            - 오른쪽으로 길수록 인구가 증가했음을 의미한다.
            """)

            # 변화율 계산
            pct_change5 = (change5 / (df_5yr[df_5yr['연도'] == latest_year-5]
                                      .set_index('region_en')['인구'])) * 100
            pct_change5 = pct_change5.sort_values(ascending=False)

            fig4, ax4 = plt.subplots(figsize=(8, len(pct_change5)*0.3))
            sns.barplot(
                x=pct_change5.values,
                y=pct_change5.index,
                orient='h',
                ax=ax4
            )
            for i, v in enumerate(pct_change5.values):
                ax4.text(v + 0.1, i, f"{v:.1f}%", va='center')
            ax4.set_title('5-Year Population Change Rate')
            ax4.set_xlabel('Change Rate (%)')
            ax4.set_ylabel('')
            st.pyplot(fig4)
            st.markdown("""
            **해설:**  
            - 변화율은 5년 전 인구 대비 증감 비율을 백분율로 나타낸다.  
            - 상대적으로 더 큰 성장 또는 감소를 파악할 수 있다.
            """)

        # 탭 3: 변화량 분석 (Top 100 사례 테이블)
        with tabs[3]:
            st.header("📋 Top 100 Year-over-Year Changes")
            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['diff'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = (df_sorted[df_sorted['지역'] != '전국']
                      .dropna(subset=['diff'])
                      .sort_values('diff', ascending=False)
                      .head(100)
                      [['연도', 'region_en', '인구', 'diff']]
                      .rename(columns={'region_en':'Region'}))
            top100['diff'] = top100['diff'].astype(int)
            # 포맷팅 및 컬러바 스타일
            styled = (top100.style
                      .format({'diff':'{:,}'})
                      .background_gradient(
                          subset=['diff'], cmap='RdBu', axis=0
                      ))
            st.write(styled)

        # 탭 4: 시각화 (피벗 & 누적 영역 그래프)
        with tabs[4]:
            st.header("🗺️ Cumulative Area Chart by Region")
            df_pivot = (df[df['지역'] != '전국']
                        .pivot(index='연도', columns='region_en', values='인구')
                        .fillna(method='ffill'))
            fig5, ax5 = plt.subplots(figsize=(10, 6))
            ax5.stackplot(
                df_pivot.index, df_pivot.T.values,
                labels=df_pivot.columns
            )
            ax5.set_title('Population by Region (Stacked Area)')
            ax5.set_xlabel('Year')
            ax5.set_ylabel('Population')
            ax5.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
            st.pyplot(fig5)



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()