# systemd 데몬 재로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable start-fastapi

# 서비스 시작
sudo systemctl start start-fastapi

# 서비스 로그 실시간 확인
sudo journalctl -u start-fastapi.service -f