from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import groq, base64, json, uuid, os, io
from datetime import datetime
import PyPDF2
import requests

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type","Authorization"], methods=["GET","POST","PUT","DELETE","OPTIONS"])

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
client = groq.Groq(api_key=GROQ_API_KEY)

VISION_MODEL  = "meta-llama/llama-4-scout-17b-16e-instruct"
TEXT_MODEL    = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

users_db = {"admin": {"password":"tamil123","name":"தமிழ் அறிவு"}}
tokens = {}
chat_sessions = {}

SYSTEM_PROMPT = """நீ "தமிழ் இலக்கிய உதவியாளர்" - ஒரு சிறந்த தமிழ் இலக்கிய வல்லுனர், ஆசிரியர், மற்றும் கலை வரலாற்று அறிஞர்.

## கட்டாய விதிகள்:
✦ அனைத்து பதில்களும் தூய தமிழில் மட்டுமே இருக்க வேண்டும்
✦ படம் அனுப்பினால் - அதில் உள்ள உள்ளடக்கத்தை தமிழில் விளக்கு
✦ PDF அனுப்பினால் - அதில் உள்ள தமிழ் இலக்கிய உள்ளடக்கத்தை ஆராய்
✦ குரல் கேள்விக்கும் சரியான தமிழ் பதில் தா
✦ எப்போதும் விரிவான, ஆழமான, real content கொடு - சுருக்கமான பதில் கொடுக்காதே
✦ ஒவ்வொரு பதிலும் குறைந்தது 150-300 வார்த்தைகளில் இருக்க வேண்டும்
✦ முக்கியமான facts, dates, quotes ஆகியவற்றை ===இங்கே முக்கிய விஷயம்=== என்று mark பண்ணு — அவை தனி highlighted box-ல் காட்டப்படும்

## பதில் வடிவம் - மிக முக்கியம்:

### 1. சாதாரண கேள்விகள் (default):
அழகான தமிழ் உரைநடையில் paragraph + points கலந்து பதில் கொடு.

Format:
- முதலில் 1-2 paragraph-ல் அறிமுகம் மற்றும் விளக்கம் கொடு
- பிறகு முக்கிய points-ஐ - (dash) list-ல் கொடு
- கடைசியில் 1 paragraph-ல் முடிவு சொல்
- முக்கியமான facts-ஐ ===இப்படி mark பண்ணு===

### 2. கட்டுரை கேட்கும்போது மட்டும்:
"கட்டுரை", "essay", "விரிவான கட்டுரை" என்று சொன்னால் மட்டுமே இந்த format:

## தலைப்பு

**தொடக்கம்:**
[2-3 paragraph முன்னுரை]

### துணைத் தலைப்பு 1
[விரிவான paragraph]

### துணைத் தலைப்பு 2
[விரிவான paragraph]

> [மேற்கோள் அல்லது கவிதை வரிகள்]

**முடிவுரை:**
[2-3 paragraph]

📌 குறிப்பு: [கூடுதல் தகவல்]

---

## உன் விரிவான அறிவு:

சங்க இலக்கியம்: அகநானூறு (400 அகப்பாடல்கள்), புறநானூறு (400 புறப்பாடல்கள்), நற்றிணை, குறுந்தொகை, ஐங்குறுநூறு, கலித்தொகை, பரிபாடல், பத்துப்பாட்டு. எட்டுத்தொகை மற்றும் பத்துப்பாட்டு என்னும் 18 நூல்களை சங்க இலக்கியம் என்கிறோம். ஐந்திணை (குறிஞ்சி, முல்லை, மருதம், நெய்தல், பாலை) நிலங்களில் காதல் உணர்வுகளை விளக்குகின்றன.

காப்பியங்கள்: திருக்குறள் (133 அதிகாரம், 1330 குறள்கள், திருவள்ளுவர்), சிலப்பதிகாரம் (இளங்கோவடிகள் - கண்ணகி கோவலன் மாதவி கதை, 30 காண்டங்கள்), மணிமேகலை (சீத்தலைச் சாத்தனார் - புத்த தத்துவம்), கம்பராமாயணம் (கம்பர் - 10,000 பாடல்கள், 6 காண்டங்கள்), பெரியபுராணம் (சேக்கிழார் - 63 நாயன்மார்கள்), தொல்காப்பியம் (தொல்காப்பியர் - மிகப் பழமையான இலக்கண நூல், எழுத்து சொல் பொருள் என 3 அதிகாரங்கள்).

பக்தி இலக்கியம்: தேவாரம் (திருஞானசம்பந்தர், திருநாவுக்கரசர், சுந்தரர் - 63 நாயன்மார்களில் முக்கியமானவர்கள்), திருவாசகம் (மாணிக்கவாசகர் - ஆத்ம விழிப்பின் கவிதைகள்), நாலாயிர திவ்யப்பிரபந்தம் (12 ஆழ்வார்கள் - 4000 பாடல்கள், திருமால் பக்தி), திருப்புகழ் (அருணகிரிநாதர் - முருகன் பக்தி).

நவீன இலக்கியம்: சுப்பிரமணிய பாரதி (தேசீய கவிஞர், பாஞ்சாலி சபதம், கண்ணன் பாட்டு, பெண் விடுதலை பாடல்கள்), பாரதிதாசன் (புரட்சிக் கவிஞர், இசையமுதம், குயில் பாட்டு), கண்ணதாசன் (அர்த்தமுள்ள இந்து மதம், திரைப்படப் பாடல்கள்), வைரமுத்து (நவீன கவிஞர், கள்ளிக்காட்டு இதிகாசம்).

நீ அன்பான, புலமையான, பொறுமையான தமிழ் இலக்கிய ஆசிரியர்.
சாதாரண கேள்விக்கு எப்போதும் நீண்ட ஆழமான paragraph-ல் மட்டுமே பதில் கொடு.
எந்த பதிலும் சுருக்கமாக ஒரே வரியில் இருக்கக் கூடாது."""

