# GED RLA Prep Platform — Score 155 to 190+

A professional GED Reasoning Through Language Arts preparation platform.
10 full-length practice exams, real-time exam simulation, analytics, personalized recommendations.

## QUICK START

Default login: username=student / password=GEDprep2024!
Admin panel: /admin/ username=admin / password=admin123

## LOCAL SETUP (PyCharm)

Step 1: Open PyCharm -> File -> Open -> select ged_rla_platform folder

Step 2: Create virtual environment
  python -m venv venv
  Windows: venv\Scripts\activate
  Mac/Linux: source venv/bin/activate

Step 3: Install dependencies
  pip install -r requirements.txt

Step 4: Run migrations
  python manage.py migrate

Step 5: Populate test content (REQUIRED)
  python manage.py populate_tests

Step 6: Start server
  python manage.py runserver

Visit: http://127.0.0.1:8000

## PROJECT STRUCTURE

  ged_rla_platform/
  config/              Django settings and URLs
  exam/                Exam models, views, URLs, management commands
  dashboard/           Dashboard and analytics views
  templates/           All HTML templates
  static/css/          main.css + exam.css
  static/js/           exam.js (timer, navigation, auto-save)
  requirements.txt
  vercel.json
  README.md

## DATABASE SCHEMA

Models: PracticeTest, Passage, Question, TestAttempt, QuestionAnswer, UserProfile
SQLite by default - upgrade to PostgreSQL by editing DATABASES in config/settings.py

## VERCEL DEPLOYMENT

1. Push to GitHub
2. Import to vercel.com -> New Project
3. Set environment variables: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS
4. Deploy - build_files.sh runs automatically

For persistent data use Neon.tech free PostgreSQL + DATABASE_URL env var.

## FEATURES

Exam: 150-min timer, auto-save, question palette, flagging, keyboard shortcuts
Dashboard: GED score estimate, skill breakdown, score trend, recommendations
Results: Full review with correct/incorrect indicators and explanations
Analytics: Score history, category progress, path to 190+ tracker

## GED SCORE SCALE

100-144: Below Passing
145-164: Passing (goal minimum)
165-174: College Ready
175-200: College Ready / Mastery (target: 190+)
