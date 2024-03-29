from django import template

register = template.Library()


@register.filter 
def addclass(field, css):
        return field.as_widget(attrs={"class": css})

# синтаксис @register... , под которой описан класс addclass() - 
# это применение "декораторов", функций, обрабатывающих функции