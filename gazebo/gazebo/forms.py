from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser

MAJOR_CHOICES = {
    'CSOM': [
        ('accounting', 'Accounting: B.S.'),
        ('afc', 'Accounting for Finance and Consulting: B.S.'),
        ('ba', 'Business Analytics'),
        ('entrepreneurship', 'Entrepreneurship (co-concentration)'),
        ('finance', 'Finance: B.S.'),
        ('gm', 'General Management: B.S.'),
        ('ml', 'Management and Leadership: B.S.'),
        ('marketing', 'Marketing: B.S.'),
        ('om', 'Operations Management: B.S.')
    ],
    'CSON': [
        ('nursing', 'Nursing: B.S.'),
        ('gphcg', 'Global Public Health and the Common Good: B.A./B.S.')
    ],
    'MCAS': [
        ('aad', 'African and African Diaspora Studies'),
        ('ap', 'Applied Physics'),
        ('ah', 'Art History'),
        ('biochem', 'Biochemistry'),
        ('bio', 'Biology'),
        ('chem', 'Chemistry'),
        ('cs', 'Classical Studies'),
        ('comm', 'Communication'),
        ('csci', 'Computer Science'),
        ('econ', 'Economics'),
        ('eng', 'English'),
        ('eg', 'Environmental Geoscience'),
        ('es', 'Environmental Studies'),
        ('fs', 'Film Studies'),
        ('french', 'French'),
        ('gs', 'Geological Sciences'),
        ('german', 'German Studies'),
        ('gph', 'Global Public Health and the Common Good'),
        ('hs', 'Hispanic Studies'),
        ('hist', 'History'),
        ('hce', 'Human-Centered Engineering'),
        ('ind', 'Independent'),
        ('is', 'International Studies'),
        ('ics', 'Islamic Civilization and Societies'),
        ('it', 'Italian'),
        ('ling', 'Linguistics'),
        ('math', 'Mathematics'),
        ('music', 'Music'),
        ('neuro', 'Neuroscience'),
        ('phil', 'Philosophy'),
        ('phy', 'Physics'),
        ('pol', 'Political Science'),
        ('psych', 'Psychology'),
        ('rus', 'Russian'),
        ('ss', 'Slavic Studies'),
        ('soc', 'Sociology'),
        ('sa', 'Studio Art'),
        ('theatre', 'Theatre'),
        ('theo', 'Theology')
    ],
    'LSEHD': [
        ('ah', 'American Heritages: B.A.'),
        ('apphd', 'Applied Psychology and Human Development: B.A., B.S.'),
        ('ee', 'Elementary Education: B.A.'),
        ('mcs', 'Mathematics/Computer Science: B.A.'),
        ('psa', 'Perspectives on Spanish America: B.A.'),
        ('se', 'Secondary Education: B.A., B.S.'),
        ('tes', 'Transformative Educational Studies: B.A.')
    ]
}

MINOR_CHOICES = {
    'CSOM': [
        ('acc_cpa', 'Accounting for CPAs'),
        ('acc_fc', 'Accounting for Finance & Consulting'),
        ('fin', 'Finance'),
        ('ml', 'Management and Leadership'),
        ('msi', 'Managing for Social Impact and the Public Good'),
        ('mkt', 'Marketing')
    ],
    'LSEHD': [
        ('comm', 'Communication'),
        ('csd', 'Cyberstrategy and Design'),
        ('dti', 'Design Thinking and Innovation'),
        ('et', 'Educational Theatre'),
        ('lhe', 'Leadership in Higher Education and Community Settings'),
        ('iehs', 'Immigration, Education, and Humanitarian Studies'),
        ('msmt', 'Middle School Mathematics Teaching'),
        ('rem', 'Research, Evaluation, and Measurement'),
        ('rtj', 'Restorative and Transformational Justice'),
        ('se', 'Special Education'),
        ('tell', 'TELL Certificate'),
        ('aphd', 'Applied Psychology and Human Development'),
        ('fe', 'Foundation in Education'),
        ('ie', 'Inclusive Education'),
        ('se', 'Secondary Education')
    ],
    'MCAS': [
        ('aad', 'African and African Diaspora Studies'),
        ('as', 'American Studies'),
        ('ac', 'Ancient Civilization'),
        ('ag', 'Ancient Greek'),
        ('arabic', 'Arabic'),
        ('ah', 'Art History'),
        ('asian', 'Asian Studies'),
        ('bio', 'Biology'),
        ('cs', 'Catholic Studies'),
        ('chem', 'Chemistry'),
        ('chinese', 'Chinese'),
        ('cs', 'Computer Science'),
        ('dance', 'Dance'),
        ('ds', 'Data Science'),
        ('eees', 'East European and Eurasian Studies'),
        ('econ', 'Economics'),
        ('eng', 'English'),
        ('envs', 'Environmental Studies'),
        ('fpj', 'Faith, Peace & Justice'),
        ('fs', 'Film Studies'),
        ('fr', 'French'),
        ('gs', 'Geological Sciences'),
        ('ger', 'German'),
        ('gms', 'German Studies'),
        ('gph', 'Global Public Health and the Common Good'),
        ('hs', 'Hispanic Studies'),
        ('hist', 'History'),
        ('is', 'International Studies'),
        ('irs', 'Irish Studies'),
        ('ics', 'Islamic Civilization & Societies'),
        ('it', 'Italian'),
        ('js', 'Jewish Studies'),
        ('jour', 'Journalism'),
        ('las', 'Latin American Studies'),
        ('ling', 'Linguistics'),
        ('math', 'Mathematics'),
        ('mhhc', 'Medical Humanities, Health, and Culture'),
        ('music', 'Music'),
        ('phil', 'Philosophy'),
        ('phy', 'Physics'),
        ('rapl', 'Religion and American Public Life'),
        ('rus', 'Russian'),
        ('soc', 'Sociology'),
        ('sa', 'Studio Art'),
        ('theatre', 'Theatre'),
        ('theo', 'Theology'),
        ('wgs', "Women's & Gender Studies")
    ]
}

