# Winter-Internship-Project
A privacy-first Telegram knowledge base bot that performs semantic question answering using sentence embeddings, with a secure, ephemeral admin web interface exposed only on demand.

This project was built with a strong emphasis on:
  🔒 Security without traditional login systems
  🧠 Semantic correctness over hallucination
  🧩 Modular, maintainable architecture
  🚀 Practical deployment under real constraints



✨ Key Features
  🤖 Telegram Knowledge Base Bot
      Uses FAISS + SentenceTransformers for semantic search
      Answers only when confidence is sufficient
      Gracefully handles low-confidence queries
      Supports multi-source answer merging
      Allows users to download original source files
      Runs locally using Telegram polling (no public server)
      
  🛠 Secure Admin Panel (On-Demand Access)
      Admin panel is not permanently exposed
      No username/password login system required
      Access is granted only via Telegram
      Uses ngrok to create a temporary, random URL
      URL is automatically invalidated after inactivity
      Admin access is controlled by Telegram User IDs      
      💡 The admin panel exists only when explicitly requested and shuts itself down automatically.



🔐 Security Model (Design Highlight)
    Instead of a traditional login system, this project uses a semaphore-based access model:
      A shared admin_state.json file acts as a control channel
      The Telegram bot requests admin access
      A separate supervisor process decides and executes
      ngrok URLs are:
        Random
        Short-lived
        Never reused
      No persistent public endpoints exist
    This significantly reduces the attack surface while keeping administration simple.



🧱 Project Architecture
Winter-Internship-Project/
│
├── Bot/
│   └── telegram_bot.py          # Telegram bot (polling-based)
│
├── admin_access.py              # Admin access supervisor (ngrok control)
├── admin_state.json             # Shared semaphore/state file
├── admin_config.json            # Admin Telegram user IDs
│
├── Data/
│   ├── embeddings.faiss         # FAISS vector index
│   └── meta.json                # Knowledge base metadata
│
├── Notes/                       # Source documents (PDF / MD / TXT)
│
└── README.md



🧠 How It Works (High-Level Flow)
    User Query Flow
    1. User asks a question on Telegram
    2. Query is embedded using SentenceTransformer
    3. FAISS retrieves top semantic matches
    4. Bot:
        Filters weak matches
        Evaluates confidence
        Merges answers if required
    5. Response is framed with confidence signaling
    6. Optional source files can be downloaded

    Admin Access Flow
    1. Admin sends /admin to the bot
    2. Bot verifies Telegram User ID
    3. Bot sets activate=true in admin_state.json
    4. admin_access.py detects the request
    5. ngrok is started and URL generated
    6. Admin receives the temporary link
    7. Inactivity timer starts
    8. ngrok shuts down automatically after timeout



🚀 Setup & Usage
    1️⃣ Install Dependencies
    
        pip install python-telegram-bot faiss-cpu sentence-transformers requests

        Ensure ngrok is installed and accessible from the command line.

    2️⃣ Configure Admins
        Edit admin_config.json:
          
        {
          "admins": [123456789]
        }

        (Use your Telegram numeric user ID.)

    3️⃣ Start Admin Supervisor
        
        python admin_access.py

        This process:
          Does nothing by default
          Waits for bot requests
          Manages ngrok lifecycle

    4️⃣ Start Telegram Bot
  
        python telegram_bot.py

        The bot will:
          Answer knowledge queries
          Respond to /admin for authorized users



📁 Knowledge Base Format
    Each entry in meta.json contains:

    {
      "id": "unique_id",
      "question": "Concept title",
      "answer": "Explanation text",
      "tags": ["topic", "subtopic"],
      "source": {
        "path": {
        "pdf": "/Notes/example.pdf"
        }
      }
    }



🧪 Design Principles
  ❌ No hallucination
  📉 Confidence-aware responses
  🔎 Semantic relevance over keyword matching
  🔐 No permanent public endpoints
  🧩 Decoupled components
  🛠 Simple, explainable logic



📌 Why This Project Is Different
    Avoids traditional authentication entirely
    Uses Telegram identity as the trust anchor
    Admin interface is ephemeral by design
    Suitable for local, academic, and sensitive datasets
    Built to function under real-world constraints (no cloud, no fixed IP)



🧾 Future Improvements
    JWT-based temporary admin tokens
    HTTPS self-hosted tunnel alternative
    Role-based admin privileges
    Web-based analytics dashboard
    Multi-admin concurrency handling



📄 License
    This project is intended for educational and academic use.



🙌 Acknowledgements
    SentenceTransformers
    FAISS
    python-telegram-bot
    ngrok
