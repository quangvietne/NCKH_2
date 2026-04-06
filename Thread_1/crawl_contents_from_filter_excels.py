from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent

# --- CẤU HÌNH NĂM VÀ NGÂN HÀNG CẦN XỬ LÝ ---
TARGET_YEAR = "2024"
TARGET_BANK = "LP Bank"  # Đổi thành "vietcombank", "bidv", v.v. hoặc "*" nếu muốn chạy tất cả ngân hàng trong năm
# ------------------------------------------

try:
	import trafilatura
except Exception as e:  # pragma: no cover
	trafilatura = None
	_trafilatura_import_error = e

try:
	from newspaper import Article
except Exception as e:  # pragma: no cover
	Article = None
	_newspaper_import_error = e


def _strip_trailing_punct(url: str) -> str:
	return url.strip().rstrip(")].,;\"' ")



def _safe_str(v) -> str:
	if v is None:
		return ""
	try:
		if pd.isna(v):
			return ""
	except Exception:
		pass
	return str(v)


def _load_items_from_filter_xlsx(xlsx_path: Path) -> list[dict[str, str]]:
	df = pd.read_excel(xlsx_path, engine="openpyxl")

	if "url_out" in df.columns:
		url_col = "url_out"
	elif "url" in df.columns:
		url_col = "url"
	else:
		raise KeyError(f"Missing url_out/url column in: {xlsx_path}")

	title_col = "title" if "title" in df.columns else None

	items: list[dict[str, str]] = []
	for _, row in df.iterrows():
		url = _safe_str(row.get(url_col)).strip()
		if not url or url.lower() in {"nan", "none"}:
			continue
		url = _strip_trailing_punct(url)

		title = ""
		if title_col is not None:
			title = _safe_str(row.get(title_col)).strip()

		items.append({"link": url, "title": title})

	# Dedupe by link, keep the first non-empty title if possible
	seen: dict[str, dict[str, str]] = {}
	for it in items:
		link = it["link"]
		if link not in seen:
			seen[link] = it
			continue
		if not seen[link].get("title") and it.get("title"):
			seen[link]["title"] = it["title"]

	return list(seen.values())


def _ensure_deps() -> None:
	if trafilatura is None:
		raise RuntimeError(
			"Missing dependency: trafilatura. Install with: pip install trafilatura\n"
			f"Import error: {_trafilatura_import_error!r}"
		)
	if Article is None:
		raise RuntimeError(
			"Missing dependency: newspaper3k. Install with: pip install newspaper3k\n"
			f"Import error: {_newspaper_import_error!r}"
		)


def _extract_with_trafilatura(url: str, session: requests.Session, timeout: int) -> str | None:
	# trafilatura.fetch_url tự download; nếu fail thì dùng requests để lấy HTML rồi extract.
	downloaded = None
	try:
		downloaded = trafilatura.fetch_url(url)
	except Exception:
		downloaded = None

	if not downloaded:
		try:
			resp = session.get(url, timeout=timeout, allow_redirects=True)
			resp.raise_for_status()
			downloaded = resp.text
		except Exception:
			downloaded = None

	if not downloaded:
		return None

	try:
		text = trafilatura.extract(
			downloaded,
			url=url,
			include_comments=False,
			include_tables=False,
			favor_precision=True,
		)
	except Exception:
		return None

	if not text:
		return None

	text = text.strip()
	if len(text) < 200:
		return None
	return text


def _extract_with_newspaper(url: str) -> str | None:
	try:
		article = Article(url, language="vi")
		article.download()
		article.parse()
		text = (article.text or "").strip()
		if len(text) < 200:
			return None
		return text
	except Exception:
		return None


