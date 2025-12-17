# Contributing to Frame2Game (F2G)

Thank you for your interest in contributing to Frame2Game.

Frame2Game is built to support solo developers and indie creators. Community contributions help improve stability, features, and usability for everyone.

Contributions of all kinds are welcome, including bug fixes, new features, UI improvements, performance optimizations, and documentation updates.

---

## Development Workflow

To keep the project stable and maintainable, Frame2Game follows a structured branching workflow.

---

## Branching Strategy

### Main Branches

- **main**
  - Stable production-ready code
  - All releases are tagged from this branch
  - Direct pushes are not allowed

- **dev**
  - Active development branch
  - All features and fixes are merged here first

### Supporting Branches

- **Feature branches**
  - Used for new features or bug fixes
  - Created from `dev`
  - Examples:
    - `feature-new-filter`
    - `feature-ui-update`
    - `fix-mask-artifacts`

- **Release branches** (optional)
  - Used to prepare EXE builds
  - Examples:
    - `release-v1.0.0`
    - `release-v1.1.0`

---

## Creating a Feature Branch

Always create new branches from `dev`:

```bash
git checkout dev
git pull
git checkout -b feature-your-feature-name


After making changes:

git add .
git commit -m "Add: new sprite styling filter"
git push origin feature-your-feature-name
```

---

## Recommended commit prefixes:

- `Add:` new feature
- `Fix:` bug fix
- `Refactor:` code improvement
- `Docs:` documentation update
- `UI:` UI-related update

## Submitting a Pull Request (PR)

Once your feature is ready:

1. Push your branch  
2. Open a Pull Request on GitHub  
3. Set:
   - Base branch → dev  
   - Compare branch → your feature branch  

### Your PR should include:
- A clear description of the change  
- Why the change is useful  
- Screenshots or examples if UI/output changed  

Example PR description:

#### Summary  
Added a new sprite-styling filter that applies toon shading.

#### Changes  
- Added filter in src/processing/filters.py  
- Updated GUI to include new filter option  

#### Screenshots  
<attach screenshot>  

#### Notes  
Compatible with existing filter pipeline.  

-----

## PR Checklist

Before submitting a PR:

- Code runs without errors  
- No large binaries or model files included  
- README/docs updated if needed  
- Branch is synced with dev  
- You followed contribution guidelines  

A maintainer will review your PR and merge it if approved.

---

## Development Setup

Install dependencies:
```bash
pip install -r requirements.txt  

cd Frame2Game

Run the application:

python main.py  

Note : for gpu support (currently ony nvidia gpu is supported via cuda) refer README.md
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```
-----

## Reporting Issues

If you find a bug or want to suggest a new feature, use the GitHub Issues section and choose the appropriate template.

A good issue includes:
- Problem description  
- Steps to reproduce  
- Expected vs actual behavior  
- Logs or screenshots  
- System details (OS, Python version, GPU, etc.)  

---

## What NOT to Commit

Please avoid committing:

- Model weights (.pt, .pth, .onnx, etc.)  
- Build outputs (dist/, build/, .exe)  
- Cached or temp files (__pycache__/, .DS_Store, .idea/)  
- Large media files unless approved  
- API keys or private configuration files  

These should be excluded in .gitignore.

---

## Project Structure Reference

```text
F2G/
├── src/                  Application source code
├── models/               Model instructions or downloads
├── assets/               Demo images (optional)
├── releases/             GitHub Releases
├── .github/              Issue & PR templates
├── main.py               Entry point
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── requirements.txt
└── .gitignore
 

---

## Thank You

Your contribution — big or small — helps improve Frame2Game for developers around the world.  
We appreciate your time, creativity, and effort.  
Together, we can make F2G a powerful and helpful tool for game development.
