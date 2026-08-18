#### Packages

Django                5.2.4<br>
django-allauth        65.9.0<br>
django-browser-reload 1.18.0<br>
django-cleanup        9.0.0<br>
django-htmx           1.23.2<br>
pillow                11.3.0<br>

<br><br>


#### Getting the files
Download zip file<br> 
or <br>
git clone command (need git to be installed) and remove git folder afterwards
```
git clone https://github.com/24127271/SmartTourism.git . && rm -rf .git
```
<br><br><br>

## Setup

#### -Install ngrok

**macOS:**
```bash
brew install ngrok
```

**Windows/Linux:**
Download from [ngrok.com](https://ngrok.com/download)

#### - Create Virtual Environment
###### # Mac
```
python3 -m venv venv
source venv/bin/activate
```

###### # Windows
```
python3 -m venv venv
(Powershell:) .\venv\Scripts\Activate.ps1
```
```
(or Command Prompt:) venv\Scripts\activate 
(or Git Bash:) source venv/Scripts/activate
```

<br>

#### - Install dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```

<br>

#### - Migrate to database
```
python manage.py migrate
python manage.py createsuperuser
```

## 📝 Environment Variables

Create `myproject/.env` with these variables:
```env
OAUTH_GOOGLE_CLIENT_ID=91584285549-kk18q256qg7hs9nf3u9afk4ilf0bhs23.apps.googleusercontent.com
OAUTH_GOOGLE_SECRET=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
OAUTH_TWITTER_CLIENT_ID=bS1pZnN0WEoxOXM0am5PU2tlVGE6MTpjaQ
OAUTH_TWITTER_SECRET=Y91xjnffSy36LCuenpUx1TS1P67l0YxicoFajS4-e8cjNlLlN1
OAUTH_FACEBOOK_CLIENT_ID=1947829022444167
OAUTH_FACEBOOK_SECRET=55f8d54964121036dd03dc23fa5e5c82
```

<br>

#### Run Django server

```bash
python manage.py runserver
```

#### Start ngrok (in a new terminal)

```bash
ngrok http 8000
```

<br>

#### - Generate Secret Key ( ! Important for deployment ! )
```
python manage.py shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
exit()
```