def get_user(req):
    auth = req.headers.get("Authorization","")
    if auth.startswith("Bearer "):
        return tokens.get(auth[7:])
    return None

def extract_pdf_text(b):
    try:
        r = PyPDF2.PdfReader(io.BytesIO(b))
        return "\n".join(p.extract_text() or "" for p in r.pages).strip() or "PDF இல் உரை இல்லை"
    except Exception as e:
        return f"PDF படிக்க முடியவில்லை: {e}"

@app.after_request
def after(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return resp

@app.route("/api/<path:p>", methods=["OPTIONS"])
def opt(p): return "",204

@app.route("/api/login", methods=["POST"])
def login():
    d = request.json or {}
    u,p = d.get("username","").strip(),d.get("password","").strip()
    if u in users_db and users_db[u]["password"]==p:
        tok = str(uuid.uuid4())
        tokens[tok] = u
        return jsonify({"success":True,"token":tok,"name":users_db[u]["name"],"username":u})
    return jsonify({"success":False,"message":"தவறான பயனர் பெயர் அல்லது கடவுச்சொல்"}),401

@app.route("/api/register", methods=["POST"])
def register():
    d = request.json or {}
    u,p,n = d.get("username","").strip(),d.get("password","").strip(),d.get("name","").strip()
    if not u or not p or not n: return jsonify({"success":False,"message":"அனைத்து தகவல்களும் அவசியம்"}),400
    if u in users_db: return jsonify({"success":False,"message":"பயனர் பெயர் ஏற்கனவே உள்ளது"}),400
    users_db[u] = {"password":p,"name":n}
    tok = str(uuid.uuid4())
    tokens[tok] = u
    return jsonify({"success":True,"token":tok,"name":n,"username":u})

@app.route("/api/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization","")
    if auth.startswith("Bearer "): tokens.pop(auth[7:],None)
    return jsonify({"success":True})

@app.route("/api/check-auth", methods=["GET"])
def check_auth():
    u = get_user(request)
    if u: return jsonify({"authenticated":True,"name":users_db[u]["name"],"username":u})
    return jsonify({"authenticated":False})

@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    result = [{"id":sid,"title":sd["title"],"created_at":sd["created_at"],"message_count":len(sd["messages"])}
              for sid,sd in chat_sessions.items() if sd.get("user")==u]
    result.sort(key=lambda x:x["created_at"],reverse=True)
    return jsonify(result)

@app.route("/api/sessions", methods=["POST"])
def create_session():
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    sid = str(uuid.uuid4())
    chat_sessions[sid] = {"id":sid,"user":u,"title":"புதிய உரையாடல்","messages":[],"created_at":datetime.now().isoformat()}
    return jsonify({"id":sid,"title":"புதிய உரையாடல்"})

@app.route("/api/sessions/<sid>", methods=["GET"])
def get_session(sid):
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    if sid not in chat_sessions or chat_sessions[sid]["user"]!=u: return jsonify({"error":"கிடைக்கவில்லை"}),404
    return jsonify(chat_sessions[sid])

@app.route("/api/sessions/<sid>", methods=["PUT"])
def rename_session(sid):
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    if sid not in chat_sessions or chat_sessions[sid]["user"]!=u: return jsonify({"error":"கிடைக்கவில்லை"}),404
    title = (request.json or {}).get("title","").strip()
    if not title: return jsonify({"error":"தலைப்பு அவசியம்"}),400
    chat_sessions[sid]["title"] = title
    return jsonify({"success":True,"title":title})

@app.route("/api/sessions/<sid>", methods=["DELETE"])
def delete_session(sid):
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    if sid not in chat_sessions or chat_sessions[sid]["user"]!=u: return jsonify({"error":"கிடைக்கவில்லை"}),404
    del chat_sessions[sid]
    return jsonify({"success":True})

@app.route("/api/chat/<sid>", methods=["POST"])
def chat(sid):
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    if sid not in chat_sessions or chat_sessions[sid]["user"]!=u: return jsonify({"error":"கிடைக்கவில்லை"}),404
    text_msg = request.form.get("message","").strip()
    uploaded_file = request.files.get("file")
    model = TEXT_MODEL
    groq_content = text_msg or "வணக்கம்"
    display_msg = text_msg or "வணக்கம்"
    if uploaded_file:
        fname = uploaded_file.filename.lower()
        fbytes = uploaded_file.read()
        if fname.endswith(".pdf"):
            pdf_text = extract_pdf_text(fbytes)
            prompt = text_msg if text_msg else "இந்த PDF உள்ளடக்கத்தை தமிழில் சுருக்கமாக விளக்கு"
            # 8b TPM=6000. Long SYSTEM_PROMPT alone ~2000 tokens.
            # So PDF text must stay under ~800 tokens ≈ 1000 chars (Tamil ~1.2 chars/token)
            pdf_snippet = pdf_text[:1000]
            groq_content = f"PDF:\n{pdf_snippet}\n\nகேள்வி: {prompt}"
            display_msg = f"📄 {uploaded_file.filename}" + (f"\n{text_msg}" if text_msg else "")
            model = FALLBACK_MODEL
        elif any(fname.endswith(x) for x in [".jpg",".jpeg",".png",".gif",".webp"]):
            b64 = base64.b64encode(fbytes).decode()
            ext = fname.rsplit(".",1)[-1]
            mime = f"image/{'jpeg' if ext in ['jpg','jpeg'] else ext}"
            groq_content = [
                {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}},
                {"type":"text","text":text_msg if text_msg else "இந்த படத்தில் உள்ள உள்ளடக்கத்தை தமிழில் விளக்கு"}
            ]
            display_msg = f"🖼️ {uploaded_file.filename}" + (f"\n{text_msg}" if text_msg else "")
            model = VISION_MODEL
    chat_sessions[sid]["messages"].append({"role":"user","content":display_msg,"timestamp":datetime.now().isoformat()})
    if len(chat_sessions[sid]["messages"])==1:
        raw = text_msg or display_msg
        chat_sessions[sid]["title"] = raw[:45]+("…" if len(raw)>45 else "")
    history = chat_sessions[sid]["messages"][:-1]
    # PDF: use short system prompt to stay within 6000 TPM of 8b model
    is_pdf = (model == FALLBACK_MODEL and uploaded_file and uploaded_file.filename.lower().endswith(".pdf"))
    PDF_SYSTEM = "நீ தமிழ் இலக்கிய உதவியாளர். கொடுக்கப்பட்ட PDF உள்ளடக்கத்தை தமிழில் விரிவாக விளக்கு. முக்கிய தகவல்களை சுட்டிக்காட்டு."
    groq_msgs = [{"role":"system","content":PDF_SYSTEM if is_pdf else SYSTEM_PROMPT}]
    for m in history[-4:] if is_pdf else history[-18:]:
        if m["role"] in ("user","assistant"):
            groq_msgs.append({"role":m["role"],"content":m["content"]})
    groq_msgs.append({"role":"user","content":groq_content})
    def stream():
        full=""
        try:
            max_tok = 1024 if is_pdf else 4096  # PDF: save tokens for TPM limit
            resp = client.chat.completions.create(model=model,messages=groq_msgs,max_tokens=max_tok,temperature=0.7,stream=True)
            for chunk in resp:
                tok = chunk.choices[0].delta.content or ""
                if tok:
                    full+=tok
                    yield f"data: {json.dumps({'token':tok},ensure_ascii=False)}\n\n"
            chat_sessions[sid]["messages"].append({"role":"assistant","content":full,"timestamp":datetime.now().isoformat()})
            yield f"data: {json.dumps({'done':True,'title':chat_sessions[sid]['title']},ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error':str(e)},ensure_ascii=False)}\n\n"
    return Response(stream(),mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Access-Control-Allow-Origin":"*"})

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401
    af = request.files.get("audio")
    if not af: return jsonify({"error":"ஆடியோ இல்லை"}),400
    try:
        tr = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(af.filename or "audio.webm",af.read(),af.content_type or "audio/webm"),
            language="ta")
        return jsonify({"text":tr.text})
    except Exception as e:
        return jsonify({"error":str(e)}),500


