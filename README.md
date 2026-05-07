# LinKo Server

FastAPI server skeleton for LinKo.

## Local Development

Install development dependencies:

```sh
python3 -m pip install -e ".[dev]"
```

Run tests:

```sh
python3 -m pytest -v
```

Run the development server:

```sh
python3 -m uvicorn app.main:app --reload
```
