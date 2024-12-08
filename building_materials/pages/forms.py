from django import forms


class DynamicFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        attributes = kwargs.pop('attributes', {})
        super().__init__(*args, **kwargs)
        for key, values in attributes.items():
            self.fields[key] = forms.ChoiceField(
                choices=[('', 'Все')] + [(value, value) for value in values],
                required=False,
                label=key.capitalize()
            )
