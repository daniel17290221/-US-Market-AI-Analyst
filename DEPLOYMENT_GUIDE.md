# 🚀 Vercel 배포 가이드 (완전 초보자용)

이 가이드는 GitHub와 Vercel을 처음 사용하는 분들을 위한 단계별 설명입니다.

---

## 📋 준비물

1. **GitHub 계정** (없으면 https://github.com 에서 무료 가입)
2. **Vercel 계정** (없으면 https://vercel.com 에서 GitHub로 로그인)
3. **Git 설치** (아래 1단계에서 확인)

---

## 1️⃣ Git 설치 확인 및 설치

### Git이 설치되어 있는지 확인

PowerShell을 열고 다음 명령어를 입력하세요:

```powershell
git --version
```

**결과:**
- `git version 2.x.x` 같은 메시지가 나오면 ✅ 이미 설치됨 → **2단계로 이동**
- `'git'은(는) 내부 또는 외부 명령...` 같은 오류가 나오면 ❌ 설치 필요

### Git 설치하기 (설치 안 되어 있는 경우)

1. https://git-scm.com/download/win 접속
2. "64-bit Git for Windows Setup" 다운로드
3. 설치 파일 실행
4. 모든 옵션은 **기본값**으로 두고 "Next" 클릭
5. 설치 완료 후 PowerShell을 **재시작**
6. `git --version` 다시 확인

---

## 2️⃣ Git 초기 설정 (처음 한 번만)

PowerShell에서 다음 명령어를 입력하세요 (이름과 이메일은 본인 것으로 변경):

```powershell
git config --global user.name "홍길동"
git config --global user.email "your-email@example.com"
```

**참고:** 이메일은 GitHub 가입 시 사용한 이메일을 입력하세요.

---

## 3️⃣ 프로젝트 폴더로 이동

PowerShell에서 프로젝트 폴더로 이동:

```powershell
cd "c:\Users\mjang\Downloads\Investment Vibecodinglab"
```

**확인:** `ls` 명령어를 입력하면 `index.html`, `us_market` 폴더 등이 보여야 합니다.

---

## 4️⃣ Git 저장소 초기화

```powershell
git init
```

**결과:** `Initialized empty Git repository...` 메시지가 나오면 성공!

---

## 5️⃣ 파일 추가 및 커밋

### 모든 파일을 Git에 추가

```powershell
git add .
```

**참고:** `.`은 "현재 폴더의 모든 파일"을 의미합니다.

### 커밋 (변경사항 저장)

```powershell
git commit -m "Initial commit: US Market Dashboard"
```

**결과:** 파일 개수와 변경사항이 표시되면 성공!

---

## 6️⃣ GitHub 리포지토리 생성

### 6-1. GitHub 웹사이트 접속

1. https://github.com 접속 및 로그인
2. 우측 상단 **+** 버튼 클릭
3. **New repository** 선택

### 6-2. 리포지토리 설정

다음과 같이 입력:

- **Repository name**: `us-market-analyst` (또는 원하는 이름)
- **Description**: `미국 시장 AI 분석 대시보드` (선택사항)
- **Public** 선택 (무료 배포를 위해)
- ❌ **"Add a README file"** 체크 해제 (이미 있음)
- ❌ **".gitignore"** 선택 안 함 (이미 있음)
- ❌ **"Choose a license"** 선택 안 함

### 6-3. Create repository 클릭

---

## 7️⃣ GitHub에 코드 업로드

### 7-1. GitHub 리포지토리 주소 복사

리포지토리 생성 후 나오는 페이지에서:

```
https://github.com/your-username/us-market-analyst.git
```

이 주소를 복사하세요. (your-username은 본인의 GitHub 아이디)

### 7-2. PowerShell에서 원격 저장소 연결

```powershell
git remote add origin https://github.com/your-username/us-market-analyst.git
```

**주의:** `your-username`을 본인의 GitHub 아이디로 변경하세요!

### 7-3. 기본 브랜치 이름 변경 (필요시)

```powershell
git branch -M main
```

### 7-4. GitHub에 업로드

```powershell
git push -u origin main
```

**처음 실행 시:**
- GitHub 로그인 창이 나타날 수 있습니다 → 로그인하세요
- 또는 Personal Access Token을 요구할 수 있습니다 (아래 참고)

**결과:** 업로드가 완료되면 GitHub 웹사이트에서 파일들이 보입니다!

---

## 8️⃣ Vercel에 배포

### 8-1. Vercel 접속 및 로그인

1. https://vercel.com 접속
2. **"Continue with GitHub"** 클릭하여 GitHub 계정으로 로그인
3. GitHub 권한 요청이 나오면 **"Authorize Vercel"** 클릭

### 8-2. 새 프로젝트 생성

1. Vercel 대시보드에서 **"Add New..."** 버튼 클릭
2. **"Project"** 선택

### 8-3. GitHub 리포지토리 연결

1. **"Import Git Repository"** 섹션에서 방금 만든 `us-market-analyst` 찾기
2. 리포지토리가 안 보이면 **"Adjust GitHub App Permissions"** 클릭
   - GitHub에서 Vercel에 접근 권한 부여
3. 리포지토리 옆의 **"Import"** 버튼 클릭

### 8-4. 프로젝트 설정

**Configure Project** 페이지에서:

- **Project Name**: `us-market-analyst` (자동 입력됨)
- **Framework Preset**: `Other` (그대로 둠)
- **Root Directory**: `./` (그대로 둠)
- **Build Command**: 비워둠 (정적 사이트)
- **Output Directory**: 비워둠

### 8-5. 환경 변수 설정 (선택사항)

**Environment Variables** 섹션에서:

1. **"Add"** 버튼 클릭
2. **Name**: `GOOGLE_API_KEY`
3. **Value**: 본인의 Gemini API 키 입력
4. **Environment**: `Production`, `Preview`, `Development` 모두 선택

**참고:** API 키가 없으면 일단 건너뛰어도 됩니다. 나중에 추가 가능합니다.

### 8-6. Deploy 버튼 클릭!

**"Deploy"** 버튼을 클릭하면 배포가 시작됩니다!

---

## 9️⃣ 배포 완료 및 확인

### 9-1. 배포 진행 상황 확인

- 빌드 로그가 실시간으로 표시됩니다
- 약 30초~1분 정도 소요

### 9-2. 배포 완료!

**"Congratulations!"** 메시지가 나타나면 성공!

다음과 같은 URL이 생성됩니다:
```
https://us-market-analyst-xxxxx.vercel.app
```

### 9-3. 웹사이트 확인

**"Visit"** 버튼을 클릭하거나 URL을 복사하여 브라우저에서 열어보세요!

---

## 🔄 코드 수정 후 재배포

코드를 수정한 후 다시 배포하려면:

```powershell
# 1. 프로젝트 폴더로 이동
cd "c:\Users\mjang\Downloads\Investment Vibecodinglab"

# 2. 변경사항 추가
git add .

# 3. 커밋
git commit -m "Update: 변경 내용 설명"

# 4. GitHub에 업로드
git push
```

**자동 배포:** GitHub에 푸시하면 Vercel이 자동으로 감지하여 재배포합니다!

---

## ❓ 자주 발생하는 문제

### 문제 1: GitHub 로그인이 안 됨

**해결:**
1. GitHub에서 Personal Access Token 생성
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token" 클릭
4. `repo` 권한 선택
5. 생성된 토큰을 비밀번호 대신 사용

### 문제 2: Vercel에서 리포지토리가 안 보임

**해결:**
1. Vercel 대시보드에서 "Adjust GitHub App Permissions" 클릭
2. GitHub에서 Vercel 앱에 리포지토리 접근 권한 부여

### 문제 3: 배포는 되었는데 페이지가 안 나옴

**해결:**
1. Vercel 대시보드에서 프로젝트 클릭
2. Settings → General
3. Root Directory가 `./`인지 확인
4. Redeploy 버튼 클릭

---

## 📞 도움이 필요하면

- **GitHub 문서**: https://docs.github.com
- **Vercel 문서**: https://vercel.com/docs
- **Git 기초**: https://git-scm.com/book/ko/v2

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] Git 설치 완료
- [ ] GitHub 계정 생성
- [ ] Vercel 계정 생성 (GitHub 연동)
- [ ] 프로젝트 폴더에 `.gitignore` 파일 존재
- [ ] 프로젝트 폴더에 `vercel.json` 파일 존재
- [ ] `index.html` 파일이 루트 디렉토리에 있음

배포 후 확인사항:

- [ ] Vercel URL 접속 가능
- [ ] 대시보드가 정상적으로 표시됨
- [ ] TradingView 위젯 작동
- [ ] 모든 섹션이 보임

---

**🎉 축하합니다! 이제 전 세계 어디서나 접속 가능한 웹사이트가 생겼습니다!**
