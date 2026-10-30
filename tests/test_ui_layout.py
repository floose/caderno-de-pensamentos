from PIL import ImageFont

from caderno import ui


def _font(specification):
    _family, size, *_styles = specification
    return ImageFont.load_default(size=size)


def _text_width(specification, text):
    return _font(specification).getlength(text)


def _text_height(specification, text="Ag"):
    top, bottom = _font(specification).getbbox(text)[1::2]
    return bottom - top


def _wrapped_line_count(specification, text, max_width):
    words = text.split()
    lines = 1
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and _text_width(specification, candidate) > max_width:
            lines += 1
            current = word
        else:
            current = candidate
    return lines


def test_ui_typography_uses_readable_minimum_sizes():
    theme = ui.THEME
    assert theme.font_body[1] >= 12
    assert theme.font_button[1] >= 12
    assert theme.font_label[1] >= 11
    assert theme.font_tiny[1] >= 10
    assert theme.font_mono_small[1] >= 10


def test_ui_text_fits_at_default_and_minimum_window_widths():
    theme = ui.THEME
    layout = theme.layout
    sidebar_content_width = layout.sidebar_width - 2 * layout.sidebar_padding_x
    topbar_text_width = sum((
        _text_width(theme.font_label, "Seu espaço   /   Todos os textos"),
        _text_width(theme.font_label, "PROTÓTIPO VISUAL     ◷  Calendário"),
    ))

    for window_width in (layout.minimum_window_size[0], layout.window_size[0]):
        content_width = window_width - layout.sidebar_width - 2 * layout.main_horizontal_padding
        state_content_width = content_width - 2 * layout.state_horizontal_padding
        assert content_width > 0
        assert state_content_width > 0
        assert _text_width(theme.font_title, "Um lugar para suas ideias.") <= state_content_width
        assert _text_width(theme.font_heading, "Seu caderno começa com uma ideia.") <= state_content_width
        assert layout.state_description_wrap <= state_content_width
        assert _text_width(theme.font_button, "Escolher outra base") + 2 * layout.button_horizontal_padding <= state_content_width
        sidebar_button_width = (
            _text_width(theme.font_button, "Fechar base")
            + 2 * layout.button_horizontal_padding
            + 2 * layout.highlight_thickness
        )
        assert sidebar_button_width <= sidebar_content_width - 16
        assert _text_width(theme.font_button, "+  Novo texto") + 2 * layout.button_horizontal_padding <= sidebar_content_width
        assert topbar_text_width <= content_width

        sort_button_width = _text_width(theme.font_button, "Ordenar: última edição  ▾")
        search_width = (
            content_width - sort_button_width
        - 2 * layout.button_horizontal_padding - 2 * layout.highlight_thickness
        - layout.search_gap - 2 * layout.highlight_thickness
        )
        placeholder_width = _text_width(theme.font_body, "⌕   Buscar por título, tema ou conteúdo…")
        assert placeholder_width <= search_width


def test_note_editor_fits_minimum_window_dimensions():
    theme = ui.THEME
    layout = theme.layout
    topbar_height = (
        _text_height(theme.font_label)
        + 2 * layout.topbar_vertical_padding
        + 2 * layout.highlight_thickness
    )
    summary_height = (
        _text_height(theme.font_summary) + _text_height(theme.font_tiny)
        + sum(layout.summary_vertical_padding)
    )
    state_height = (
        layout.minimum_window_size[1] - topbar_height
        - 2 * layout.main_vertical_padding - summary_height
    )
    editor_content_height = state_height - 2 * layout.state_vertical_padding - 2 * layout.highlight_thickness
    required_editor_height = (
        2 * (_text_height(theme.font_label) + 5)
        + _text_height(theme.font_heading) + 12
        + _text_height(theme.font_label) + 4 + _text_height(theme.font_body) + 8
        + 8 * _text_height(theme.font_text)
        + _text_height(theme.font_button) + 2 * 8 + 12
    )
    editor_width = (
        layout.minimum_window_size[0] - layout.sidebar_width
        - 2 * layout.main_horizontal_padding - 2 * layout.state_horizontal_padding
        - layout.notes_list_width - layout.notes_list_gap
    )

    assert editor_content_height > required_editor_height
    assert editor_width >= 300
    assert (editor_width - 8) / 2 >= 140
    assert _text_width(theme.font_label, "Hashtags") <= (editor_width - 8) / 2


def test_password_dialog_text_and_actions_fit_its_theme_geometry():
    theme = ui.THEME
    layout = theme.layout
    dialog_width, dialog_height = layout.password_dialog_size
    content_width = dialog_width - 2 * (18 + layout.password_dialog_padding)
    content_height = dialog_height - 2 * 18
    action_width = sum(
        _text_width(theme.font_button, label)
        + 2 * layout.button_horizontal_padding
        + 2 * layout.highlight_thickness
        for label in ("Cancelar", "Continuar")
    ) + 8
    prompt = "Digite a senha desta base para desbloqueá-la."
    required_height = (
        _text_height(theme.font_heading, "Confirmar senha") + 8
        + _wrapped_line_count(theme.font_body, prompt, layout.password_prompt_wrap)
        * _text_height(theme.font_body) + 18
        + _text_height(theme.font_label) + 5
        + _text_height(theme.font_body) + 14
        + _text_height(theme.font_button) + 2 * 8
        + 2 * layout.highlight_thickness + 22
    )

    assert layout.password_prompt_wrap <= content_width
    assert _text_width(theme.font_heading, "Confirmar senha") <= content_width
    assert action_width <= content_width
    assert required_height <= content_height


def test_unsaved_changes_dialog_actions_fit_its_theme_geometry():
    theme = ui.THEME
    layout = theme.layout
    width, height = layout.unsaved_dialog_size
    content_width = width - 2 * (18 + layout.unsaved_dialog_padding)
    action_width = sum(
        _text_width(theme.font_button, label)
        + 2 * layout.button_horizontal_padding
        + 2 * layout.highlight_thickness
        for label in ("Salvar  ⌘S", "Descartar  ⌘⌫", "Cancelar  Esc")
    ) + 16
    description = "Salve antes de continuar ou descarte o que ainda não foi salvo."
    required_height = (
        _text_height(theme.font_heading) + 8
        + _wrapped_line_count(theme.font_body, description, content_width)
        * _text_height(theme.font_body)
        + 24 + _text_height(theme.font_button) + 2 * 8
        + 2 * 20
    )

    assert action_width <= content_width
    assert required_height <= height - 2 * 18
