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

        # CSV 읽기 (parse_dates 옵션 제거)
        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 결측치 및 중복 확인",
            "2. 연도별 전체 인구 추이 그래프",
            "3. 지역별 인구 변화량 순위",
            "4. 증감률 상위 지역 및 연도 도출",
            "5. 누적영역그래프 등 적절한 시각화"
        ])

        # 1. 결측치 및 중복 확인
        with tabs[0]:
            st.header("결측치 및 중복 확인")
            # '세종' 지역의 '-' → 0 치환
            df.loc[df['지역']=='세종', :] = df.loc[df['지역']=='세종', :].replace('-', 0)
            # 지정 열을 숫자로 변환
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            st.subheader("데이터 요약 통계")
            st.write(df[['인구', '출생아수(명)', '사망자수(명)']].describe())
            st.subheader("데이터 구조 정보")
            import io
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())

        # 2. 연도별 전체 인구 추이 그래프
        with tabs[1]:
            st.header("연도별 전체 인구 추이 그래프")
            national = df[df['지역']=='전국'].sort_values('연도')
            years = national['연도']
            pop = national['인구']
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot(years, pop, marker='o', label='Population')
            # 최근 3년 출생자–사망자 평균으로 2035년 예측
            recent = national.tail(3)
            avg_net = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = int(years.max())
            pred_year = 2035
            pop_last = pop.iloc[-1]
            pred_pop = pop_last + avg_net * (pred_year - last_year)
            ax.plot([last_year, pred_year], [pop_last, pred_pop],
                    linestyle='--', marker='o', label='Projection')
            ax.scatter(pred_year, pred_pop)
            ax.set_title("Yearly Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # 3. 지역별 인구 변화량 순위
        with tabs[2]:
            st.header("지역별 인구 변화량 순위")
            max_year = df['연도'].max()
            prev_year = max_year - 5
            df_latest = df[(df['연도']==max_year) & (df['지역']!='전국')]
            df_prev   = df[(df['연도']==prev_year) & (df['지역']!='전국')]
            change = pd.merge(
                df_latest[['지역','인구']],
                df_prev[['지역','인구']],
                on='지역',
                suffixes=('_latest','_prev')
            )
            change['change'] = change['인구_latest'] - change['인구_prev']
            change['change_thousands'] = change['change'] / 1000
            change['pct_change'] = change['change'] / change['인구_prev'] * 100
            kor_to_eng = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
                '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
                '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam',
                '제주':'Jeju'
            }
            change['Region'] = change['지역'].map(kor_to_eng)
            change_sorted = change.sort_values('change', ascending=False)
            import seaborn as sns
            import matplotlib.pyplot as plt
            # 절대 변화량 (천 단위)
            fig1, ax1 = plt.subplots()
            sns.barplot(
                x='change_thousands', y='Region',
                data=change_sorted, ax=ax1
            )
            for i, v in enumerate(change_sorted['change_thousands']):
                ax1.text(v, i, f"{v:.1f}")
            ax1.set_title("Population Change over Last 5 Years")
            ax1.set_xlabel("Change (thousands)")
            st.pyplot(fig1)
            # 변화율 (%)
            fig2, ax2 = plt.subplots()
            sns.barplot(
                x='pct_change', y='Region',
                data=change_sorted, ax=ax2
            )
            for i, v in enumerate(change_sorted['pct_change']):
                ax2.text(v, i, f"{v:.1f}%")
            ax2.set_title("Population Change Rate over Last 5 Years")
            ax2.set_xlabel("Change Rate (%)")
            st.pyplot(fig2)
            st.markdown(
                "- 첫 번째 그래프는 지난 5년간 각 지역의 인구 절대 변화량을 천 단위로 보여준다.\n"
                "- 두 번째 그래프는 같은 기간 동안의 인구 변화율을 % 단위로 나타낸다. 높은 값은 큰 인구 증가를 의미한다."
            )

        # 4. 증감률 상위 지역 및 연도 도출
        with tabs[3]:
            st.header("증감률 상위 지역 및 연도 도출")
            df_diff = df[df['지역']!='전국'].sort_values(['지역','연도'])
            df_diff['diff'] = df_diff.groupby('지역')['인구'].diff()
            df_diff = df_diff.dropna(subset=['diff'])
            top100 = df_diff.sort_values('diff', ascending=False).head(100)
            top100['Diff'] = top100['diff'].apply(lambda x: f"{int(x):,}")
            display_df = top100[['지역','연도','Diff']].rename(
                columns={'지역':'Region','연도':'Year'}
            )
            styled = display_df.style.applymap(
                lambda v: 'background-color: #ADD8E6' if int(v.replace(',',''))>0 else 'background-color: #FFCCCC',
                subset=['Diff']
            )
            st.write("Top 100 Population Changes")
            st.write(styled)

        # 5. 누적영역그래프 등 적절한 시각화
        with tabs[4]:
            st.header("누적영역그래프 등 적절한 시각화")
            pivot_df = df.pivot(index='연도', columns='지역', values='인구')
            kor_to_eng = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
                '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
                '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam',
                '제주':'Jeju'
            }
            pivot_df.columns = pivot_df.columns.map(lambda x: kor_to_eng.get(x, x))
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            pivot_df.plot.area(ax=ax)
            ax.set_title("Population Trends by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            leg = ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), title='Region')
            leg.set_title('Region')
            st.pyplot(fig)




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