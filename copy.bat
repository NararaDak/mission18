@echo off
robocopy "D:\project\mission18" "Y:\home\ubuntu\project\mission18" /MIR /MT:8 /R:2 /W:2 /XD .web .venv __pycache__ .states .github .git mlruns .vscode data .streamlit /XF *.pyc
