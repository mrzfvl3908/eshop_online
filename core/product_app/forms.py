from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review

        fields = [
            'rating',
            'comment',
        ]

        widgets = {

            'rating': forms.RadioSelect(
                choices=[
                    (1, '1'),
                    (2, '2'),
                    (3, '3'),
                    (4, '4'),
                    (5, '5'),
                ],
                attrs={
                    'class': 'rating-input',
                }
            ),

            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Write your review...',
                }
            ),
        }

    def clean_comment(self):
        comment = self.cleaned_data['comment'].strip()

        if not comment:
            raise forms.ValidationError(
                'Please write your review.'
            )

        return comment
