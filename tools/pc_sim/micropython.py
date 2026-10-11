# PC용 micropython 대체 모듈 (미리보기 전용)
# viper/native 함수는 일반 파이썬 함수로 그대로 실행됨.


def viper(f):
    return f


def native(f):
    return f


def const(x):
    return x


def mem_info(*a):
    print("[pc_sim] mem_info: n/a")
