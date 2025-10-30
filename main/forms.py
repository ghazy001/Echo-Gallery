from django import forms

class ImageGenerateForm(forms.Form):
    prompt = forms.CharField(
        label="Describe the image you want",
        widget=forms.Textarea(attrs={
            "placeholder": "a cyberpunk cat hacking a computer, neon lighting, 4k",
            "rows": 3,
            "class": "form-control",
        })
    )


class BackgroundRemoveForm(forms.Form):
    image = forms.ImageField(
        label="Upload an image to remove its background",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
        })
    )


class ImageEditorForm(forms.Form):
    image = forms.ImageField(
        label="Upload image to edit",
        required=True,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    text = forms.CharField(
        label="Describe the edit you want",
        required=True,
        widget=forms.Textarea(attrs={
            "placeholder": "Make it look like a cinematic sci-fi movie poster with neon lighting",
            "rows": 3,
            "class": "form-control",
        })
    )




class ArtUploadForm(forms.Form):
    image = forms.ImageField()











# ----------------------------- Price Prediction Form ----------------------------------------

# your_app/forms.py
from django import forms

PAINTER_CHOICES = [
    ("", "Select painter…"),
    ("Noah", "Noah"),
    ("Vincent", "Vincent"),
    ("Ava", "Ava"),
    ("Liam", "Liam"),
    ("Olivia", "Olivia"),
    # add the rest you have (total 11)
]

STYLE_CHOICES = [
    ("", "Select style…"),
    ("Abstract Expressionism", "Abstract Expressionism"),
    ("Modern", "Modern"),
    ("Cubism", "Cubism"),
    # add the rest (6 total)
]

MEDIUM_CHOICES = [
    ("", "Select medium…"),
    ("Oil", "Oil"),
    ("Acrylic", "Acrylic"),
    ("Watercolor", "Watercolor"),
    ("Charcoal", "Charcoal"),
    ("Ink", "Ink"),
]

SUBJECT_CHOICES = [
    ("", "Select subject…"),
    ("Landscape","Landscape"), ("Seascape","Seascape"), ("Abstract","Abstract"),
    ("Still Life","Still Life"), ("Wildlife","Wildlife"), ("Portrait","Portrait"),
    ("Cityscape","Cityscape"),
]

LOCATION_CHOICES = [
    ("", "Pick on map or choose…"),
    ("Miami", "Miami"),
    ("Chicago", "Chicago"),
    ("Calgary", "Calgary"),
    ("Online", "Online"),
    # add the rest you saw in your data
]

SHIPMENT_CHOICES = [
    ("", "Select…"),
    ("Free Shipping","Free Shipping"),
    ("Standard","Standard"),
    ("Express","Express"),
]

FRAME_CHOICES = [("", "Select…"), ("Yes","Yes"), ("No","No")]
COPY_ORIGINAL_CHOICES = [("", "Select…"), ("Original","Original"), ("Copy","Copy")]
PRINT_REAL_CHOICES = [("", "Select…"), ("Real","Real"), ("Print","Print")]

ENV_CHOICES = [
    ("", "Select…"),
    ("Living Room","Living Room"), ("Bedroom","Bedroom"), ("Office","Office"),
    ("Corporate","Corporate"), ("Kid Room","Kid Room"),
]

MOOD_CHOICES = [
    ("", "Select…"),
    ("Calming","Calming"), ("Relaxing","Relaxing"), ("Joyful","Joyful"),
    ("Reflective","Reflective"), ("Energetic","Energetic"),
]

LIGHTING_CHOICES = [
    ("", "Select…"),
    ("Natural Light","Natural Light"), ("Bright Light","Bright Light"),
    ("Dim Light","Dim Light"),
]

REPRO_CHOICES = [
    ("", "Select…"),
    ("Lithograph","Lithograph"), ("Screen Print","Screen Print"),
    ("Giclée","Giclée"), ("Poster","Poster"),
]

AUDIENCE_CHOICES = [
    ("", "Select…"),
    ("Corporate Clients","Corporate Clients"),
    ("Young Professionals","Young Professionals"),
    ("Collectors","Collectors"),
]

COLOR_PALETTE_CHOICES = [
    ("", "Auto from color wheel…"),
    ("Warm Tones","Warm Tones"),
    ("Cool Tones","Cool Tones"),
    ("Earthy Tones","Earthy Tones"),
    ("Neutral Tones","Neutral Tones"),
    ("Oceanic Tones","Oceanic Tones"),
]

UNIT_CHOICES = [("cm","cm"), ("in","in")]

class PriceForm(forms.Form):
    # Core
    artist = forms.ChoiceField(choices=PAINTER_CHOICES, label="Name of Painter")
    subject = forms.ChoiceField(choices=SUBJECT_CHOICES, required=False, label="Subject of Painting")
    style = forms.ChoiceField(choices=STYLE_CHOICES, required=False)
    medium = forms.ChoiceField(choices=MEDIUM_CHOICES, required=False)

    # Size (user-friendly)
    unit = forms.ChoiceField(choices=UNIT_CHOICES, initial="in", required=False, label="Units")
    height = forms.FloatField(required=False, min_value=1, label="Height")
    width = forms.FloatField(required=False, min_value=1, label="Width")
    size = forms.CharField(required=False, help_text='Auto-filled as HxW + unit (e.g. 20"x30").')

    frame = forms.ChoiceField(choices=FRAME_CHOICES, required=False)
    location = forms.CharField(required=False)

    delivery_days = forms.IntegerField(required=False, min_value=0, label="Delivery (days)")
    shipment = forms.ChoiceField(choices=SHIPMENT_CHOICES, required=False)

    color_palette = forms.ChoiceField(choices=COLOR_PALETTE_CHOICES, required=False)
    color_hex = forms.CharField(required=False)  # filled by color wheel, e.g. #ff7733

    copy_or_original = forms.ChoiceField(choices=COPY_ORIGINAL_CHOICES, required=False)
    print_or_real = forms.ChoiceField(choices=PRINT_REAL_CHOICES, required=False)

    environment = forms.ChoiceField(choices=ENV_CHOICES, required=False, label="Recommended Environment")
    mood = forms.ChoiceField(choices=MOOD_CHOICES, required=False, label="Mood/Atmosphere")
    lighting = forms.ChoiceField(choices=LIGHTING_CHOICES, required=False, label="Theme/Lighting Requirements")
    reproduction_type = forms.ChoiceField(choices=REPRO_CHOICES, required=False)
    audience = forms.ChoiceField(choices=AUDIENCE_CHOICES, required=False, label="Target Audience")



#-------------- fin ---------------------------