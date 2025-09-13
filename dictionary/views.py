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




@login_required
def home_view(request):
    context = {}

    # ✅ Word of the Day (only on initial GET without query param)
    if request.method == 'GET' and not request.GET.get('query'):
        all_words = Word.objects.exclude(all_meanings__isnull=True).exclude(all_meanings='')  # only words with meanings
        if all_words.exists():
            context['word_of_the_day'] = random.choice(all_words)

    # 🔍 Handle search via GET (?query=word) or POST form
    search_word = request.GET.get('query', '').lower() if request.method == 'GET' else request.POST.get('word', '').lower()

    if search_word:
        user = request.user
        word_obj, created = Word.objects.get_or_create(word=search_word)

        if created or not word_obj.all_meanings:
            url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{search_word}'
            res = requests.get(url)

            try:
                data = res.json()

                if isinstance(data, dict):
                    context['error'] = data.get('message', 'Word not found')
                    return render(request, 'home.html', context)

                data = data[0]
                pronunciation = ''
                for phonetic in data.get('phonetics', []):
                    if phonetic.get('audio'):
                        pronunciation = phonetic['audio']
                        break

                all_meanings_list = []
                for meaning in data.get('meanings', []):
                    part_of_speech = meaning.get('partOfSpeech', '')
                    for definition in meaning.get('definitions', []):
                        def_text = definition.get('definition', '')
                        example = definition.get('example', '')
                        synonyms = definition.get('synonyms', [])
                        antonyms = definition.get('antonyms', [])

                        try:
                            tamil_def = GoogleTranslator(source='auto', target='ta').translate(def_text)
                        except Exception as e:
                            tamil_def = ""

                        all_meanings_list.append({
                            'part_of_speech': part_of_speech,
                            'definition': def_text,
                            'definition_ta': tamil_def,
                            'example': example,
                            'synonyms': synonyms,
                            'antonyms': antonyms,
                        })

                # 📷 Fetch image from Pexels
                PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
                headers = { "Authorization": PEXELS_API_KEY }
                image_response = requests.get(
                    f'https://api.pexels.com/v1/search?query={search_word}&per_page=1',
                    headers=headers
                )

                if image_response.status_code == 200:
                    photos = image_response.json().get('photos', [])
                    image_url = photos[0]['src']['medium'] if photos else ""
                else:
                    image_url = ""

                import json
                word_obj.all_meanings = json.dumps(all_meanings_list)
                word_obj.pronunciation = pronunciation
                word_obj.image_url = image_url
                word_obj.save()

            except Exception as e:
                context['error'] = f"Error processing the word: {e}"
                return render(request, 'home.html', context)

        # Save to history if not already saved for the user
        History.objects.get_or_create(user=user, word=word_obj)
        context['word'] = word_obj

    return render(request, 'home.html', context)


@login_required
def add_bookmark(request, word_id):
    word = Word.objects.get(id=word_id)
    Bookmark.objects.get_or_create(user=request.user, word=word)
    return redirect('home')

@login_required
def remove_bookmark(request, word_id):
    Bookmark.objects.filter(user=request.user, word_id=word_id).delete()
    return redirect('bookmarks')

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
