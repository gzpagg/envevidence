from .models import FieldSpec


def water_treatment_fields() -> list[FieldSpec]:
    entries = [
        ("pollutant", "污染物", "Target pollutant; preserve chemical identity.", False),
        (
            "water_matrix",
            "水体类型",
            "Synthetic water, real wastewater, surface water, etc.",
            False,
        ),
        ("initial_concentration", "初始浓度", "Initial target pollutant concentration.", True),
        ("process", "处理工艺", "Treatment process applied to this experimental condition.", False),
        (
            "dose",
            "投加剂量",
            "Reagent-specific doses; name each reagent and keep original units.",
            True,
        ),
        ("ph", "pH", "Initial or controlled pH; distinguish if both are provided.", False),
        ("reaction_time", "反应时间", "Duration associated with the reported result.", True),
        (
            "removal_efficiency",
            "污染物去除率",
            "Target pollutant removal, NOT TOC removal/mineralization.",
            True,
        ),
        (
            "mineralization_efficiency",
            "矿化率 / TOC 去除率",
            "Mineralization or TOC removal; retain the exact endpoint name in value. Never substitute pollutant removal.",
            True,
        ),
    ]
    return [
        FieldSpec(key=key, label=label, description=description, requires_unit=unit)
        for key, label, description, unit in entries
    ]