def fetch_article_text(url: str, session: requests.Session, timeout: int) -> tuple[str | None, str | None]:
	"""Return (text, method). method in {trafilatura,newspaper3k} or None."""
	text = _extract_with_trafilatura(url, session=session, timeout=timeout)
	if text:
		return text, "trafilatura"

	text = _extract_with_newspaper(url)
	if text:
		return text, "newspaper3k"

	return None, None


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(
		description=(
			"Read all *_filter.xlsx under data/<YEAR>/<BANK>/bronze/, crawl article text from url_out, "
			"and save JSON into data/<YEAR>/<BANK>/silver/1/ with metadata: link, title, content, source(domain)."
		)
	)
	parser.add_argument(
		"--data-root",
		default=f"data/{TARGET_YEAR}",
		help=f"Root folder that contains YEAR/BANK folders (default: data/{TARGET_YEAR}).",
	)
	parser.add_argument(
		"--stage-in",
		default="bronze",
		help="Input stage folder name under each bank folder (default: bronze).",
	)
	parser.add_argument(
		"--stage-out",
		default="silver/1",
		help="Output stage folder under each bank folder (default: silver/1).",
	)
	parser.add_argument(
		"--glob",
		default="**/bronze/**/*_filter.xlsx",
		help="Glob pattern under data-root. By default, it uses TARGET_BANK and stage_in configuration.",
	)
	parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout seconds.")
	parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between URLs.")
	parser.add_argument(
		"--out",
		default="",
		help=(
			"Optional explicit output JSON path. If omitted, writes per-bank outputs to "
			"data/<YEAR>/<BANK>/<stage-out>/article_texts_<ts>.json (default stage-out is silver/1). "
			"If provided, writes ONE combined JSON containing all banks."
		),
	)
	args = parser.parse_args(argv)

	# Tương thích với TARGET_BANK và tuỳ chỉnh stage_in
	if args.glob == "**/bronze/**/*_filter.xlsx":
		bank_path = "**" if TARGET_BANK == "*" else TARGET_BANK
		args.glob = f"{bank_path}/{args.stage_in}/**/*_filter.xlsx"

	_ensure_deps()

	data_root = Path(args.data_root)
	if not data_root.is_absolute():
		data_root = PROJECT_ROOT / data_root
	if not data_root.exists():
		raise FileNotFoundError(f"data-root not found: {data_root.resolve()}")

	xlsx_files = [p for p in data_root.glob(args.glob) if p.is_file()]
	# Skip Office temp files like ~$...
	xlsx_files = [p for p in xlsx_files if not p.name.startswith("~$")]

	if not xlsx_files:
		print("No *_filter.xlsx files found under:", data_root.resolve())
		return 0

	ts = datetime.now().strftime("%Y%m%d_%H%M%S")

	session = requests.Session()
	session.headers.update(
		{
			"User-Agent": (
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/122.0.0.0 Safari/537.36"
			)
		}
	)

	# Collect results per bank, then write JSON into each bank's silver folder.
	# Output format:
	# {
	#   "BIDV": [
	#     {"link": "https://...", "title": "...", "content": "...", "source": "baochinhphu.vn"},
	#     {"link": "https://...", "title": "...", "content": null, "source": "..."}
	#   ]
	# }
	result_by_bank: dict[str, list[dict]] = {}
	bank_root_by_name: dict[str, Path] = {}

	print(f"Found {len(xlsx_files)} *_filter.xlsx files")
	for i, xlsx_path in enumerate(sorted(xlsx_files), start=1):
		# Expect: data/<YEAR>/<BANK>/<stage-in>/*.xlsx
		# So bank folder is parent of stage-in folder.
		stage_in = str(args.stage_in)
		if xlsx_path.parent.name == stage_in:
			bank = xlsx_path.parent.parent.name
			bank_root = xlsx_path.parent.parent
		else:
			# Fallback: best-effort
			bank = xlsx_path.parent.name
			bank_root = xlsx_path.parent

		print(f"[{i}/{len(xlsx_files)}] Reading: {xlsx_path}")

		try:
			items = _load_items_from_filter_xlsx(xlsx_path)
		except Exception as e:
			print("  ERROR reading excel:", repr(e))
			continue

		if not items:
			print("  No URLs in file.")
			continue

		bank_root_by_name.setdefault(bank, bank_root)
		bank_items = result_by_bank.setdefault(bank, [])
		print(f"  Bank={bank} | Links={len(items)}")

		for j, it in enumerate(items, start=1):
			url = it.get("link", "")
			title = it.get("title", "")
			print(f"    - ({j}/{len(items)}) {url}")
			content, _method = fetch_article_text(url, session=session, timeout=args.timeout)
			source = ""
			try:
				source = (urlparse(url).netloc or "").lower()
			except Exception:
				source = ""
			bank_items.append({"link": url, "title": title, "content": content, "source": source})
			time.sleep(max(0.0, float(args.sleep)))


	# Write outputs
	if args.out:
		out_path = Path(args.out)
		if not out_path.is_absolute():
			out_path = PROJECT_ROOT / out_path
		out_path.parent.mkdir(parents=True, exist_ok=True)
		with out_path.open("w", encoding="utf-8") as f:
			json.dump(result_by_bank, f, ensure_ascii=False, indent=2)
		print("\nSaved combined JSON:")
		print("-", out_path)
		return 0

	# Otherwise write per-bank outputs under each bank folder
	# (per-bank outputs)
	else:
		for bank, items in sorted(result_by_bank.items()):
			bank_root = bank_root_by_name.get(bank)
			if bank_root is None:
				bank_root = data_root / bank
			out_dir = bank_root / str(args.stage_out)
			out_dir.mkdir(parents=True, exist_ok=True)
			out_path = out_dir / f"article_texts_{ts}.json"

			payload = {bank: items}
			with out_path.open("w", encoding="utf-8") as f:
				json.dump(payload, f, ensure_ascii=False, indent=2)

			ok_n = sum(1 for it in items if it.get("content"))
			all_n = len(items)
			print(f"Saved: {out_path.resolve()} | Bank={bank} | Extracted OK: {ok_n}/{all_n}")

	# Final summary across all banks/files
	total_ok = sum(1 for items in result_by_bank.values() for it in items if it.get("content"))
	total_all = sum(len(items) for items in result_by_bank.values())
	print(f"\nDone. Extracted OK: {total_ok}/{total_all}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())