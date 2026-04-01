# 🤝 Contributing to Stock Mirror Fish

Thank you for considering contributing! Every improvement — big or small — makes this tool better for everyone.

## 🚀 How to Contribute

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/stock-mirror-fish.git
cd stock-mirror-fish
```

### 2. Create a Branch
```bash
git checkout -b feature/amazing-new-feature
# or
git checkout -b fix/bug-description
```

### 3. Set Up Dev Environment
```bash
pip install -r requirements.txt
python app.py   # runs on http://localhost:8080
```

### 4. Make Your Changes
- Follow the existing code style (Python: PEP 8, JS: consistent with `dashboard.html`)
- Keep functions small and well-named
- Add comments for any non-obvious financial logic

### 5. Test Your Changes
```bash
python -m py_compile app.py   # syntax check
# Open http://localhost:8080 and test the dashboard
```

### 6. Commit with Emoji Conventions
```bash
git commit -m "✨ Add: VWAP indicator to chart overlay"
git commit -m "🐛 Fix: Kelly Criterion edge case when stop=0"
git commit -m "📊 Improve: Calmar ratio calculation accuracy"
git commit -m "📝 Docs: Add API endpoint documentation"
git commit -m "🎨 Style: Tighten spacing in heatmap strip"
```

### 7. Open a Pull Request
Push to your fork and open a PR against `main`. Include:
- What you changed and why
- Any screenshots for UI changes
- Test steps for the reviewer

---

## 🧮 Adding New Agent Metrics

To add a new risk metric to an agent:

```python
# In app.py — add your calculation function
def calc_my_metric(prices, returns):
    """Brief description of what this measures and why it matters."""
    try:
        result = ...  # your calculation
        return round(result, 2)
    except:
        return 0.0

# Then call it inside get_stock() and add to the result dict
"my_metric": calc_my_metric(prices, returns),
```

Then surface it in `dashboard.html` inside `renderTechnicals()`.

---

## 🐛 Reporting Bugs

Open a GitHub Issue with:
- OS and Python version
- Steps to reproduce
- Expected vs actual behaviour
- Any error messages from the terminal

---

## 💡 Feature Ideas

Check the [Roadmap in README.md](README.md#️-roadmap) for planned features. Open an Issue to discuss before building something large — we'd love to align on approach first.

---

## 📋 Code Style

- **Python**: PEP 8, type hints where practical
- **JS**: Vanilla ES6+, no frameworks, keep it readable
- **CSS**: CSS variables for all colours (see `:root` block)
- **Commits**: Emoji prefix as above

---

*Thank you for making Stock Mirror Fish better! 🐟*
