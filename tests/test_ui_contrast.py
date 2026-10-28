from caderno import ui


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(first, second):
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_small_text_palette_meets_wcag_aa_contrast_on_its_backgrounds():
    pairs = (
        (ui.MUTED, ui.PAPER),
        (ui.MUTED, ui.SIDEBAR),
        (ui.MUTED, ui.PANEL),
        (ui.MUTED, ui.STATE_PANEL),
        (ui.MUTED, ui.DISABLED_BUTTON),
        (ui.SAGE, ui.PAPER),
        ("#ffffff", ui.PRIMARY_BUTTON),
        (ui.INK, ui.SECONDARY_BUTTON),
        (ui.INK, ui.SECONDARY_ACTIVE),
        ("#ffffff", ui.GREEN),
        ("#5b655c", ui.SIDEBAR),
        ("#273b30", "#e4e5dd"),
        ("#252c27", ui.PAPER),
        ("#38453b", ui.STATE_PANEL),
        ("#f6f3e9", ui.GREEN),
        ("#ffffff", ui.GREEN),
    )

    for foreground, background in pairs:
        assert contrast_ratio(foreground, background) >= 4.5, (foreground, background)


def test_control_boundaries_and_selected_navigation_indicator_are_distinguishable():
    assert contrast_ratio(ui.FIELD_BORDER, ui.PANEL) >= 3
    assert contrast_ratio(ui.FIELD_BORDER, ui.PAPER) >= 3
    assert contrast_ratio(ui.GREEN, ui.SIDEBAR) >= 3
    assert contrast_ratio("#6d826f", "#f1f2ec") >= 3
    assert contrast_ratio(ui.FOCUS_ON_PRIMARY, ui.GREEN) >= 3
    assert contrast_ratio(ui.GREEN, ui.PANEL) >= 3


def test_create_and_close_vault_buttons_have_readable_normal_and_active_colors(monkeypatch):
    configured = {}

    class FakeButton:
        def __init__(self, _parent, **options):
            configured.update(options)

    monkeypatch.setattr(ui.tk, "Button", FakeButton)
    for variant, expected_background, expected_foreground, expected_active in (
        ("primary", ui.PRIMARY_BUTTON, "white", ui.GREEN),
        ("secondary", ui.SECONDARY_BUTTON, ui.INK, ui.SECONDARY_ACTIVE),
    ):
        ui.make_button(None, "test", ui.GREEN, "white", pady=8, variant=variant)
        assert configured["bg"] == expected_background
        assert configured["fg"] == expected_foreground
        assert configured["activebackground"] == expected_active
        assert configured["activeforeground"] == expected_foreground
        assert contrast_ratio(
            "#ffffff" if expected_foreground == "white" else expected_foreground,
            expected_active,
        ) >= 4.5
