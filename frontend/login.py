import streamlit as st
from call_api import CallApi
from loading_popup import LoadingPopup

def show_login():
    api = CallApi()
    st.markdown("""
        <style>
        .login-card {
            max-width: 400px;
            margin: 40px auto 0 auto;
            padding: 2rem 2rem 1.5rem 2rem;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px 0 rgba(0,0,0,0.1);
        }
        .login-title {text-align:center; font-size:2rem; font-weight:700; margin-bottom:1.5rem; color: #333;}
        </style>
    """, unsafe_allow_html=True)
    
    # 7번 요구사항: 로그인 화면 크기 조정 및 중앙 배치
    _, centerCol, _ = st.columns([1, 2, 1])
    with centerCol:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">로그인</div>', unsafe_allow_html=True)

        if "login_error" not in st.session_state:
            st.session_state["login_error"] = ""

        with st.form("login_form", clear_on_submit=False):
            user_id = st.text_input("아이디", max_chars=32, help="아이디(4~32자)")
            user_pw = st.text_input("비밀번호", type="password", max_chars=64, help="비밀번호(6~64자)")
            
            btnCols = st.columns([1, 1])
            login_btn = btnCols[0].form_submit_button("로그인", use_container_width=True)
            signup_btn = btnCols[1].form_submit_button("회원가입", use_container_width=True)

            if login_btn:
                if not (4 <= len(user_id) <= 32):
                    st.session_state["login_error"] = "아이디는 4~32자여야 합니다."
                elif not (6 <= len(user_pw) <= 64):
                    st.session_state["login_error"] = "비밀번호는 6~64자여야 합니다."
                else:
                    with LoadingPopup("로그인 중..."):
                        res = api.login(user_id, user_pw)
                        if res.get("ok"):
                            userData = res.get("responseJson", {})
                            st.session_state["user_id"] = userData.get("userId")
                            st.session_state["user_name"] = userData.get("userName")
                            st.session_state["login_error"] = ""
                            # 세션 복구용 쿼리 파라미터 저장 - 9번 요구사항 개선 방안
                            st.query_params["uid"] = st.session_state["user_id"]
                            st.query_params["uname"] = st.session_state["user_name"]
                            st.success(f"로그인 성공! 환영합니다, {st.session_state['user_name']}님.")
                            st.rerun()
                        else:
                            st.session_state["login_error"] = res.get("error", "아이디 또는 비밀번호가 올바르지 않습니다.")
            
            if signup_btn:
                st.session_state["goto_signup"] = True
                st.rerun()

        if st.session_state["login_error"]:
            st.error(st.session_state["login_error"])
        st.markdown('</div>', unsafe_allow_html=True)


# show_login 함수만 정의 (import 시 자동 실행 방지)
