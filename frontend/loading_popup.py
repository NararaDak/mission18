# 긴 작업 처리 중 사용자에게 보여줄 로딩 오버레이 팝업 관리 클래스
import streamlit as st

class LoadingPopup:
    # 로딩 메시지 설정
    def __init__(self, message: str = "잠시만 기다려주세요..."):
        self.message = message
        self.placeholder = None

    # 'with' 문 진입 시 로딩 HTML/CSS 출력
    def __enter__(self):
        self.placeholder = st.empty()
        
        # 화면 전체를 덮는 반투명 오버레이와 회전 스피너 구현 (HTML/CSS)
        overlay_html = f"""
        <style>
        .custom-loading-overlay {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: rgba(0, 0, 0, 0.4); z-index: 999999;
            display: flex; justify-content: center; align-items: center;
            flex-direction: column; backdrop-filter: blur(2px);
        }}
        .custom-loader {{
            border: 8px solid #f3f3f3; border-top: 8px solid #ff4b4b;
            border-radius: 50%; width: 60px; height: 60px;
            animation: spin 1s linear infinite; margin-bottom: 20px;
        }}
        .custom-loading-text {{
            color: white; font-size: 24px; font-weight: bold;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        <div class="custom-loading-overlay">
            <div class="custom-loader"></div>
            <div class="custom-loading-text">{self.message}</div>
        </div>
        """
        self.placeholder.markdown(overlay_html, unsafe_allow_html=True)
        return self

    # 'with' 문 종료 시 오버레이 제거 및 예외 발생 시 알림 toast 출력
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.placeholder:
            self.placeholder.empty()
            
        if exc_type is not None:
            st.toast("❌ 작업 처리 중 오류가 발생했습니다.")
