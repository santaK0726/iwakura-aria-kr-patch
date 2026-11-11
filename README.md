# 이와쿠라 아리아 한국어 패치 v0.5.1

Nintendo Switch 일본어판 **이와쿠라 아리아**의 비공식 한국어 패치입니다. 스위치용과 에뮬레이터용을 각각 제공합니다. 두 패키지는 같은 번역 데이터를 사용하며 설치 폴더 구조가 다릅니다.

**[다운로드: v0.5.1](https://github.com/santaK0726/iwakura-aria-kr-patch/releases/tag/v0.5.1)**

현재 배포는 개발판입니다. 대사·UI·글꼴·이미지 번역과 기존 UI 수정이 포함되어 있으며, 일부 원문과 미검수 구간이 남아 있습니다. 자세한 범위는 아래를 확인하세요.

## 지원 대상과 준비물

- 일본어판 본편 ID: `01009BD0209D8000`
- 업데이트 ID: `01009BD0209D8800`
- 게임 버전: **1.0.3 / 업데이트 v196608**
- 본인이 보유한 게임에서 추출한 **업데이트 적용 후의 수정하지 않은 RomFS**
- 패치 생성용 PC: Python 3.11 이상, Pillow 13.0.0(동봉 libwebp 1.6.0), NumPy 2.x

이 배포물은 원본이 필요한 차분 패치입니다. 원본 게임 파일, 완성된 MPK, 원문 대본, 키, 펌웨어, 에뮬레이터는 포함하지 않습니다. 원본 RomFS의 7개 MPK 크기와 SHA-256이 [지원 프로필](source-profile.json)에 모두 맞아야 생성됩니다. 기존 한글패치가 들어간 RomFS는 입력으로 사용할 수 없습니다.

## 1. 패치 파일 생성

1. [Releases](https://github.com/santaK0726/iwakura-aria-kr-patch/releases/tag/v0.5.1)에서 사용할 패키지를 내려받아 압축을 풉니다.
   - `Iwakura-Aria-Korean-v0.5.1-Switch-Patch.zip`: 스위치용
   - `Iwakura-Aria-Korean-v0.5.1-Emulator-Patch.zip`: 에뮬레이터용
2. 압축을 푼 폴더에서 터미널을 열고 의존성을 설치합니다.

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Windows에서는 `Build-Patch.cmd`를 실행하고 원본 RomFS 폴더 경로를 입력합니다. 또는 아래처럼 직접 실행합니다.

   ```powershell
   python -X utf8 apply_patch.py --source-romfs "D:\GameDump\romfs" --output "D:\Iwakura-Korean-Built"
   ```

4. `PASS`와 출력 폴더가 표시되면 다음 설치 절차를 따릅니다. 지정한 출력 폴더가 이미 있으면 덮어쓰지 않고 중단합니다. 생성 중 원본 게임·설치된 모드·세이브는 변경하지 않습니다.

GitHub의 `Source code` ZIP에는 차분 데이터가 없습니다. 위의 **플랫폼별 Patch ZIP**을 받으세요. 두 패키지를 함께 생성하려면 `--target both`를 지정할 수 있습니다.

## 2. 스위치에 적용

1. 게임을 완전히 종료하고 전원을 끈 다음 microSD 카드를 PC에 연결합니다. Atmosphère LayeredFS를 사용하는 환경이 필요합니다.
2. 같은 게임의 기존 번역 모드는 먼저 PC에 백업하고 카드 밖으로 옮깁니다. 기존 `cheats`·`exefs` 등 다른 파일은 건드리지 않습니다.
3. **생성된 출력 폴더의 `atmosphere` 폴더**를 microSD 카드 최상위에 복사합니다.

   ```text
   SD:/atmosphere/contents/01009BD0209D8000/romfs/
     bg.mpk
     bg_eng.mpk
     bg_jpn.mpk
     mes00.mpk
     script.mpk
     system.mpk
     system_jpn_swi.mpk
   ```

4. 본체에서 게임 버전 1.0.3을 확인하고 게임의 일본어 언어 분기를 선택합니다. 언어 이름이 `한국어`로 바뀌어 보이면 그 항목을 선택하세요.

스위치 실기 실행은 미확인입니다. 이 배포물에는 Atmosphère 자체가 들어 있지 않습니다.

## 3. 에뮬레이터에 적용

1. 게임과 에뮬레이터를 완전히 종료합니다.
2. 에뮬레이터에서 해당 게임의 **모드 데이터 폴더**를 엽니다.
3. **생성된 `Iwakura-Aria-Korean-v0.5.1` 폴더 전체**를 그 안에 복사합니다.

   ```text
   게임별 모드 폴더/01009BD0209D8000/
     Iwakura-Aria-Korean-v0.5.1/
       romfs/
         (위와 같은 MPK 7개)
   ```

4. 기존 한글패치와 중복 적용하지 말고 v0.5.1 하나만 활성화합니다. 업데이트 1.0.3을 적용하고 일본어 분기(또는 한국어로 표시되는 항목)를 선택합니다.

ZIP 자체나 `patch-data` 폴더는 모드 폴더에 넣지 마세요. 에뮬레이터마다 모드 경로가 다르므로 게임별 모드 폴더를 기준으로 합니다. Windows yuzu의 이전 설치 구조를 참고했으며, 다른 에뮬레이터에서의 실행은 확인하지 않았습니다.

## 되돌리기와 세이브

게임을 종료한 뒤 에뮬레이터의 이 모드를 비활성화하거나, 스위치에서는 이번에 넣은 MPK 7개만 카드 밖으로 옮깁니다. 이전 모드로 돌아가려면 백업을 복원합니다. 다른 파일이 섞인 `atmosphere` 또는 타이틀 폴더 전체를 지우지 마세요.

패치 생성기는 세이브를 읽거나 수정하지 않습니다. 별도 세이브 변환도 제공하지 않습니다. 기존 세이브의 모든 구간에서 호환성을 검증한 것은 아니므로 적용 전 평소 방식으로 백업하세요.

## 번역 범위와 검증

- 번역 텍스트 10,570개 항목, 이미지 후보 23개/실제 이미지 멤버 31개, UI 문구 영역 194개를 포함합니다. 이는 전체 게임 100% 검수 수치가 아닙니다.
- v0.5에서 사용자가 확인한 UI·글꼴·이미지를 유지하고 일반 서술 8개를 추가했습니다. v0.5와 달라진 아카이브는 `mes00.mpk` 하나입니다.
- **원문 유지:** 대본 138개 항목, 글꼴 시험용 MSB 4개와 SCX 글리프 목록 9개, 일부 장식·소품 글씨. 매뉴얼과 영상은 사용자 결정으로 원본을 유지합니다.
- 전체 의미 검수·전 루트 플레이·실제 자동 줄바꿈/페이지 한도 확인은 미완료입니다. v0.5 UI에 대한 사용자 확인을 v0.5.1 추가 대사나 실기 검증으로 확대하지 않습니다.
- 원본에서 재구성한 결과의 MPK 구조·보호 영역·파일별 SHA-256·최종 읽기 복원을 검사합니다. 배포 검증 결과와 정확한 출력 해시는 [verification](verification/)에 있습니다.

## 출처

- 글꼴: [Pretendard 1.3.9](https://github.com/orioncactus/pretendard), SIL OFL 1.1. [동봉 라이선스](LICENSES/Pretendard-OFL.txt)를 유지하세요.
- [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere): 스위치 LayeredFS 구현 참고.
- [sc3tools](https://github.com/CommitteeOfZero/sc3tools): 개발 중 문자표·MSB/SCX 분석 참고. 실행 파일은 배포하지 않습니다.
- 생성기에서 사용하는 Pillow·NumPy는 requirements를 통해 별도 설치합니다. [고지](NOTICE.md)를 참고하세요.

원작·상표·원화의 권리는 각 권리자에게 있습니다. 이 프로젝트는 원작의 공식 한국어판이 아닙니다.

<!-- VERIFIED_GAME_HASHES_BEGIN -->
## 패치시 기반 파일 언어 및 해시값

패치버전: **v0.5.1**  
패치시 기반 파일 언어: **日本語 / 일본어**

업데이트 1.0.3 원본 RomFS MPK 7개와 패치 후 MPK 7개; Switch/에뮬레이터 공통

아래 값은 전체 해시표의 첫 번째 파일을 대표로 표시한 것입니다. 게임 전체·원본 덤프·패치 ZIP의 해시가 아닙니다. 검사 대상: **`bg.mpk`**

**원본 대상 해시값**

- CRC32 : `876F6A6B`
- MD5 : `444A16540213961DE433EF854303CEF3`

**패치후 해시값**

- CRC32 : `D32F20DE`
- MD5 : `DB45B6A110AD63D71AA0A080F422F313`

**[전체 파일별 원본/패치 후 CRC32·MD5 표](docs/FILE_HASHES.md)** · [CSV](docs/FILE_HASHES.csv) · [SHA-256 포함 JSON](docs/FILE_HASHES.json)

해시는 표시된 검사 대상과 버전에만 적용됩니다. CRC32·MD5는 식별용이며, 적용기의 SHA-256 원본 검증은 그대로 유지합니다. 신규 추가 파일은 원본 해시가 없습니다.
<!-- VERIFIED_GAME_HASHES_END -->
