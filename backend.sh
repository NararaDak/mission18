nohup python -m backend.backend > output.log 2>&1 &
# 백그라운드에서 실행 중인 프로세스 확인
ps aux | grep backend.backend
