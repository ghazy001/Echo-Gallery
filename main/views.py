from events.models import Event
from blog.models import Article
from gallery.models import  ArtworkFeedback
from django.shortcuts import  get_object_or_404
from workshops.models import Workshop
from .forms import ImageGenerateForm, BackgroundRemoveForm , ImageEditorForm
from django.utils import timezone
from django.shortcuts import  redirect
from django.contrib import messages
import base64
import requests
from django.db.models import Q
from gallery.models import Artwork
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from groq import Groq
from .utils import clean_profanity
from .utils import get_weather_for_city
import os
from django.conf import settings
from django.shortcuts import render
from .forms import ArtUploadForm
from .ml_model import predict_image
from .forms import PriceForm
from .price_ml import predict_price
import colorsys




FACEPP_API_KEY = "jzgXwXuwHh0xrjV-EG3aAo6G9fvjleK8"
FACEPP_API_SECRET = "YzsRe5onLZElJlp0IeevyhNKASKJLSec"


def index(request):
    return render(request, 'main/index.html')


# ---------------------- events --------------------------

def public_events_list_view(request):
    events = (
        Event.objects
        .filter(is_published=True)
        .select_related('place')
        .order_by('start_date')
    )
    return render(request, 'main/events/public_events_list.html', {
        'events': events
    })


def public_event_weather_view(request, event_id):
    """
    Return current weather for this event's city as JSON.
    Used by front-end JS in public_event_detail.html.
    """
    event = get_object_or_404(
        Event.objects.select_related('place'),
        id=event_id,
        is_published=True
    )

    city = event.place.city if event.place and event.place.city else ""
    weather_data = get_weather_for_city(city)

    return JsonResponse(weather_data)


def public_event_detail_view(request, event_id):
    event = get_object_or_404(
        Event.objects.select_related('place'),
        id=event_id,
        is_published=True
    )
    return render(request, 'main/events/public_event_detail.html', {
        'event': event
    })


# ---------------------- blog --------------------------

def public_article_list_view(request):
    articles = (
        Article.objects
        .filter(is_published=True)
        .select_related('category', 'author')
        .order_by('-published_at')
    )
    return render(request, 'main/articles/public_blog_list.html', {
        'articles': articles
    })


def public_article_detail_view(request, article_id):
    article = get_object_or_404(
        Article.objects.select_related('category', 'author'),
        id=article_id,
        is_published=True
    )
    return render(request, 'main/articles/public_blog_detail.html', {
        'article': article
    })


 # ---------------------- gallery --------------------------


def public_artwork_list_view(request):
    """
    Show all visible artworks to visitors.
    """
    artworks = Artwork.objects.filter(is_visible=True).order_by('-created_at')
    return render(request, 'main/artwork/public_artwork_list.html', {
        'artworks': artworks
    })


def public_artwork_detail_view(request, artwork_id):
    """
    Show 1 artwork + approved feedback.
    Also handle POST form to submit new feedback.
    """
    # 1. Fetch artwork or 404 if hidden
    artwork = get_object_or_404(
        Artwork,
        id=artwork_id,
        is_visible=True
    )

    # 2. Only show approved feedback publicly
    approved_feedback = (
        ArtworkFeedback.objects
        .filter(artwork=artwork, is_approved=True)
        .select_related('user')
        .order_by('-created_at')
    )

    # 3. Handle new feedback submit
    if request.method == "POST":
        raw_name = request.POST.get("name", "").strip()
        raw_comment = request.POST.get("comment", "").strip()
        raw_rating = request.POST.get("rating", "").strip()

        # rating normalization: must be int 1-5, default 5
        if raw_rating.isdigit():
            rating_val = int(raw_rating)
            rating_val = min(max(rating_val, 1), 5)
        else:
            rating_val = 5

        # basic validation
        if raw_comment == "":
            messages.error(request, "Comment cannot be empty.")
        else:
            # censor profanity BEFORE save
            safe_comment = clean_profanity(raw_comment)

            fb = ArtworkFeedback(
                artwork=artwork,
                comment=safe_comment,
                rating=rating_val,
                created_at=timezone.now(),
                is_approved=False,  # still needs moderation
            )

            if request.user.is_authenticated:
                fb.user = request.user
            else:
                fb.name = raw_name or "Anonymous"

            fb.save()

            messages.success(
                request,
                "Thanks! Your feedback was submitted and is waiting for approval."
            )

            # redirect after POST (PRG pattern)
            return redirect('public_artwork_detail', artwork_id=artwork.id)

    # 4. Prefill name in form if logged in
    initial_name = request.user.username if request.user.is_authenticated else ""

    context = {
        "artwork": artwork,
        "approved_feedback": approved_feedback,
        "initial_name": initial_name,
    }
    return render(request, "main/artwork/public_artwork_detail.html", context)




