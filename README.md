# AcademiaMatch

AI-Powered Research Collaboration Platform for Humber Polytechnic

## 🎯 Overview

AcademiaMatch connects external researchers with Humber Polytechnic faculty members based on research interests using advanced semantic analysis powered by Sentence Transformers.

## ✨ Features

- **User Registration**: Separate forms for external and internal (Humber) researchers
- **AI Matching**: Semantic similarity using Sentence Transformers (all-MiniLM-L6-v2)
- **Email Search**: Find matches by entering your email address
- **Auto-Generated Email Templates**: Pre-filled collaboration inquiry emails
- **Real-Time Counters**: Live display of registered researchers
- **Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Load initial data:
```bash
python load_data.py
```

3. Run the app:
```bash
python app.py
```

4. Visit: `http://localhost:5000`

### Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions.

**Recommended:** Deploy to Render.com (100% FREE)

## 📊 Tech Stack

- **Backend**: Flask 3.0
- **Database**: SQLite (SQLAlchemy ORM)
- **AI/ML**: Sentence Transformers, scikit-learn
- **Frontend**: HTML5, CSS3 (Responsive)
- **Deployment**: Render.com / Heroku / PythonAnywhere

## 📁 Project Structure

```
academiamatch/
├── app.py                  # Main Flask application
├── matching.py             # AI matching algorithm
├── load_data.py            # Data loading script
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register_external.html
│   ├── register_internal.html
│   ├── success.html
│   ├── matches.html
│   └── not_found.html
└── DEPLOYMENT_GUIDE.md     # Deployment instructions
```

## 🎨 Branding

- **Primary Color**: #003C71 (Humber Blue)
- **Accent Color**: #F7B500 (Humber Gold)
- **Institution**: Humber Polytechnic

## 📝 License

© 2025 Humber Polytechnic. All rights reserved.

## 🆘 Support

For issues or questions, contact the development team or refer to the DEPLOYMENT_GUIDE.md file.

---

**Built with ❤️ for Humber Polytechnic Research Community**
