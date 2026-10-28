from caderno import ui


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(first, second):
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_small_text_palette_meets_wcag_aa_contrast_on_its_backgrounds():
    theme = ui.THEME
    pairs = (
        (theme.muted, theme.paper),
        (theme.muted, theme.sidebar),
        (theme.muted, theme.panel),
        (theme.muted, theme.state_panel),
        (theme.muted, theme.disabled_button.background),
        (theme.sage, theme.paper),
        (theme.primary_button.foreground, theme.primary_button.background),
        (theme.primary_button.active_foreground, theme.primary_button.active_background),
        (theme.secondary_button.foreground, theme.secondary_button.background),
        (theme.secondary_button.active_foreground, theme.secondary_button.active_background),
        (theme.locked_status, theme.sidebar),
        (theme.selected_navigation_foreground, theme.selected_navigation_background),
        (theme.welcome_title, theme.paper),
        (theme.state_title, theme.state_panel),
        (theme.brand_mark_foreground, theme.green),
        (theme.primary_button.focus, theme.primary_button.active_background),
    )

    for foreground, background in pairs:
        assert contrast_ratio(foreground, background) >= 4.5, (foreground, background)
    assert theme.primary_button.foreground == theme.ink
    assert theme.primary_button.active_foreground == theme.ink


def test_control_boundaries_and_selected_navigation_indicator_are_distinguishable():
    theme = ui.THEME
    assert contrast_ratio(theme.field_border, theme.panel) >= 3
    assert contrast_ratio(theme.field_border, theme.paper) >= 3
    assert contrast_ratio(theme.green, theme.sidebar) >= 3
    assert contrast_ratio(theme.state_icon_foreground, theme.state_icon_background) >= 3
    assert contrast_ratio(theme.primary_button.focus, theme.primary_button.active_background) >= 3
    assert contrast_ratio(theme.green, theme.panel) >= 3


def test_create_and_close_vault_buttons_have_readable_normal_and_active_colors(monkeypatch):
    configured = {}

    class FakeButton:
        def __init__(self, _parent, **options):
            configured.update(options)

    monkeypatch.setattr(ui.tk, "Button", FakeButton)
    for variant, style in (
        ("primary", ui.THEME.primary_button),
        ("secondary", ui.THEME.secondary_button),
    ):
        ui.make_button(None, "test", variant, pady=8)
        assert configured["bg"] == style.background
        assert configured["fg"] == style.foreground
        assert configured["activebackground"] == style.active_background
        assert configured["activeforeground"] == style.active_foreground
        assert configured["highlightcolor"] == style.focus
        assert configured["disabledforeground"] == style.foreground
        assert contrast_ratio(style.foreground, style.background) >= 4.5
        assert contrast_ratio(style.active_foreground, style.active_background) >= 4.5


def test_disabled_button_uses_the_shared_disabled_theme(monkeypatch):
    configured = {}

    class FakeButton:
        def __init__(self, _parent, **options):
            configured.update(options)

    monkeypatch.setattr(ui.tk, "Button", FakeButton)
    ui.make_button(None, "test", "primary", pady=8, state="disabled")

    assert configured["bg"] == ui.THEME.disabled_button.background
    assert configured["fg"] == ui.THEME.disabled_button.foreground
    assert configured["activebackground"] == ui.THEME.disabled_button.active_background
    assert configured["activeforeground"] == ui.THEME.disabled_button.active_foreground
    assert configured["disabledforeground"] == ui.THEME.disabled_button.foreground
    assert configured["highlightcolor"] == ui.THEME.disabled_button.focus


def test_disabled_button_still_rejects_unknown_variant():
    try:
        ui.make_button(None, "test", "unknown", pady=8, state="disabled")
    except ValueError as error:
        assert "Variante de botão desconhecida" in str(error)
    else:
        raise AssertionError("A fábrica aceitou variante inexistente")
