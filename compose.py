"""
compose.py

Packages the chosen chart + caption into a per-match output folder
for manual posting on X.
"""

import os


def _code(name: str) -> str:
    return name[:3].upper()


def make_output_dir(meta: dict, root: str = "output") -> str:
    folder = f"{meta['date']}_{_code(meta['team_a'])}_{_code(meta['team_b'])}"
    path   = os.path.join(root, folder)
    os.makedirs(path, exist_ok=True)
    return path


def build_caption(candidate, meta: dict) -> str:
    tag_comp  = meta["competition"].replace(" ", "").replace(".", "")
    tag_match = (f"#{meta['team_a'].replace(' ','')} "
                 f"#{meta['team_b'].replace(' ','')}")
    caption   = f"{candidate.headline}\n\n#{tag_comp} {tag_match}"
    if len(caption) > 275:
        max_hl  = 275 - len(f"\n\n#{tag_comp} {tag_match}")
        caption = (candidate.headline[:max_hl].rsplit(" ", 1)[0]
                   + f"…\n\n#{tag_comp} {tag_match}")
    return caption


def save_package(image_path: str, caption: str, out_dir: str) -> str:
    caption_path = os.path.join(out_dir, "caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)
    return caption_path
