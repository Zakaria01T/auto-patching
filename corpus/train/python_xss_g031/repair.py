def format_translation_entry(source_text):
    from django.utils.html import format_html
    return format_html("<div class='translation'>{}</div>", source_text)
