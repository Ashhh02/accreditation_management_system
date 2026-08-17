from django import forms

from .models import EvidenceSubmission


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [super().clean(item, initial) for item in data]
        return [super().clean(data, initial)]


class EvidenceSubmissionForm(forms.ModelForm):
    files = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True, 'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png'}),
    )
    link_url = forms.URLField(required=False, label='Supporting link')

    class Meta:
        model = EvidenceSubmission
        fields = ('self_evaluation', 'actual_situation')
        widgets = {
            'self_evaluation': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Explain how the program meets this requirement and cite the evidence.',
            }),
            'actual_situation': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Describe the current situation, implementation, and any gaps.',
            }),
        }


class ReviewActionForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            ('approve', 'Approve and forward'),
            ('revision', 'Request revision'),
            ('non_complied', 'Mark non-complied'),
        ),
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Add reviewer remarks...'}),
    )

    def __init__(self, *args, allow_non_complied=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not allow_non_complied:
            self.fields['action'].choices = (
                ('approve', 'Approve and forward'),
                ('revision', 'Request revision'),
            )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('action') == 'revision' and not cleaned.get('remarks', '').strip():
            self.add_error('remarks', 'Remarks are required when requesting a revision.')
        return cleaned