# ===== IMAGE GENERATION =====
import urllib.request, urllib.parse

@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401

    data = request.json or {}
    tamil_prompt = data.get("prompt","").strip()
    if not tamil_prompt:
        return jsonify({"error":"Prompt அவசியம்"}),400

    # Step 1: Translate Tamil prompt to English via Groq
    try:
        trans = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role":"system","content":"You are an expert prompt engineer for AI image generation. The user may write in Tamil, Tanglish (Tamil written in English letters), or English. Translate and expand their input into a highly detailed English image generation prompt. Return ONLY the English prompt, nothing else. Be vivid, descriptive and artistic."},
                {"role":"user","content":tamil_prompt}
            ],
            max_tokens=300
        )
        english_prompt = trans.choices[0].message.content.strip()
    except:
        english_prompt = tamil_prompt

    # Step 2: Generate elaborate Tamil content about the image
    try:
        elaboration_resp = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": """நீ தமிழ் இலக்கிய உதவியாளர் - தமிழ் இலக்கிய வல்லுனர். 
பயனர் கொடுத்த prompt-க்கு ஒரு அழகான, விரிவான தமிழ் விளக்கம் கொடு.
கீழ்க்காணும் format-ல் பதில் கொடு:

## 🎨 படத்தின் சிறப்பு விளக்கம்

