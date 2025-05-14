(*추가)한국 기준으로 서버 시간 설정: sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime <br/>
현재 경로 상세 출력: ls -al <br/>
경로 이동: cd 경로 <br/>
vim 에디터로 파일 열기: vim bitcoinAutoTrade.py <br/>
vim 에디터 입력: i <br/>
vim 에디터 저장: :wq! <br/>
패키지 목록 업데이트: sudo apt update <br/>
pip3 설치: sudo apt install python3-pip <br/>
pip3로 pyupbit 설치: pip3 install pyupbit <br/>
백그라운드 실행: nohup python3 autotrade.py > output.log & <br/>
실행되고 있는지 확인: ps ax | grep .py <br/>
프로세스 종료(PID는 ps ax | grep .py를 했을때 확인 가능): kill -9 PID <br/>
로그 확인 방법: tail -f trading_bot.log! <br/>
