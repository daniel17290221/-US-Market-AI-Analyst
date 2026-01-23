# 🚀 GitHub Desktop으로 Vercel 배포하기 (초간단 버전)

GitHub Desktop이 이미 설치되어 있으니 훨씬 쉽습니다!

---

## 📋 준비물

- ✅ GitHub Desktop (이미 설치됨)
- ✅ GitHub 계정 (GitHub Desktop 로그인 시 사용)
- ⬜ Vercel 계정 (아래에서 생성)

---

## 1️⃣ GitHub Desktop에서 리포지토리 생성

### 1-1. GitHub Desktop 열기

1. **GitHub Desktop** 실행
2. 로그인이 안 되어 있으면 GitHub 계정으로 로그인

### 1-2. 새 리포지토리 추가

**방법 A: 기존 폴더를 리포지토리로 만들기 (추천)**

1. 메뉴: **File** → **Add local repository...**
2. **Choose...** 버튼 클릭
3. 폴더 선택: `c:\Users\mjang\Downloads\미국 종목 분석`
4. "create a repository" 링크 클릭 (폴더가 Git 리포지토리가 아니라는 메시지가 나오면)

**방법 B: 처음부터 새로 만들기**

1. 메뉴: **File** → **New repository...**
2. **Name**: `us-market-analyst`
3. **Local path**: `c:\Users\mjang\Downloads`
4. ✅ **Initialize this repository with a README** 체크 해제
5. **Git ignore**: None
6. **License**: None
7. **Create repository** 클릭

---

## 2️⃣ 파일 커밋하기

### 2-1. 변경사항 확인

GitHub Desktop 왼쪽 패널에 모든 파일이 체크되어 있는지 확인:
- ✅ index.html
- ✅ us_market/ 폴더
- ✅ vercel.json
- ✅ README.md
- ✅ .gitignore
- 등등...

### 2-2. 커밋 메시지 작성

왼쪽 하단에:
- **Summary**: `Initial commit: US Market Dashboard`
- **Description**: (비워둬도 됨)

### 2-3. Commit 버튼 클릭

**"Commit to main"** 버튼 클릭!

---

## 3️⃣ GitHub에 업로드 (Publish)

### 3-1. Publish repository 클릭

상단의 **"Publish repository"** 버튼 클릭

### 3-2. 설정 확인

팝업 창에서:
- **Name**: `us-market-analyst` (그대로 둠)
- **Description**: `미국 시장 AI 분석 대시보드` (선택사항)
- ❌ **Keep this code private** 체크 해제 (Public으로 해야 무료 배포 가능)
- **Organization**: None (개인 계정)

### 3-3. Publish Repository 클릭

업로드가 완료되면 GitHub 웹사이트에서 확인 가능합니다!

---

## 4️⃣ Vercel 계정 생성 및 배포

### 4-1. Vercel 접속

1. 브라우저에서 https://vercel.com 접속
2. **"Start Deploying"** 또는 **"Sign Up"** 클릭

### 4-2. GitHub로 로그인

1. **"Continue with GitHub"** 클릭
2. GitHub 로그인 (이미 로그인되어 있으면 자동)
3. **"Authorize Vercel"** 클릭 (권한 요청 시)

### 4-3. 새 프로젝트 생성

1. Vercel 대시보드에서 **"Add New..."** 버튼 클릭
2. **"Project"** 선택

### 4-4. 리포지토리 선택

1. **"Import Git Repository"** 섹션에서 `us-market-analyst` 찾기
2. 리포지토리가 안 보이면:
   - **"Adjust GitHub App Permissions"** 클릭
   - GitHub에서 Vercel 앱에 리포지토리 접근 권한 부여
   - 다시 Vercel로 돌아오기
3. `us-market-analyst` 옆의 **"Import"** 버튼 클릭

### 4-5. 프로젝트 설정

**Configure Project** 페이지:

- **Project Name**: `us-market-analyst` ✅
- **Framework Preset**: `Other` ✅
- **Root Directory**: `./` (그대로) ✅
- **Build Command**: (비워둠) ✅
- **Output Directory**: (비워둠) ✅

### 4-6. 환경 변수 추가 (선택사항)

**Environment Variables** 섹션:

Gemini API 키가 있다면:
1. **Name**: `GOOGLE_API_KEY`
2. **Value**: 본인의 API 키
3. **Environment**: Production, Preview, Development 모두 선택

없으면 건너뛰어도 됩니다!

### 4-7. Deploy 클릭!

**"Deploy"** 버튼 클릭하면 배포 시작!

---

## 5️⃣ 배포 완료!

### 약 30초~1분 후...

✅ **"Congratulations!"** 메시지가 나타나면 성공!

생성된 URL:
```
https://us-market-analyst-xxxxx.vercel.app
```

**"Visit"** 버튼을 클릭하여 웹사이트 확인!

---

## 🔄 코드 수정 후 재배포 (매우 간단!)

### GitHub Desktop에서:

1. 파일 수정 (예: `index.html` 편집)
2. GitHub Desktop 열기
3. 변경된 파일 확인 (자동으로 감지됨)
4. 왼쪽 하단에 커밋 메시지 입력
   - 예: `Update: ETF 섹션 글자 크기 증가`
5. **"Commit to main"** 클릭
6. 상단의 **"Push origin"** 버튼 클릭

**끝!** Vercel이 자동으로 감지하여 재배포합니다!

---

## 📊 배포 상태 확인

### Vercel 대시보드에서:

1. https://vercel.com/dashboard 접속
2. `us-market-analyst` 프로젝트 클릭
3. **Deployments** 탭에서 배포 상태 확인
   - ✅ Ready: 배포 완료
   - 🔄 Building: 배포 중
   - ❌ Error: 오류 발생

---

## ❓ 문제 해결

### 문제 1: GitHub Desktop에서 "Publish repository" 버튼이 안 보임

**해결:** 이미 publish되었을 수 있습니다. 상단에 "Push origin" 버튼이 있는지 확인하세요.

### 문제 2: Vercel에서 리포지토리가 안 보임

**해결:**
1. Vercel에서 "Adjust GitHub App Permissions" 클릭
2. GitHub 설정 페이지에서 Vercel 앱 찾기
3. "Repository access" → "All repositories" 또는 특정 리포지토리 선택
4. Save

### 문제 3: 배포는 되었는데 페이지가 비어있음

**해결:**
1. `index.html`이 프로젝트 루트에 있는지 확인
2. Vercel 프로젝트 Settings → General
3. Root Directory가 `./`인지 확인
4. Redeploy

---

## 🎯 다음 단계

배포가 완료되면:

1. ✅ URL을 즐겨찾기에 추가
2. ✅ 친구들과 공유
3. ✅ 매일 업데이트되는 시장 분석 확인
4. ✅ 필요하면 코드 수정 후 재배포

---

## 📝 요약

### 처음 배포 (한 번만):
1. GitHub Desktop에서 리포지토리 생성
2. 파일 커밋
3. GitHub에 Publish
4. Vercel에서 Import
5. Deploy 클릭

### 이후 업데이트 (매번):
1. 파일 수정
2. GitHub Desktop에서 커밋
3. Push origin 클릭
4. 자동 재배포 ✨

---

**🎉 축하합니다! 이제 프로페셔널한 웹 대시보드를 운영하게 되었습니다!**

**생성된 URL을 저장해두세요:**
```
https://us-market-analyst-xxxxx.vercel.app
```
