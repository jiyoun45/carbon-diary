# carbon_calculator.py
# 친환경 행동별 예상 탄소 감축량 계산

CARBON_FACTORS = {
    "public_transport": {
        "name": "대중교통 이용",
        "unit": "km",
        "factor": 0.10
    },
    "walking": {
        "name": "걷기 및 자전거 이용",
        "unit": "km",
        "factor": 0.20
    },
    "tumbler": {
        "name": "텀블러 사용",
        "unit": "회",
        "factor": 0.03
    },
    "less_disposable": {
        "name": "일회용품 줄이기",
        "unit": "회",
        "factor": 0.02
    },
    "plant_based_meal": {
        "name": "식물성 식사",
        "unit": "끼",
        "factor": 0.50
    },
    "electricity_saving": {
        "name": "전기 절약",
        "unit": "kWh",
        "factor": 0.40
    }
}


def calculate_reduction(action, amount):
    """친환경 행동에 따른 예상 탄소 감축량을 계산한다."""

    if action not in CARBON_FACTORS:
        raise ValueError("지원하지 않는 행동 유형입니다.")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("수량은 숫자로 입력해 주세요.")

    if amount <= 0:
        raise ValueError("수량은 0보다 커야 합니다.")

    if amount > 10000:
        raise ValueError("수량이 너무 큽니다. 입력값을 확인해 주세요.")

    factor = CARBON_FACTORS[action]["factor"]
    reduction = amount * factor

    return round(reduction, 3)


def get_action_options():
    """화면에서 사용할 행동 목록을 반환한다."""

    return [
        {
            "id": action_id,
            "name": info["name"],
            "unit": info["unit"],
            "factor": info["factor"]
        }
        for action_id, info in CARBON_FACTORS.items()
    ]
