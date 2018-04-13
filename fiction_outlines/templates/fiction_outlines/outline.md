# {{ outline.title }}

{{ outline.description }}
{% for item, info in annotated_list %}
{% if item.story_element_type == "root" %}{% else %}{% if item.story_element_type == "ss" %}**{{ item.name }}**{% else %}{% if item.story_element_type == "book" %}##{% elif item.story_element_type == "act" %}###{% elif item.story_element_type == "part" %}####{% else %}#####{% endif %} {{ item.name }}{% endif %}{% endif %}

{{ item.description }}
{% if item.story_element_type == "ss" %}
----
{% endif %}
{% endfor %}
