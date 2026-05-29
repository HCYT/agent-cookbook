# Image Generation Prompt Strategies

[繁體中文說明](./README.md)

The previous recipe [`codex-image-generation`](../codex-image-generation/README.en.md) covers API integration. This one covers how to write prompts that consistently produce good results.

Every strategy here is extracted from generating hundreds of images. Not theory — each one has pass-rate data behind it.

## Table of contents

1. [Prompt structure](#prompt-structure)
2. [Negative prompts — blocking retreat paths](#negative-prompts--blocking-retreat-paths)
3. [Reference image strategies](#reference-image-strategies)
4. [Anime → photo-realistic pipeline](#anime--photo-realistic-pipeline)
5. [Batch matrix design](#batch-matrix-design)
6. [Prompt caching optimization](#prompt-caching-optimization)
7. [Quality tracking and iteration](#quality-tracking-and-iteration)
8. [Common failure modes](#common-failure-modes)

---

## Prompt structure

### Core principle: describe the scene, not the result

Don't tell the model "draw X". Describe a scene that makes X happen naturally.

**Weak**:
```
a girl in loose clothing
```

**Strong**:
```
morning kitchen, a girl in her boyfriend's oversized white shirt making coffee,
sleeves rolled to elbows, light streaming through the window
```

Good prompts build a scene and let the model fill in visual details.

### Hierarchical weight structure

When prompts get long, use PRIMARY / SECONDARY / TERTIARY layers so the model knows what to prioritize:

```
PRIMARY: anime style, single character portrait, warm color palette,
         high quality rendering, morning golden light

SECONDARY: kitchen setting, relaxed atmosphere, cooking breakfast,
           wearing oversized boyfriend shirt

TERTIARY: steam from coffee cup, soft depth of field, lens flare from window
```

The model satisfies PRIMARY first, then SECONDARY, then TERTIARY. When token budget is tight, the last layer gets sacrificed.

### Style anchoring

Place style keywords at the beginning of every prompt to keep the look consistent:

```
anime style, clean sharp linework, warm color palette, high quality rendering
```

Common style anchors:

| Style | Keywords |
| --- | --- |
| Anime | `anime style, clean sharp linework, high quality rendering` |
| Watercolor | `watercolor painting, soft edges, color bleeding, paper texture` |
| Photography | `photorealistic, 85mm lens, shallow depth of field, natural lighting` |
| Oil painting | `oil painting, visible brushstrokes, rich color, canvas texture` |

Same style anchor across all generations → much better consistency.

---

## Negative prompts — blocking retreat paths

Negative prompts aren't just for preventing mistakes. Their real function is to **block the model's conservative retreat paths**, forcing it toward your intended direction.

### Why "blocking retreats"

The model is pushed by your positive prompt in a certain direction, but instinctively looks for safe alternatives — adding props to cover things up, using rough textures to reduce realism, changing composition to avoid details. Negative prompts seal those exits.

### Layered design

Organize negative prompts in layers, combining as needed:

#### Layer 1: Quality control (always include)

```
bad anatomy, extra fingers, deformed hands, broken limbs,
twisted joints, floating body parts, asymmetrical rendering errors
```

#### Layer 2: Face style control

Steer facial features. For Asian characters, exclude Western traits:

```
western face, european face, deep set eyes, high nose bridge,
doll-like face, plastic skin
```

For realistic style:

```
anime face, cartoon eyes, flat shading, 2D illustration style
```

#### Layer 3: Material control

Control skin and fabric texture direction. Exclude what you don't want, and the model moves toward the opposite:

```
dry skin texture, powdery roughness, chalk-like surface,
cold skin tone, matte flat skin rendering
```

Excluding these → the model produces warm, luminous skin.

#### Layer 4: Composition control

Prevent the model from dodging your intended framing:

```
cropped composition, extreme close-up face only,
blurry background replacing content
```

### Combination example

Use `## Negative prompt:` as a separator so the model clearly understands it's a reverse instruction:

```
A girl in a bright kitchen making breakfast, wearing an apron,
warm morning light from the window, anime style, high quality

## Negative prompt:
bad anatomy, extra fingers, deformed hands,
western face, deep set eyes, plastic skin,
dry skin texture, powdery roughness, cold skin tone,
cropped composition, blurry, low quality
```

### Scene-specific negative templates

Different scenes need different retreats blocked:

**Indoor daily life**:
```
bad anatomy, extra fingers, deformed hands,
dull lighting, muddy colors, flat shading,
harsh shadows, overexposed, underexposed
```

**Outdoor nature**:
```
bad anatomy, extra fingers, deformed hands,
studio lighting, indoor background, artificial light,
flat sky, grey atmosphere, desaturated colors
```

**Portrait close-up**:
```
bad anatomy, extra fingers, deformed hands,
blurry face, asymmetrical eyes, plastic skin,
pore-less skin, airbrushed, mannequin-like
```

---

## Reference image strategies

### When to use reference images

| Purpose | How |
| --- | --- |
| Character consistency | Use a fixed character sheet as ref for all generations |
| Style consistency | Use a style reference image |
| Scene variations | Fixed character ref, vary scene in prompt |
| Incremental tweaks | Use last successful image as ref, change one variable |

### Multiple reference images

The API supports multiple refs in one call. Common uses:

- **Character sheet + outfit reference** — control character and clothing separately
- **Front + side view** — help the model understand 3D structure
- **Character A + Character B** — generate group shots

```json
{
  "content": [
    { "type": "input_image", "image_url": "data:image/png;base64,{character}" },
    { "type": "input_image", "image_url": "data:image/png;base64,{outfit}" },
    { "type": "input_text", "text": "Wearing this outfit, standing at a cafe entrance" }
  ]
}
```

### The ceiling effect

**Key concept**: the reference image's quality, style, and detail level is the ceiling for generated images.

- Low-quality ref → generated image won't be more refined
- Strongly-styled ref → generated image follows that style
- Ref's pose and composition heavily influence the result

Invest time in good character sheets. One great sheet pays dividends across every subsequent generation.

---

## Anime → photo-realistic pipeline

A two-step pipeline: generate anime first, then convert to photo-realistic.

### Why not generate photo-realistic directly

Going straight to photo-realistic, the model tends toward "AI-looking fake photos". The two-step approach:

1. Anime compositions and poses are easier to control
2. Using anime as ref for photo conversion, the model faithfully copies composition
3. Confirm the composition in anime first, then convert — no restart if unhappy

### Conversion prompt template

```
Convert this anime illustration into a real photograph.
It should look like it was shot with a real DSLR camera,
with natural skin texture, pores, and lighting.
The character is an Asian woman. Keep exactly the same composition,
pose, expression, clothing, scene, and lighting.
Photographic style, Sony A7IV, 85mm lens, natural light, shallow depth of field.

## Negative prompt:
anime style, illustration, CG, 3D render, plastic skin, airbrushed skin,
doll-like, cartoon, flat shading
```

### Conversion tips

| Aspect | Approach |
| --- | --- |
| Avoid AI fake face | Add "natural skin texture and pores", negative `plastic skin, airbrushed` |
| Control facial direction | Specify ethnicity/face shape: "Asian woman, round face" |
| Camera parameters | Add `Sony A7IV, 85mm, f/1.8` — model references photography training data |
| Don't over-specify | Keep conversion prompt clean, let the ref carry the visuals. Too much description fights the ref |

### Iterating on results

Use the successful image as ref, change one variable at a time:

```bash
# Original: cafe scene, satisfied with it
# Want to change expression only
python basic-gen.py "Same as reference, but with a smiling expression" ./success-cafe.png cafe-smile
```

Changing too many things at once → completely different image → starting over.

---

## Batch matrix design

When you need bulk images (character libraries, scene series, training datasets), think in matrices.

### Matrix structure

```
characters × scenes × actions = total generations
```

Example:

```python
CHARACTERS = ["character_a", "character_b", "character_c"]
SCENES = ["kitchen_morning", "cafe_afternoon", "park_sunset"]
ACTIONS = ["standing", "sitting", "walking"]

# 3 × 3 × 3 = 27 images
```

### Design principles

1. **Shared base**: style anchor + negative shared across all, only vary scene and action
2. **Naming convention**: `{character}_{scene}_{action}` → easy to track and analyze
3. **Resumable**: check if output file exists before generating, skip completed ones
4. **Rate limiting**: sleep 3–5s between calls to avoid rate limits
5. **Pass-rate tracking**: after each batch, compute success rates per combination

### Pass-rate tracking

After a batch run, group by scene and action to find weak spots:

```python
# Example output
# kitchen_morning: 8/9 (89%)
# cafe_afternoon:  7/9 (78%)
# park_sunset:     9/9 (100%)
```

Low pass-rate → prompt issue → targeted adjustment.

See [`examples/matrix-gen.py`](./examples/matrix-gen.py) for a full working example.

---

## Prompt caching optimization

### How it works

The API's prompt cache does **prefix matching** — it compares from the start, and if the prefix matches, it hits the cache.

Strategy: **fixed content first, variable content last.**

```
[Fixed]   instructions + system message + ref image
[Variable] per-image prompt
```

### In practice

```python
body = {
    "instructions": "Generate images immediately without text response.",  # fixed
    "input": [{"role": "user", "content": [
        ref_image_block,   # fixed (same character, same ref)
        {"type": "input_text", "text": prompt},  # varies
    ]}],
    "prompt_cache_key": "my-batch-v1",  # shared across batch
}
```

### Cache effectiveness

| Scenario | First call | Subsequent calls |
| --- | --- | --- |
| No cache | Full processing | Full processing |
| Cache, same ref + different prompt | Full processing | Shared prefix hits, only processes the diff |

Batch of 50 images with the same character: the last 49 return noticeably faster.

### When to rotate cache keys

- Different character (ref changed) → new key
- Different instructions → new key
- Same character + same instructions, new batch → can reuse

---

## Quality tracking and iteration

### JSON logs

Log every generation for post-analysis:

```json
{
  "slug": "character_a_kitchen_standing",
  "timestamp": "2025-05-29T14:30:00",
  "prompt": "...",
  "negative": "...",
  "success": true,
  "elapsed_s": 12.3,
  "text_response": null
}
```

### Iteration workflow

```
Round 1: run the full matrix, record pass rates
    ↓
Analyze failed prompts → adjust wording
    ↓
Round 2: re-run only failed slugs
    ↓
Repeat until pass rate > 80%
    ↓
Archive successful prompts → reuse directly next time
```

### Archiving successful prompts

Save validated prompts as `.txt` files for reuse:

```
prompts/
  kitchen-morning.txt
  cafe-afternoon.txt
  park-sunset.txt
```

Scripts can read prompt files directly:

```bash
python basic-gen.py prompts/kitchen-morning.txt ./ref.png kitchen-01
```

---

## Common failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| API returns 401 | Token expired | Re-run `codex login` |
| Runs but no image, no error | Silently blocked by content policy | Rephrase, avoid sensitive combinations |
| Image but style drifts | No style anchor, or ref style too weak | Strengthen style keywords at prompt start |
| Image but weird composition | Contradictory prompt, model confused | Simplify prompt, one focus point at a time |
| Image but face collapse | Ref face info insufficient, or prompt fights ref | Use a clear, front-facing character sheet |
| Batch fails midway | Not blocked — connection issue | Add retry logic, or reduce concurrency |
| Same prompt, inconsistent results | Normal, model has randomness | Run same prompt 2–3 times, pick the best |

### Anti-patterns

| Don't | Why |
| --- | --- |
| Over-long prompts | Exceeds model attention span, back half ignored |
| Change 3+ variables at once | Can't diagnose which variable caused the issue |
| Run batch without logging | Discover all bad images after the fact, no way to trace |
| Ignore usage stats | Miss token exhaustion or rate limits |
| Blurry / tiny ref images | Model can't extract enough info, ref is wasted |

---

## Included examples

| File | Purpose |
| --- | --- |
| [`examples/matrix-gen.py`](./examples/matrix-gen.py) | Matrix batch generation — characters × scenes × actions |
| [`examples/anime-to-real.py`](./examples/anime-to-real.py) | Anime → photo-realistic conversion pipeline |

## Privacy notes

Character names, scenes, and prompts in the examples are generic placeholders. Replace them with your own characters and references.
