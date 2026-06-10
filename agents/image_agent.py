import os
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI, BadRequestError
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ GPT Image 2 — current OpenAI flagship image model ($0.005/image at low quality)
# DALL-E 2 and DALL-E 3 were removed from the OpenAI API on May 12, 2026


def generate_blog_image(prompt: str) -> str | None:
    """
    Generate a single image using GPT Image 2.
    Returns a base64 data URI, or None if generation fails.

    Pricing (per image):
        low    = $0.005   ← default (best value)
        medium = $0.053
        high   = $0.211

    Override via environment variables:
        IMAGE_MODEL   (default: gpt-image-2)
        IMAGE_QUALITY (default: low)
        IMAGE_SIZE    (default: 1024x1024)
    """
    enhanced_prompt = (
        f"Professional, clean, modern blog illustration for: {prompt}. "
        f"High quality, editorial style, no text overlays."
    )

    model   = os.getenv("IMAGE_MODEL",   "gpt-image-2")
    quality = os.getenv("IMAGE_QUALITY", "low")      # low=$0.005 | medium=$0.053 | high=$0.211
    size    = os.getenv("IMAGE_SIZE",    "1024x1024")

    try:
        response = client.images.generate(
            model=model,
            prompt=enhanced_prompt,
            n=1,
            size=size,
            quality=quality,
        )
        img = response.data[0]

        # GPT Image 2 returns b64_json by default
        raw_b64 = getattr(img, "b64_json", None)
        if raw_b64:
            print(f"[IMAGE] Generated with {model} ({quality} quality) — $0.005")
            return f"data:image/png;base64,{raw_b64}"

        # Fallback: if a URL was returned, download immediately (URLs expire ~1 hour)
        url = getattr(img, "url", None)
        if url and url.startswith("http"):
            import requests as _req
            try:
                r = _req.get(url, timeout=20)
                r.raise_for_status()
                b64 = base64.b64encode(r.content).decode()
                print(f"[IMAGE] Downloaded and converted to base64 data URI")
                return f"data:image/png;base64,{b64}"
            except Exception as dl_err:
                print(f"[IMAGE] Download failed ({dl_err}), keeping original URL")
                return url

    except BadRequestError as e:
        print(f"[IMAGE] {model} failed ({e.status_code}): {e.message}")
    except Exception as e:
        print(f"[IMAGE] Error: {e}")

    print("[IMAGE] Image generation failed — skipping")
    return None


def generate_images_for_blog(topic: str, sections: list = None) -> list:
    """
    Generate cover + up to 2 section images IN PARALLEL.

    Before: sequential → ~45s for 3 images
    After:  parallel   → ~15s for 3 images  (3x faster)
    """
    # Build the list of (label, prompt) in order
    jobs = [
        ("cover",     "Cover Image",     f"Cover image representing the topic: {topic}"),
        ("section",   "Section 1 Image", (sections[0] if sections and len(sections) > 0 else f"Key aspects of {topic}")),
        ("section",   "Section 2 Image", (sections[1] if sections and len(sections) > 1 else f"Future of {topic}")),
    ]

    print(f"[IMAGE] Generating {len(jobs)} images in parallel…")

    results: dict[int, str | None] = {}

    def _generate(idx: int, prompt: str) -> tuple[int, str | None]:
        return idx, generate_blog_image(prompt)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_generate, i, prompt): i
            for i, (_, _, prompt) in enumerate(jobs)
        }
        for future in as_completed(futures):
            idx, url = future.result()
            results[idx] = url

    # Reassemble in original order
    images = []
    for i, (img_type, label, _) in enumerate(jobs):
        url = results.get(i)
        if url:
            images.append({"type": img_type, "label": label, "url": url})

    print(f"[IMAGE] Done — {len(images)}/{len(jobs)} images generated")
    return images