# ---------------------- workshops --------------------------



def public_workshop_list_view(request):
    now = timezone.now()
    # active and in the future or ongoing
    workshops = (
        Workshop.objects
        .filter(is_active=True, end_time__gte=now)
        .select_related('place')
        .prefetch_related('materials')
        .order_by('start_time')
    )

    return render(request, 'main/workshops/public_workshop_list.html', {
        'workshops': workshops
    })


def public_workshop_weather_view(request, workshop_id):
    """
    Returns weather as JSON for the workshop's city.
    Used by AJAX on the detail page.
    """
    workshop = get_object_or_404(
        Workshop.objects.select_related('place'),
        id=workshop_id,
        is_active=True
    )

    city = workshop.place.city if workshop.place and workshop.place.city else ""
    weather_data = get_weather_for_city(city)

    return JsonResponse(weather_data)


def public_workshop_detail_view(request, workshop_id):
    workshop = get_object_or_404(
        Workshop.objects.select_related('place').prefetch_related('materials'),
        id=workshop_id,
        is_active=True
    )

    return render(request, 'main/workshops/public_workshop_detail.html', {
        'workshop': workshop
    })





# ---------------------- image generation --------------------------



def ai_image_generator_page(request):
    image_url = None
    error = None

    print("DEBUG KEY:", settings.DEEPAI_API_KEY)

    if request.method == "POST":
        form = ImageGenerateForm(request.POST)
        if form.is_valid():
            prompt = form.cleaned_data["prompt"]

            try:
                resp = requests.post(
                    "https://api.deepai.org/api/text2img",
                    data={'text': prompt},
                    headers={'api-key': settings.DEEPAI_API_KEY},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                image_url = data.get("output_url")
                if not image_url:
                    error = "The AI did not return an image. Try another prompt."

            except requests.exceptions.RequestException as e:
                error = f"Request failed: {e}"
    else:
        form = ImageGenerateForm()

    return render(
        request,
        "main/Ai/generator.html",
        {
            "form": form,
            "image_url": image_url,
            "error": error,
        }
    )


#---------------------- ai background removal --------------------------

def ai_background_remover_page(request):
    output_url = None
    error = None

    if request.method == "POST":
        form = BackgroundRemoveForm(request.POST, request.FILES)
        if form.is_valid():
            img_file = form.cleaned_data["image"]

            # choose the key source:
            # 1. try env (recommended, like before)
            # 2. fallback hardcoded for dev ONLY
            api_key = getattr(settings, "DEEPAI_API_KEY", None) or "94242180-9293-4b4f-af09-f9e3fe00b173"

            try:
                resp = requests.post(
                    "https://api.deepai.org/api/background-remover",
                    headers={"api-key": api_key},
                    files={
                        "image": (img_file.name, img_file.read())
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                # DeepAI usually returns {"output_url": "..."}
                output_url = data.get("output_url")
                if not output_url:
                    error = "The AI did not return a processed image. Try another file."

            except requests.exceptions.RequestException as e:
                error = f"Request failed: {e}"

        else:
            error = "Invalid form. Please upload an image."
    else:
        form = BackgroundRemoveForm()

    return render(
        request,
        "main/Ai/background_remove.html",
        {
            "form": form,
            "output_url": output_url,
            "error": error,
        }
    )


#---------------------- ai image editor --------------------------

def ai_photo_editor_page(request):
    output_url = None
    error = None

    if request.method == "POST":
        form = ImageEditorForm(request.POST, request.FILES)
        if form.is_valid():
            img_file = form.cleaned_data["image"]
            edit_text = form.cleaned_data["text"]

            api_key = getattr(settings, "DEEPAI_API_KEY", None) or "94242180-9293-4b4f-af09-f9e3fe00b173"

            try:
                resp = requests.post(
                    "https://api.deepai.org/api/image-editor",
                    headers={"api-key": api_key},
                    files={
                        "image": (img_file.name, img_file.read()),
                    },
                    data={
                        "text": edit_text,
                    },
                    timeout=40,
                )
                resp.raise_for_status()
                data = resp.json()

                output_url = data.get("output_url")
                if not output_url:
                    error = "The AI did not return an edited image. Try adjusting your edit text."

            except requests.exceptions.RequestException as e:
                error = f"Request failed: {e}"
        else:
            error = "Please provide an image and edit instructions."
    else:
        form = ImageEditorForm()

    return render(
        request,
        "main/Ai/photo_editor.html",
        {
            "form": form,
            "output_url": output_url,
            "error": error,
        }
    )


#---------------------- Detect Emotion --------------------------

def emotion_page(request):
    """
    Render the camera UI page.
    This will show: live webcam, Detect Emotion button, and results.
    """
    return render(request, "main/emotion/emotion_page.html")


@csrf_exempt
def emotion_analyze(request):
    """
    POST { "image_b64": "<base64 jpeg>" }
    1. Convert base64 to bytes
    2. Send to Face++ /emotion
    3. Return the dominant emotion and a simplified label
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # Parse JSON body
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    image_b64 = body.get("image_b64")
    if not image_b64:
        return JsonResponse({"error": "Missing image_b64"}, status=400)

    # Convert base64 string -> raw bytes
    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return JsonResponse({"error": "Invalid base64 image"}, status=400)

    # Build form-data for Face++
    files = {
        "image_file": ("snapshot.jpg", image_bytes, "image/jpeg"),
    }
    data = {
        "api_key": FACEPP_API_KEY,
        "api_secret": FACEPP_API_SECRET,
        "return_attributes": "emotion",
    }

    # Call Face++
    try:
        face_resp = requests.post(
            "https://api-us.faceplusplus.com/facepp/v3/detect",
            data=data,
            files=files,
            timeout=10,
        )
        face_resp.raise_for_status()
    except requests.RequestException as e:
        return JsonResponse({"error": f"Face++ request failed: {e}"}, status=500)

    face_json = face_resp.json()
    faces = face_json.get("faces", [])

    if not faces:
        return JsonResponse({"status": "no_face", "message": "No face detected"})

    attrs = faces[0].get("attributes", {})
    emotion_scores = attrs.get("emotion", {})

    if not emotion_scores:
        return JsonResponse({"status": "no_emotion", "message": "No emotion info"})

    # Get the dominant emotion from Face++ scores
    dominant_emotion = max(emotion_scores, key=lambda k: emotion_scores[k])
    intensity = emotion_scores[dominant_emotion]

    # Simplify for UX: collapse to happy / sad / neutral etc.
    # You can tune these rules.
    simplified = "neutral"
    if dominant_emotion == "happiness":
        simplified = "happy"
    elif dominant_emotion in ["sadness", "fear", "disgust", "anger"]:
        simplified = "sad"
    elif dominant_emotion == "surprise":
        simplified = "surprised"

    return JsonResponse({
        "status": "ok",
        "dominant_emotion": dominant_emotion,  # e.g. "happiness", "sadness"
        "intensity": intensity,                # numeric strength
        "simplified": simplified,              # e.g. "happy", "sad"
        "raw": emotion_scores,                 # full dict from Face++
    })


@csrf_exempt
def recommend_artworks_for_emotion(request):
    """
    POST { "emotion": "happy" }
    Use the emotion to search Artworks.
    We'll match description keywords for that emotion.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    emotion = body.get("emotion", "").strip().lower()
    if not emotion:
        return JsonResponse({"error": "Missing emotion"}, status=400)

    # Map an emotion to keywords to look for in Artwork.description
    EMOTION_KEYWORDS = {
        "happy": ["happy", "happiness", "joy", "joyful", "smile", "celebration", "love"],
        "sad": ["sad", "sadness", "lonely", "melancholy", "tears", "grief"],
        "angry": ["anger", "angry", "rage", "furious", "violence"],
        "fear": ["fear", "anxiety", "terror", "afraid"],
        "surprised": ["surprise", "astonished", "wonder", "awe", "shocked"],
        "neutral": [],
    }

    keywords = EMOTION_KEYWORDS.get(emotion, [])

    if keywords:
        q_obj = Q()
        for kw in keywords:
            q_obj |= Q(description__icontains=kw)

        artworks_qs = (
            Artwork.objects
            .filter(is_visible=True)
            .filter(q_obj)
            .order_by("-created_at")
        )
    else:
        # fallback for neutral / unknown -> just recent visible art
        artworks_qs = (
            Artwork.objects
            .filter(is_visible=True)
            .order_by("-created_at")[:10]
        )

    out = []
    for art in artworks_qs:
        out.append({
            "id": art.id,
            "title": art.title,
            "artist": art.artist,
            "description": art.description[:200] + ("..." if len(art.description) > 200 else ""),
            "image_url": art.image.url if art.image else None,
        })

    return JsonResponse({
        "status": "ok",
        "emotion": emotion,
        "count": len(out),
        "artworks": out,
    })



#---------------------- chatbot --------------------------

def ai_chat_page(request):
    """
    Renders the chat UI (hero + chat card).
    """
    return render(request, "main/Ai/chat_page.html")


@csrf_exempt
def ai_chat_send(request):
    """
    AJAX endpoint.
    Expects JSON: { "message": "hi" }
    Returns JSON: { "reply": "hello human" }

    We'll send the single user message to Groq and get a completion.
    We'll keep conversation on the frontend for now.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_message = body.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    # init Groq client
    client = Groq(api_key=getattr(settings, "GROQ_API_KEY", None))

    # Build messages list.
    # For now we give minimal context: a system-style intro + latest user message.
    # You can later extend this to include previous turns (chat history).
    groq_messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant for the Art Museum website. Be friendly and concise.",
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=groq_messages,
            temperature=1,
            max_completion_tokens=512,
            top_p=1,
            reasoning_effort="medium",
            stream=False,  # important: we'll get a full response, easier for AJAX
            stop=None,
        )

        # Groq returns choices[0].message.content for non-stream
        reply_text = completion.choices[0].message.content

    except Exception as e:
        return JsonResponse({"error": f"Groq API failed: {e}"}, status=500)

    return JsonResponse({
        "reply": reply_text,
    })



# ---------------------- ml model for artist prediction --------------------------

def identify_artist_view(request):
    context = {
        "form": ArtUploadForm(),
        "result": None,
        "uploaded_image_url": None,
    }

    if request.method == "POST":
        form = ArtUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # 1. get uploaded file
            img_file = form.cleaned_data["image"]

            # 2. save it to media/uploads/
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, img_file.name)

            # Write file to disk
            with open(file_path, "wb+") as dest:
                for chunk in img_file.chunks():
                    dest.write(chunk)

            # 3. run prediction
            result = predict_image(file_path)

            # 4. build public URL so we can display the uploaded image back to user
            uploaded_image_url = settings.MEDIA_URL + "uploads/" + img_file.name

            context["form"] = ArtUploadForm()  # empty form again
            context["result"] = result
            context["uploaded_image_url"] = uploaded_image_url

            return render(request, "main/Ml/upload.html", context)

        else:
            context["form"] = form
            return render(request, "main/Ml/upload.html", context)

    # GET (just show the form)
    return render(request, "main/Ml/upload.html", context)




#--------------------------- price prediction -----------------------------


def price_predict_view(request):
    context = {"form": PriceForm(), "prediction": None}
    if request.method == "POST":
        form = PriceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            price = predict_price(data)
            context["form"] = form
            context["prediction"] = price
            return render(request, "main/Ml/price_predict.html", context)
        context["form"] = form
    return render(request, "main/Ml/price_predict.html", context)




def _hex_to_palette(hex_str: str) -> str:
    try:
        hex_str = hex_str.lstrip("#")
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
    except Exception:
        return ""

    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue = h * 360.0
    if 25 <= hue < 70:   return "Warm Tones"     # yellows/oranges
    if 70 <= hue < 170:  return "Earthy Tones"   # greens
    if 170 <= hue < 270: return "Cool Tones"     # blues
    if hue >= 270 or hue < 25: return "Warm Tones"  # reds/magentas
    return "Neutral Tones"

def price_predict_view(request):
    # use one 'form' variable for both GET and POST to keep the template happy
    form = PriceForm(request.POST or None)
    prediction = None

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        # If user picked a color on the wheel but didn’t set a palette, auto-fill it
        if not data.get("color_palette") and data.get("color_hex"):
            data["color_palette"] = _hex_to_palette(data["color_hex"])

        # IMPORTANT: keep your model’s expected keys (we already match them in price_ml.predict_price)
        prediction = predict_price(data)

    return render(request, "main/Ml/price_predict.html", {
        "form": form,
        "prediction": prediction,
    })


