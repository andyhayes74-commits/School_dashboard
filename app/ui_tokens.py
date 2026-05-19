"""Semantic UI tokens and stylesheet helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app import config


@dataclass(frozen=True)
class UITokens:
    font_family: str
    canvas_surface: str
    surface_default: str
    surface_raised: str
    surface_input: str
    text_primary: str
    text_secondary: str
    text_tertiary: str
    text_inverse: str
    border_subtle: str
    border_default: str
    action_brand: str
    action_brand_hover: str
    status_success_bg: str
    status_success_fg: str
    status_info_bg: str
    status_info_fg: str
    status_warning_bg: str
    status_warning_fg: str
    status_danger_bg: str
    status_danger_fg: str
    radius_sm: int
    radius_md: int
    radius_lg: int
    space_1: int
    space_2: int
    space_3: int
    space_4: int
    space_5: int
    space_6: int
    focus_ring: str


FONT_STACK = '"Segoe UI Variable", "Inter", "Segoe UI", Roboto, Arial, sans-serif'


def build_tokens(theme: dict[str, str], dark_mode: bool = False) -> UITokens:
    merged = {**config.DEFAULT_THEME, **theme}
    if dark_mode:
        return UITokens(
            font_family=FONT_STACK,
            canvas_surface="#0B1220",
            surface_default="#111827",
            surface_raised="#172033",
            surface_input="#0F172A",
            text_primary="#F8FAFC",
            text_secondary="#CBD5E1",
            text_tertiary="#94A3B8",
            text_inverse="#F8FAFC",
            border_subtle="#334155",
            border_default="#475569",
            action_brand="#60A5FA",
            action_brand_hover=merged["accent_colour"],
            status_success_bg="#064E3B",
            status_success_fg="#D1FAE5",
            status_info_bg="#1E3A8A",
            status_info_fg="#DBEAFE",
            status_warning_bg="#7C2D12",
            status_warning_fg="#FFEDD5",
            status_danger_bg="#7F1D1D",
            status_danger_fg="#FEE2E2",
            radius_sm=6,
            radius_md=10,
            radius_lg=12,
            space_1=4,
            space_2=8,
            space_3=12,
            space_4=16,
            space_5=20,
            space_6=24,
            focus_ring="#60A5FA",
        )

    return UITokens(
        font_family=FONT_STACK,
        canvas_surface=merged["secondary_colour"],
        surface_default="#FFFFFF",
        surface_raised="#FFFFFF",
        surface_input="#F8FAFC",
        text_primary=merged["text_colour"],
        text_secondary="#334155",
        text_tertiary="#64748B",
        text_inverse="#F8FAFC",
        border_subtle="#E2E8F0",
        border_default="#CBD5E1",
        action_brand=merged["accent_colour"],
        action_brand_hover=merged["primary_colour"],
        status_success_bg="#ECFDF3",
        status_success_fg="#166534",
        status_info_bg="#EFF6FF",
        status_info_fg="#1E3A8A",
        status_warning_bg="#FFF7ED",
        status_warning_fg="#9A3412",
        status_danger_bg="#FEF2F2",
        status_danger_fg="#991B1B",
        radius_sm=6,
        radius_md=10,
        radius_lg=12,
        space_1=4,
        space_2=8,
        space_3=12,
        space_4=16,
        space_5=20,
        space_6=24,
        focus_ring="#1D4ED8",
    )