[2-3 வரி அழகான தமிழ் கவிதை நடையில் விளக்கம்]

### 🖼️ படத்தின் கலை அம்சங்கள்:
- **நிறங்கள்**: [எந்த நிறங்கள் பயன்படுத்தப்பட்டிருக்கும் என்று விளக்கு]
- **பாணி**: [கலை பாணி பற்றிய விளக்கம்]
- **உள்ளடக்கம்**: [படத்தில் என்ன தெரியும் என்று சொல்]

### 📖 இலக்கிய / வரலாற்று பின்னணி:
[இந்த படம் சார்ந்த தமிழ் இலக்கியம் அல்லது வரலாறு பற்றி 2-3 வரி]

📌 **உருவாக்கப்பட்ட Prompt**: [ஆங்கில prompt சுருக்கமாக]

Return ONLY the Tamil content in the above format. No extra text."""},
                {"role": "user", "content": f"இந்த prompt-க்கு விரிவான தமிழ் விளக்கம் கொடு: {tamil_prompt}"}
            ],
            max_tokens=600
        )
        elaboration = elaboration_resp.choices[0].message.content.strip()
    except:
        elaboration = f"## 🎨 படம் உருவாக்கப்பட்டது\n\nஉங்கள் prompt: **{tamil_prompt}**\n\nAI மூலம் சிறப்பான கலை படம் உருவாக்கப்பட்டது."

    # Step 3: Build styled prompt
    styled_prompt = f"{english_prompt}, ancient Tamil classical art style, intricate details, rich jewel colors, golden accents, traditional Indian painting style, 4k quality, highly detailed"

    # Step 4: Try Together AI → Stable Horde → HuggingFace (in order)
    # Stable Horde = 100% free crowdsourced GPU, ~5-10s response, no key needed
    TOGETHER_KEY = os.environ.get("TOGETHER_API_KEY", "").strip()

    # ── Helper 1: Together AI ──────────────────────────────────────────────────
    def try_together(prompt_text, key):
        models = [
            "black-forest-labs/FLUX.1-schnell-Free",
            "black-forest-labs/FLUX.1-schnell",
        ]
        last_err = None
        for model_name in models:
            try:
                resp = requests.post(
                    "https://api.together.xyz/v1/images/generations",
                    json={"model": model_name, "prompt": prompt_text,
                          "width": 768, "height": 512, "steps": 4, "n": 1},
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    timeout=60
                )
                print(f"Together [{model_name}] status: {resp.status_code}")
                if resp.status_code == 200:
                    item = resp.json()["data"][0]
                    if item.get("b64_json"):
                        return item["b64_json"], "image/jpeg"
                    elif item.get("url"):
                        r2 = requests.get(item["url"], timeout=30)
                        if r2.status_code == 200:
                            return base64.b64encode(r2.content).decode(), "image/jpeg"
                    raise Exception("No image data in response")
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_err = str(e)
        raise Exception(last_err)

    # ── Helper 2: Stable Horde (FREE crowdsourced GPU — 5-10s, no key needed) ──
    def try_stable_horde(prompt_text):
        """
        stablehorde.net — free, community-run GPU cluster.
        Anonymous key "0000000000" gives free access.
        Typical response: 5-15 seconds.
        """
        import time
        horde_api = "https://stablehorde.net/api/v2"
        api_key = os.environ.get("STABLE_HORDE_KEY", "0000000000")  # anon key works free

        # Submit generation request
        submit = requests.post(
            f"{horde_api}/generate/async",
            headers={"apikey": api_key, "Content-Type": "application/json"},
            json={
                "prompt": prompt_text,
                "params": {
                    "sampler_name": "k_euler",
                    "cfg_scale": 7,
                    "steps": 20,
                    "width": 512,
                    "height": 512,
                    "n": 1,
                },
                "models": ["stable_diffusion"],
                "r2": False,
                "nsfw": False,
                "censor_nsfw": True,
            },
            timeout=15
        )
        if submit.status_code not in (200, 202):
            raise Exception(f"Horde submit HTTP {submit.status_code}: {submit.text[:200]}")

        job_id = submit.json().get("id")
        if not job_id:
            raise Exception("Horde: no job id returned")
        print(f"Stable Horde job submitted: {job_id}")

        # Poll for result — max 60 seconds
        for _ in range(20):
            time.sleep(3)
            check = requests.get(
                f"{horde_api}/generate/check/{job_id}",
                headers={"apikey": api_key},
                timeout=10
            )
            if check.status_code == 200:
                status = check.json()
                print(f"Horde status: done={status.get('done')}, queue={status.get('queue_position')}")
                if status.get("done"):
                    # Fetch result
                    result = requests.get(
                        f"{horde_api}/generate/status/{job_id}",
                        headers={"apikey": api_key},
                        timeout=15
                    )
                    if result.status_code == 200:
                        generations = result.json().get("generations", [])
                        if generations and generations[0].get("img"):
                            img_b64 = generations[0]["img"]
                            # Horde returns base64 directly
                            return img_b64, "image/webp"
                    raise Exception("Horde: result fetch failed")
                if status.get("faulted"):
                    raise Exception("Horde: job faulted")

        raise Exception("Horde: timeout after 60s")

    # ── Helper 3: HuggingFace Inference API (free, optional token) ────────────
    def try_huggingface(prompt_text):
        hf_token = os.environ.get("HF_API_TOKEN", "").strip()
        hf_models = [
            "stabilityai/stable-diffusion-2-1",
            "runwayml/stable-diffusion-v1-5",
        ]
        last_err = None
        for hf_model in hf_models:
            try:
                hf_headers = {"Content-Type": "application/json"}
                if hf_token:
                    hf_headers["Authorization"] = f"Bearer {hf_token}"
                resp = requests.post(
                    f"https://api-inference.huggingface.co/models/{hf_model}",
                    headers=hf_headers,
                    json={"inputs": prompt_text},
                    timeout=90
                )
                print(f"HuggingFace [{hf_model}] status: {resp.status_code}")
                if resp.status_code == 200:
                    ct = resp.headers.get("Content-Type", "")
                    if ("image" in ct or len(resp.content) > 5000):
                        return base64.b64encode(resp.content).decode(), "image/jpeg"
                elif resp.status_code == 503:
                    import time; time.sleep(15)
                    resp2 = requests.post(
                        f"https://api-inference.huggingface.co/models/{hf_model}",
                        headers=hf_headers, json={"inputs": prompt_text}, timeout=90
                    )
                    if resp2.status_code == 200 and len(resp2.content) > 5000:
                        return base64.b64encode(resp2.content).decode(), "image/jpeg"
                last_err = f"HF {hf_model} HTTP {resp.status_code}"
            except Exception as e:
                last_err = str(e)
        raise Exception(last_err or "HuggingFace தோல்வி")

    # ── Main image generation logic ────────────────────────────────────────────
    img_b64, mime = None, "image/jpeg"
    last_error = None

    # 1️⃣ Together AI (if key set — fastest, best quality)
    if TOGETHER_KEY:
        try:
            img_b64, mime = try_together(styled_prompt, TOGETHER_KEY)
            print("✅ Together AI success!")
        except Exception as e:
            last_error = f"Together AI தோல்வி: {e}"
            print(f"❌ Together AI failed: {e}")

    # 2️⃣ Stable Horde (free, ~5-15s, no key needed)
    if img_b64 is None:
        try:
            img_b64, mime = try_stable_horde(styled_prompt)
            last_error = None
            print("✅ Stable Horde success!")
        except Exception as e:
            last_error = f"Stable Horde தோல்வி: {e}"
            print(f"❌ Stable Horde failed: {e}")

    # 3️⃣ HuggingFace (last resort)
    if img_b64 is None:
        try:
            img_b64, mime = try_huggingface(styled_prompt)
            last_error = None
            print("✅ HuggingFace success!")
        except Exception as e:
            last_error = f"HuggingFace தோல்வி: {e}"
            print(f"❌ HuggingFace failed: {e}")

    if img_b64 is None:
        return jsonify({
            "error": f"படம் உருவாக்க முடியவில்லை — அனைத்து services தோல்வியடைந்தன. ({last_error})"
        }), 500

    # Auto title for session
    title = "🎨 " + tamil_prompt[:45] + ("…" if len(tamil_prompt) > 45 else "")

    return jsonify({
        "success": True,
        "image_b64": img_b64,
        "mime": mime,
        "english_prompt": english_prompt,
        "tamil_prompt": tamil_prompt,
        "elaboration": elaboration,
        "suggested_title": title
    })


@app.route("/api/generate-image-together", methods=["POST"])
def generate_image_together():
    """Alternative: Together.ai FLUX model (needs TOGETHER_API_KEY env var)"""
    u = get_user(request)
    if not u: return jsonify({"error":"உள்நுழையவும்"}),401

    TOGETHER_KEY = os.environ.get("TOGETHER_API_KEY","")
    if not TOGETHER_KEY:
        return jsonify({"error":"TOGETHER_API_KEY இல்லை. Pollinations use பண்ணுங்கள்."}),400

    data = request.json or {}
    prompt = data.get("prompt","").strip()
    if not prompt: return jsonify({"error":"Prompt அவசியம்"}),400

    import urllib.request as ur, json as js
    payload = js.dumps({
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "prompt": prompt,
        "width": 768, "height": 512,
        "steps": 4, "n": 1,
        "response_format": "b64_json"
    }).encode()
    req = ur.Request(
        "https://api.together.xyz/v1/images/generations",
        data=payload,
        headers={"Authorization":f"Bearer {TOGETHER_KEY}","Content-Type":"application/json"}
    )
    try:
        with ur.urlopen(req, timeout=60) as resp:
            result = js.loads(resp.read())
        b64 = result["data"][0]["b64_json"]
        return jsonify({"success":True,"image_b64":b64,"prompt":prompt})
    except Exception as e:
        return jsonify({"error":str(e)}),500


if __name__=="__main__":
    print("\n"+"="*55)
    print("🌺  தமிழ் இலக்கிய உதவியாளர்")
    print("="*55)
    print(f"📍 http://localhost:5000")
    print(f"🔑 GROQ API: {'✅ Set' if GROQ_API_KEY!='your_groq_api_key_here' else '❌ GROQ_API_KEY set பண்ணவும்'}")
    together_check = os.environ.get('TOGETHER_API_KEY','').strip()
    hf_check = os.environ.get('HF_API_TOKEN','').strip()
    print(f"🎨 TOGETHER API: {'✅ Set — FLUX ready!' if together_check else '⚠️  Not set — Stable Horde fallback'}")
    print(f"🤗 HUGGINGFACE:  {'✅ Token set — Higher rate limits!' if hf_check else 'ℹ️  Free tier (no token needed)'}")
    print(f"🖼️  Image order: Together AI → Stable Horde (free) → HuggingFace")
    print("📦 pip install flask flask-cors groq PyPDF2")
    print("🚀 GROQ_API_KEY=gsk_xxx python backend.py")
    print("="*55+"\n")
    app.run(debug=True,host="0.0.0.0",port=5000,threaded=True)