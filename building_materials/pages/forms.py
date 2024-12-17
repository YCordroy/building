from django import forms


class DynamicFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        attributes = kwargs.pop('attributes', {})
        super().__init__(*args, **kwargs)

        # Генерация чекбоксов
        for key, values in attributes.items():
            self.fields[key] = forms.MultipleChoiceField(
                choices=[(value, value) for value in values],
                required=False,
                label=key.capitalize(),
                widget=forms.CheckboxSelectMultiple()
            )
