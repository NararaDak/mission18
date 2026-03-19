import streamlit as st

class LoadingPopup:
    """
    with LoadingPopup("처리 중입니다..."):
        # 긴 작업
    형태로 사용할 수 있는 커스텀 로딩 팝업 클래스입니다.
    """
    def __init__(self, message: str = "잠시만 기다려주세요..."):
        self.message = message
        self.placeholder = None

    def __enter__(self):
        self.placeholder = st.empty()
        
        # 화면 전체를 덮는 반투명 오버레이와 로딩 스피너를 보여주는 CSS/HTML
        overlay_html = f"""
        <style>
        .custom-loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.4);
            z-index: 999999;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            backdrop-filter: blur(2px);
        }}
        .custom-loader {{
            border: 8px solid #f3f3f3;
            border-top: 8px solid #ff4b4b;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }}
        .custom-loading-text {{
            color: white;
            font-size: 24px;
            font-weight: bold;
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

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 작업이 끝나면 오버레이를 화면에서 제거하고 에러 발생 시에만 토스트 메시지 표시
        if self.placeholder:
            self.placeholder.empty()
            
        if exc_type is not None:
            st.toast("❌ 작업 처리 중 오류가 발생했습니다.")
