# Swak 구조 

## 처리 흐름

### 플러그인 처리 흐름

플러그인은 크게 입력(Input)과 출력(Output) 플러그인으로 분류된다. 입력 플러그인은 데이터의 스트림을 얻어내는 데 사용되고, 출력 플러그인은 그 스트림을 가공하거나, 최종적으로 전송하는데 사용된다. 

입력은 한 번만 나오고, 출력은 한 번 이상 연쇄될 수 있다.

<img src="images/plugin_flow.png" width="550" />

### 외부 프로세스 호출 흐름
외부 실행파일이나 스크립트를 실행할 수 있다. 단, 그것들은 입력 파일명과 출력 파일명을 인자로 받아 실행하도록 구성되어야 한다.

<img src="images/process_flow.png" width="700" />

## 폴더 구조
    
    swak/
        bin/  # 실행 파일들
        swak/  # 코드
            plugins/  # 표준 플러그인들



# Swak 플러그인 만들기
플러그인은 크게 표준 플러그인과 외부 플러그인으로 나눈다. 표준 플러그인은 `swak/plugins`에 위치하며, Swak이 기동할 때 자동으로 타입에 맞는 패키지로 로딩된다. 표준 플러그인은 Swak코드 관리자가 만드는 것이기에, 여기에서는 외부 플러그인 만드는 법을 살펴보겠다.

## 외부 플러그인 규칙

여기서 Swak의 플러그인 코드는 GitHub을 통해서 관리되는 것으로 가정하며, 다음과 같은 규칙을 따라야 한다.

- GitHub의 저장소(Repository) 명은 `swak-plugin-` 으로 시작한다.
- 설치를 위한 `setup.py`를 제공해야 한다.
- 버전 정보를 갖는다.

## 샘플 플러그인
간단한 샘플 플러그인(`foo`)을 예제로 하여 알아보자.

1. 먼저 GitHub에서 `swak-plugin-foo`라는 저장소를 만든다.
2. 저장소를 로컬로 `clone`한다.

    `git clone https://github.com/GitHub계정/swak-plugin-foo.git`

3. 폴더로 이동 후, 개발용으로 설치한다.

    `python setup.py install -e .`

## 개발용 실행