DEPARTMENT_CHOICES = {
    'MCAS': [
        ('aahf', 'Art, Art History, and Film'),
        ('bio', 'Biology'),
        ('chem', 'Chemistry'),
        ('cs', 'Classical Studies'),
        ('comm', 'Communication'),
        ('cs', 'Computer Science'),
        ('ees', 'Earth and Environmental Sciences'),
        ('esgs', 'Eastern, Slavic, and German Studies'),
        ('econ', 'Economics'),
        ('eng', 'Engineering'),
        ('eng', 'English'),
        ('hist', 'History'),
        ('math', 'Mathematics'),
        ('music', 'Music'),
        ('phil', 'Philosophy'),
        ('phys', 'Physics'),
        ('ps', 'Political Science'),
        ('pn', 'Psychology and Neuroscience'),
        ('rll', 'Romance Languages and Literatures'),
        ('soc', 'Sociology'),
        ('theatre', 'Theatre'),
        ('theo', 'Theology')
    ],
    'CSOM': [
        ('acc', 'Accounting'),
        ('ba', 'Business Analytics'),
        ('bls', 'Business Law and Society'),
        ('fin', 'Finance'),
        ('mo', 'Management and Organization'),
        ('mkt', 'Marketing')
    ],
    'LSEHD': [
        ('cdep', 'Counseling, Developmental, & Educational Psychology'),
        ('elhe', 'Educational Leadership & Higher Education'),
        ('dfe', 'Department of Formative Education'),
        ('mesa', 'Measurement, Evaluation, Statistics, & Assessment'),
        ('tcs', 'Teaching, Curriculum, and Society')
    ],
    'CSON': [
        ('nursing', 'Nursing')
    ]
}


SCHOOL_CHOICES = [
    ('CSOM', 'CSOM'),
    ('CSON', 'CSON'),
    ('MCAS', 'MCAS'),
    ('LSEHD', 'LSEHD'),
]

class StudentSignUpForm(forms.ModelForm):
    school = forms.ChoiceField(choices=SCHOOL_CHOICES)
    major = forms.ChoiceField(choices=[('', '---------')], required=False)
    minor = forms.ChoiceField(choices=[('', '---------')], required=False)

    class Meta:
        model = CustomUser
        fields = ('eagle_id', 'school', 'major', 'minor')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'school' not in self.data:
            self.fields['major'].choices = [('', '---------')]
            self.fields['minor'].choices = [('', '---------')]
        else:
            school = self.data['school']
            self.fields['major'].choices = MAJOR_CHOICES.get(school, [('', '---------')])
            self.fields['minor'].choices = MINOR_CHOICES.get(school, [('', '---------')])

    def clean(self):
        cleaned_data = super().clean()
        school = cleaned_data.get('school')
        major = cleaned_data.get('major')

        if school and not major:
            self.add_error('major', 'This field is required.')

class AdminSignUpForm(UserCreationForm):
    department = forms.ChoiceField(choices=[(key, key) for key in DEPARTMENT_CHOICES.keys()])

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'eagle_id', 'password1', 'password2', 'department')