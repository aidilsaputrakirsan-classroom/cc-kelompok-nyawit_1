from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cloud App API",
    description="API untuk mata kuliah Komputasi Awan",
    version="0.1.0"
)

# CORS - agar frontend bisa akses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Untuk development saja
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Hello from Cloud App API!",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/team")
def team_info():
    return {
        "team": "cloud-team-XX",
        "members": [
            # TODO: Isi dengan data tim Anda
            {"name": "Muchlis Wahyu Saputra", "nim": "10231054", "role": "Lead Backend"},
            {"name": "Ranaya Chintya Mahitsa", "nim": "10231078", "role": "Lead Frontend"},
            {"name": "Ahmad Baihaqi", "nim": "10221063", "role": "Lead DevOps"},
            {"name": "Az-Zahra Atikah Nurhaliza", "nim": "10231022", "role": "Lead QA & Docs"}
        ]
    }