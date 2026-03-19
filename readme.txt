이름: Python: streamlit frontend
실행 방식: python -m streamlit run frontend/frontend.py
작업 경로: ${workspaceFolder}

# 가상 활성화.
.venv\Scripts\Activate

# backend 실행
.venv\Scripts\python.exe -m backend.backend
python -m backend/backend.py

# frontend 실행 (streamlit)
.venv\Scripts\python.exe -m streamlit run frontend/frontend.py
python -m streamlit run frontend/frontend.py

# backend 디버그 실행
.venv\Scripts\python.exe -m debugpy --listen 5678 --wait-for-client -m backend.backend

# frontend 디버그 실행
.venv\Scripts\python.exe -m debugpy --listen 5679 --wait-for-client -m streamlit run frontend/frontend.py


