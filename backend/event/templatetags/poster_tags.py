from django import template

register = template.Library()

@register.simple_tag
def generate_qrcode_for_event(event, fill, bg_color):
    return event.qrcode.generate(fill=fill, bg_color=bg_color)

