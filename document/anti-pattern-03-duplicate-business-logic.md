---
title: "여러 레이어에 중복된 비즈니스 로직"
tags: ["layered-architecture", "duplication", "backend"]
summary: "Controller, Service, Repository 에서 같은 검증을 반복하는 패턴"
---

# 여러 레이어에 중복된 비즈니스 로직

## 개요
레이어드 아키텍처를 쓴다고 해놓고 실제로는 같은 검증/권한 체크가
Controller와 Service, 때로는 Repository에도 중복되어 있는 경우다.

## 문제
- 하나의 정책이 바뀌면 세 군데 코드를 모두 고쳐야 한다.
- 어느 레이어가 진짜 소스 오브 트루스(Source of Truth)인지 알 수 없다.
- 테스트가 레이어마다 필요 이상으로 늘어난다.

## 나타나는 형태
- Controller: `if (!user.isActive) throw ...`
- Service: `if (!user.isActive) throw ...`
- Repository: `WHERE user.active = true`

## 개선
- 비즈니스 규칙은 Service/Domain 단에서만 검증하도록 기준을 잡는다.
- Controller는 입력 형식/인증 정도만 책임진다.
- 반복되는 검증은 데코레이터/미들웨어/도메인 서비스로 공통화한다.
