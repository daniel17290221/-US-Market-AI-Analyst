# Capacitor 모바일 앱 패키징

웹, PWA, Android, iOS는 같은 Flask API와 배당 페이지를 사용합니다. 네이티브 앱은
HTTPS로 배포된 웹 주소를 Capacitor WebView에서 엽니다.

## 최초 네이티브 프로젝트 생성

PowerShell:

```powershell
$env:CAPACITOR_SERVER_URL = "https://your-production-domain.example"
npx cap add android
npx cap add ios
npm run cap:sync
```

`CAPACITOR_SERVER_URL`에는 `/dividend`를 붙이지 않습니다. 설정 파일이 자동으로
`/dividend?source=capacitor`를 사용합니다.

로컬 HTTP 서버는 Android 개발 중에만 다음처럼 명시적으로 허용합니다.

```powershell
$env:CAPACITOR_SERVER_URL = "http://10.0.2.2:5000"
$env:CAPACITOR_ALLOW_CLEARTEXT = "1"
npm run cap:sync
```

릴리스 빌드에서는 반드시 HTTPS를 사용하고 `CAPACITOR_ALLOW_CLEARTEXT`를 제거합니다.

## Android

```powershell
npm run cap:android
```

Android Studio에서 서명 키, 앱 아이콘, 스플래시, 버전 코드와 개인정보처리방침 URL을
확인한 후 AAB를 생성합니다.

## iOS

```bash
npm run cap:ios
```

iOS 빌드와 App Store 제출은 macOS와 Xcode가 필요합니다. Xcode에서 Team,
Bundle Identifier, 앱 아이콘, 스플래시와 개인정보처리방침 URL을 설정합니다.

## 배포 전 점검

- 프로덕션 주소는 HTTPS만 사용
- 키움 앱키와 토큰은 모바일 앱에 포함하지 않고 Flask 서버 환경변수로만 관리
- `KIWOOM_SYNC_SECRET`은 브라우저 저장소에 저장하지 않음
- 가족 프로필 암호화 보관함 비밀번호는 서버로 전송하지 않음
- 서버 변경 후 `npm run cap:sync` 실행
- `npm test`와 Android/iOS 실제 기기 테스트 수행

`mobile-shell/index.html`은 서버 주소가 없는 개발 패키지에서만 표시되는 안전한
대체 화면입니다.
