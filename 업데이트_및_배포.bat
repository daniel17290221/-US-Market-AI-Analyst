@echo off
echo [1/3] Master 브랜치 최신화 및 커밋 중...
git add .
git commit -m "Manual sync and deploy: %date% %time%"

echo.
echo [2/3] Master 내용을 Main 브랜치로 강제 병합 중...
git checkout main
git reset --hard master

echo.
echo [3/3] GitHub로 푸시 중 (Vercel 배포 트리거)...
git push origin master --force
git push origin main --force

echo.
echo [!] 모든 작업 완료! 
echo [!] 다시 Master 브랜치로 돌아갑니다.
git checkout master

pause
