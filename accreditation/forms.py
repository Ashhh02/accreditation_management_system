from django import forms

from .models import EvidenceSubmission


ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png'}

ALLOWED_FILE_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'image/jpeg',
    'image/png',
}

# Aligned with DATA_UPLOAD_MAX_MEMORY_SIZE so a single file can never push a
# request over the body cap.
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


GENERIC_FILE_TYPES = {'application/octet-stream'}

UNSUPPORTED_TYPE_ERROR = (
    'Unsupported file type. Allowed: PDF, Word, Excel, PowerPoint, and JPEG/PNG images.'
)


def _validate_uploaded_file(uploaded):
    """Validate a single uploaded supporting file, raising a ValidationError if invalid."""
    if uploaded.size and uploaded.size > MAX_UPLOAD_SIZE:
        raise forms.ValidationError('Each supporting file must be smaller than 5 MB.')
    name = (uploaded.name or '').lower()
    extension = name.rsplit('.', 1)[-1].__str__() if '.' in name else ''
    extension = f'.{extension}' if extension else ''
    content_type = (uploaded.content_type or '').lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise forms.ValidationError(UNSUPPORTED_TYPE_ERROR)
    if content_type and content_type not in ALLOWED_FILE_TYPES | GENERIC_FILE_TYPES:
        raise forms.ValidationError('The file content does not match an allowed document type.')


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

    change_remarks = forms.CharField(
        required=False,
        label='What changed in this version? (optional)',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Briefly describe what is new or different in this upload (used in the version history).',
        }),
    )

    def clean_files(self):
        files = self.cleaned_data.get('files') or []
        for uploaded in files:
            _validate_uploaded_file(uploaded)
        return files


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
