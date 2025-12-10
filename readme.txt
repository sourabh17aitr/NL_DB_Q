python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -e .

python -m ipykernel install --user --name=nldbq --display-name "Python (nldbq)"
jupyter notebook

pip freeze > requirements.txt
