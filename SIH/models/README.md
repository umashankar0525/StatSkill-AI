# Local model bundle

StatSkill AI uses stock Ollama models and does not require a cloud LLM API key.

Run `./setup.ps1` after cloning. It reads `manifest.json`, downloads
`llama3.2:3b` and `llama3.1:8b` from the Ollama registry, and caches
`all-MiniLM-L6-v2` for local embeddings.

The model weights are about 6.9 GB in total and are intentionally downloaded
by the setup script instead of being stored as Git objects. This keeps cloning
reliable, preserves the upstream Ollama model manifests and licenses, and gives
every contributor the same named model versions without requiring credentials.
