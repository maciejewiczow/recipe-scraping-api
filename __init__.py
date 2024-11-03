from dotenv import load_dotenv

load_dotenv(verbose=True)

from api.index import app  # noqa: E402

app.run()
