from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
import requests, random, os
from .models import Word, History
from django.contrib.auth.decorators import login_required
from deep_translator import GoogleTranslator
from .forms import CustomUserCreationForm, CustomLoginForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Bookmark, Word
from django.shortcuts import get_object_or_404
from django.contrib import messages

from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_admin_user(request):
    User = get_user_model()
    if not User.objects.filter(email="admin@example.com").exists():
        User.objects.create_superuser(
            email="vetrivel@gmail.com",
            name="Admin",
            password="your_secure_password"
        )
        return HttpResponse("Superuser created")
    return HttpResponse("Superuser already exists")


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')  # Redirect to login so user sees the message
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')



import os
import requests
import json
import random
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from deep_translator import GoogleTranslator  # ✨ Added import
from .models import Word, History

# Helper function to create the prompt for the Llama 3 model
# your_app/views.py

def create_llm_prompt(word):
    """
    Creates a stricter, more detailed prompt for the AI to ensure valid JSON output.
    """
    return f"""
    You are a helpful dictionary assistant. Your task is to provide a detailed dictionary entry for the English word "{word}".
    You MUST respond with a single, valid JSON object and nothing else. Do not include any introductory text, explanations, or markdown formatting like ```json.

    The JSON object must strictly adhere to the following structure:
    - A root object with four keys: "summary", "meanings", "synonyms", "antonyms".
    - "summary": A string containing a concise, one-to-two-line definition.
    - "meanings": An array of objects. Each object must have three string keys: "part_of_speech", "definition", and "example".
    - "synonyms": An array of strings.
    - "antonyms": An array of strings.

    Ensure all keys and string values are enclosed in double quotes.

    Example for the word 'run':
    {{
      "summary": "To move at a speed faster than a walk, never having both or all feet on the ground at the same time.",
      "meanings": [
        {{
          "part_of_speech": "verb",
          "definition": "Move at a speed faster than a walk.",
          "example": "The dog loves to run in the park."
        }},
        {{
          "part_of_speech": "noun",
          "definition": "A period of running.",
          "example": "I go for a run every morning."
        }}
      ],
      "synonyms": ["sprint", "race", "dart", "dash"],
      "antonyms": ["walk", "stroll", "amble"]
    }}

    Now, provide ONLY the JSON object for the word "{word}":
    """
