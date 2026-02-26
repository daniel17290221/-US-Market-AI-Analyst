@echo off
echo [1/2] Main 브랜치 최신화 및 커밋 중...
git add .
git commit -m "Manual sync and deploy: %date% %time%"

echo.
echo [2/2] GitHub Main 브랜치로 푸시 중 (Vercel 배포 트리거)...
git push origin main

echo.
echo [!] 모든 작업 완료! 
echo [!] Vercel 대시보드에서 빌드 상태를 확인하세요.

pause
