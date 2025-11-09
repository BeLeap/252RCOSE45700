---
title: "God Object / Manager 객체 남용"
tags: ["oop", "design", "architecture"]
summary: "모든 책임이 한 객체에 몰리는 구조"
---

# God Object / Manager 객체 남용

## 개요
`AppManager`, `MainService`, `CoreHandler` 같은 이름의 클래스가
실제로는 도메인의 거의 모든 기능을 알고 수행하는 안티패턴이다.

## 왜 문제인가?
- 단일 책임 원칙(SRP)을 위반한다.
- 변경이 잦아지면 이 객체만 계속 수정되어 git blame이 지저분해진다.
- 의존성이 이 객체를 기준으로 역으로 생성되어 순환 참조를 유발하기 쉽다.

## 예시
- `UserManager`가 인증, 인가, 프로필 수정, 비밀번호 재설정, 알림 전송까지 다 한다.
- `MainService`가 외부 API까지 직접 호출한다.

## 개선 아이디어
- 기능을 유스케이스/도메인 단위로 분리한다. (예: `UserAuthService`, `UserProfileService`)
- 모듈 경계를 정하고 인터페이스를 두어 의존성 방향을 고정한다.
- DI 컨테이너를 사용할 경우 등록 시에도 역할별로 나눈다.