@login_required
def home_view(request):
    context = {}

    # Word of the Day logic
    if request.method == 'GET' and not request.GET.get('query'):
        all_words = Word.objects.exclude(all_meanings__isnull=True).exclude(all_meanings='')
        if all_words.exists():
            word_of_the_day_obj = random.choice(all_words)
            context['word_of_the_day'] = word_of_the_day_obj
            # ✨ NEW: Add bookmark status for Word of the Day
            context['wotd_is_bookmarked'] = word_of_the_day_obj.is_bookmarked_by(request.user)

    # Handle search
    search_word = request.GET.get('query', '').lower() if request.method == 'GET' else request.POST.get('word', '').lower()

    if search_word:
        user = request.user
        word_obj, created = Word.objects.get_or_create(word=search_word)

        if created or not word_obj.all_meanings:
            try:
                # --- 1. Get Definitions from Llama 3 ---
                HF_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
                if not HF_API_KEY:
                    raise ValueError("Hugging Face API key not configured.")

                api_url = "https://router.huggingface.co/v1/chat/completions"
                headers = {"Authorization": f"Bearer {HF_API_KEY}"}
                prompt = create_llm_prompt(search_word)

                payload = {
                    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.5,
                }

                llm_response = requests.post(api_url, headers=headers, json=payload, timeout=45)
                llm_response.raise_for_status()
                response_data = llm_response.json()
                content_str = response_data['choices'][0]['message']['content']
                
                json_start = content_str.find('{')
                json_end = content_str.rfind('}') + 1
                if json_start == -1 or json_end == 0:
                    raise ValueError("Invalid JSON response from the language model.")
                
                word_data = json.loads(content_str[json_start:json_end])

                # --- 1.5. Translate Definitions to Tamil --- ✨ NEW SECTION
                if 'meanings' in word_data and isinstance(word_data['meanings'], list):
                    for meaning in word_data['meanings']:
                        english_definition = meaning.get('definition', '')
                        if english_definition:
                            try:
                                # Translate and add the new key to the dictionary
                                translated_text = GoogleTranslator(source='auto', target='ta').translate(english_definition)
                                
                                meaning['definition_ta'] = translated_text
                            except Exception as e:
                                meaning['definition_ta'] = "" 
                        else:
                            meaning['definition_ta'] = ""

                # --- 2. Get Pronunciation (Audio) ---
                pronunciation_url = ""
                try:
                    audio_res = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{search_word}')
                    if audio_res.status_code == 200:
                        audio_data = audio_res.json()[0]
                        for phonetic in audio_data.get('phonetics', []):
                            if phonetic.get('audio'):
                                pronunciation_url = phonetic['audio']
                                break
                except Exception:
                    pass 

                # --- 3. Get Image from Pexels ---
                PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
                image_url = ""
                if PEXELS_API_KEY:
                    pexels_headers = {"Authorization": PEXELS_API_KEY}
                    image_response = requests.get(f'https://api.pexels.com/v1/search?query={search_word}&per_page=1', headers=pexels_headers)
                    if image_response.status_code == 200:
                        photos = image_response.json().get('photos', [])
                        if photos:
                            image_url = photos[0]['src']['medium']

                # --- 4. Save Everything to Database ---
                word_obj.all_meanings = json.dumps(word_data)
                word_obj.pronunciation = pronunciation_url
                word_obj.image_url = image_url
                word_obj.save()

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
                status_code = http_err.response.status_code
                if status_code == 401:
                    context['error'] = "Authentication Error: Please check your Hugging Face API key."
                elif status_code == 429:
                    context['error'] = "API Rate Limit Exceeded: Please wait a moment before trying again."
                elif status_code == 503:
                    context['error'] = "The AI model is starting up. Please try again shortly."
                else:
                    context['error'] = f"The API returned an error (Code: {status_code})."
                return render(request, 'home.html', context)
            
            except requests.exceptions.RequestException as e:
                context['error'] = f"A network error occurred: {e}"
                return render(request, 'home.html', context)

            except (ValueError, KeyError, json.JSONDecodeError):
                context['error'] = "Error processing the AI's response. It may not have provided a valid definition."
                return render(request, 'home.html', context)
            
            except Exception as e:
                # This will now catch any and all errors during the process
                context['error'] = f"An unexpected error occurred: {e}"
                print(f"--- DEBUG: A critical error occurred in the home view: {e}") # DEBUG
                return render(request, 'home.html', context)
            pass
        History.objects.get_or_create(user=user, word=word_obj)
        context['word'] = word_obj
        # ✨ NEW: Add bookmark status for the searched word
        context['word_is_bookmarked'] = word_obj.is_bookmarked_by(request.user)

    return render(request, 'home.html', context)





# your_app/views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

# ... your other views (home_view, history_view, etc.) ...

@login_required
def bookmark_word(request, word_id):
    # This view handles ADDING a bookmark via AJAX
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        word = get_object_or_404(Word, id=word_id)
        # get_or_create prevents duplicates and errors
        Bookmark.objects.get_or_create(user=request.user, word=word)
        return JsonResponse({'status': 'ok', 'message': 'Bookmarked successfully'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def unbookmark_word(request, word_id):
    # This view handles REMOVING a bookmark via AJAX
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        word = get_object_or_404(Word, id=word_id)
        # Filter and delete the specific bookmark
        Bookmark.objects.filter(user=request.user, word=word).delete()
        return JsonResponse({'status': 'ok', 'message': 'Bookmark removed'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def history_view(request):
    user_history = History.objects.filter(user=request.user).select_related('word').order_by('-searched_at')
    words = [entry.word for entry in user_history]
    return render(request, 'history.html', {'history': words})

@login_required
@login_required
def bookmarks_view(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('word')
    return render(request, 'bookmarks.html', {'bookmarks': bookmarks})


@login_required
def bookmark_word(request, word_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        word = get_object_or_404(Word, id=word_id)
        Bookmark.objects.get_or_create(user=request.user, word=word)
        return JsonResponse({'message': 'Bookmarked successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
